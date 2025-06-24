import pytest
import requestcompletion as rc
from typing import List, Callable
from pydantic import BaseModel, Field
import random
from requestcompletion.nodes.library import LimitedToolCallLLM

# ============ Model ===========
@pytest.fixture
def model():
    return rc.llm.OpenAILLM("gpt-4o")


# ============ Output Models ===========
class SimpleOutput(BaseModel):  # simple structured output case
    text: str = Field(description="The text to return")
    number: int = Field(description="The number to return")


class TravelPlannerOutput(BaseModel):  # structured using tool calls
    travel_plan: str = Field(description="The travel plan")
    Total_cost: float = Field(description="The total cost of the trip")
    Currency: str = Field(description="The currency used for the trip")


class MathOutput(BaseModel):  # structured using terminal llm as tool
    sum: float = Field(description="The sum of the random numbers")
    random_numbers: List[int] = Field(
        description="The list of random numbers generated"
    )


class EmptyModel(BaseModel):  # empty structured output case
    pass


class PersonOutput(BaseModel):  # complex structured output case
    name: str = Field(description="The name of the person")
    age: int = Field(description="The age of the person")
    Favourites: SimpleOutput = Field(
        description="The favourite text and number of the person"
    )


@pytest.fixture
def travel_planner_output_model():
    return TravelPlannerOutput


@pytest.fixture
def math_output_model():
    return MathOutput


@pytest.fixture
def simple_output_model():
    return SimpleOutput


@pytest.fixture
def empty_output_model():
    return EmptyModel


@pytest.fixture
def person_output_model():
    return PersonOutput


# ============ Tools ===========

def _increment_tools_called():
    """Increments the tools_called context variable by 1"""
    count = rc.context.get("tools_called", -1)
    rc.context.put("tools_called", count + 1)

@pytest.fixture
def simple_tools():
    def random_number() -> int:
        """Returns a random number between 1 and 100.
        Args:
        Returns:
            int: A random number between 1 and 100.
        """
        _increment_tools_called()
        return random.randint(1, 100)
    return random_number

@pytest.fixture
def travel_planner_tools():
    def available_locations() -> List[str]:
        """Returns a list of available locations.
        Args:
        Returns:
            List[str]: A list of available locations.
        """
        _increment_tools_called()
        return [
            "New York",
            "Los Angeles",
            "Chicago",
            "Delhi",
            "Mumbai",
            "Bangalore",
            "Paris",
            "Denmark",
            "Sweden",
            "Norway",
            "Germany",
        ]

    def currency_used(location: str) -> str:
        """Returns the currency used in a location.
        Args:
            location (str): The location to get the currency used for.
        Returns:
            str: The currency used in the location.
        """
        _increment_tools_called()
        currency_map = {
            "New York": "USD",
            "Los Angeles": "USD",
            "Chicago": "USD",
            "Delhi": "INR",
            "Mumbai": "INR",
            "Bangalore": "INR",
            "Paris": "EUR",
            "Denmark": "EUR",
            "Sweden": "EUR",
            "Norway": "EUR",
            "Germany": "EUR",
        }
        used_currency = currency_map.get(location)
        if used_currency is None:
            raise ValueError(f"Currency not available for location: {location}")
        return used_currency

    def average_location_cost(location: str, num_days: int) -> float:
        """Returns the average cost of living in a location for a given number of days.
        Args:
            location (str): The location to get the cost of living for.
            num_days (int): The number of days for the trip.
        Returns:
            float: The average cost of living in the location.
        """
        _increment_tools_called()
        daily_costs = {
            "New York": 200.0,
            "Los Angeles": 180.0,
            "Chicago": 150.0,
            "Delhi": 50.0,
            "Mumbai": 55.0,
            "Bangalore": 60.0,
            "Paris": 220.0,
            "Denmark": 250.0,
            "Sweden": 240.0,
            "Norway": 230.0,
            "Germany": 210.0,
        }
        daily_cost = daily_costs.get(location)
        if daily_cost is None:
            raise ValueError(f"Cost information not available for location: {location}")
        return daily_cost * num_days

    def convert_currency(amount: float, from_currency: str, to_currency: str) -> float:
        """Converts currency using a static exchange rate (for testing purposes).
        Args:
            amount (float): The amount to convert.
            from_currency (str): The currency to convert from.
            to_currency (str): The currency to convert to.
        Returns:
            float: The converted amount.
        Raises:
            ValueError: If the exchange rate is not available.
        """
        _increment_tools_called()
        exchange_rates = {
            ("USD", "EUR"): 0.85,
            ("EUR", "USD"): 1.1765,
            ("USD", "INR"): 83.0,
            ("INR", "USD"): 0.01205,
            ("EUR", "INR"): 98.0,
            ("INR", "EUR"): 0.0102,
        }

        rate = exchange_rates.get((from_currency, to_currency))
        if rate is None:
            raise ValueError("Exchange rate not available")
        return amount * rate

    return convert_currency, available_locations, currency_used, average_location_cost


# ============ Nodes ===========
@pytest.fixture
def simple_node(request, model, simple_output_model):

    system_simple = rc.llm.SystemMessage("Return a simple text and number. Don't use any tools.")
    fixture_name = request.param

    if fixture_name == "easy_wrapper":
        simple_node = rc.library.tool_call_llm(
            connected_nodes={
                rc.library.from_function(random.random)
            },  # providing a tool to the node becuase providing an empty set will cause an error
            pretty_name="Simple Node",
            system_message=system_simple,
            model=model,
            output_model=simple_output_model,
        )
        return simple_node
    elif fixture_name == "class_based":

        class SimpleNode(rc.library.StructuredToolCallLLM):
            def __init__(
                self,
                message_history: rc.llm.MessageHistory,
                output_model: BaseModel = simple_output_model,
                llm_model: rc.llm.ModelBase = model,
            ):
                message_history = [x for x in message_history if x.role != "system"]
                message_history.insert(0, system_simple)
                super().__init__(
                    message_history=message_history,
                    llm_model=llm_model,
                    output_model=output_model,
                )

            @classmethod
            def connected_nodes(cls):
                return {rc.library.from_function(random.random)}

            @classmethod
            def pretty_name(cls) -> str:
                return "Simple Node"

        return SimpleNode
    else:
        raise ValueError(f"Unknown node fixture: {fixture_name}")


@pytest.fixture
def travel_planner_node(
    request, model, travel_planner_tools, travel_planner_output_model
):
    """
    Returns the appropriate nodes based on the parametrized fixture name.
    """
    fixture_name = request.param
    convert_currency, available_locations, currency_used, average_location_cost = (
        travel_planner_tools
    )
    system_travel_planner = rc.llm.SystemMessage(
        "You are a travel planner that will plan a trip. you have access to AvailableLocations, ConvertCurrency, CurrencyUsed and AverageLocationCost tools. Use them when you need to."
    )

    convert_currency_node = rc.library.from_function(convert_currency)
    available_locations_node = rc.library.from_function(available_locations)
    currency_used_node = rc.library.from_function(currency_used)
    average_location_cost_node = rc.library.from_function(average_location_cost)

    if fixture_name == "easy_wrapper":
        travel_planner_node = rc.library.tool_call_llm(
            connected_nodes={
                convert_currency_node,
                available_locations_node,
                currency_used_node,
                average_location_cost_node,
            },
            pretty_name="Travel Planner Node",
            system_message=system_travel_planner,
            model=model,
            output_model=travel_planner_output_model,
        )

        return travel_planner_node
    elif fixture_name == "class_based":

        class TravelPlannerNode(rc.library.StructuredToolCallLLM):
            def __init__(
                self,
                message_history: rc.llm.MessageHistory,
                output_model: BaseModel = travel_planner_output_model,
                llm_model: rc.llm.ModelBase = model,
            ):
                message_history = [x for x in message_history if x.role != "system"]
                message_history.insert(0, system_travel_planner)
                super().__init__(
                    message_history=message_history,
                    llm_model=llm_model,
                    output_model=output_model,
                )

            @classmethod
            def connected_nodes(cls):
                return {
                    convert_currency_node,
                    available_locations_node,
                    currency_used_node,
                    average_location_cost_node,
                }

            @classmethod
            def pretty_name(cls) -> str:
                return "Travel Planner Node"

        return TravelPlannerNode

    else:
        raise ValueError(f"Unknown node fixture: {fixture_name}")


@pytest.fixture
def math_node(request, model, math_output_model):
    system_math_genius = rc.llm.SystemMessage(
        "You are a math genius that calls the RNG tool to generate 5 random numbers between 1 and 100 and gives the sum of those numbers."
    )

    rng_node = rc.library.terminal_llm(
        pretty_name="RNG Tool",
        system_message=rc.llm.SystemMessage(
            "You are a helful assistant that can generate 5 random numbers between 1 and 100."
        ),
        model=model,
        tool_details="A tool used to generate 5 random integers between 1 and 100.",
        tool_params=None,
    )

    fixture_name = request.param
    if fixture_name == "easy_wrapper":
        math_node = rc.library.tool_call_llm(
            connected_nodes={rng_node},
            pretty_name="Math Node",
            system_message=system_math_genius,
            model=model,
            output_model=math_output_model,
        )
        return math_node
    elif fixture_name == "class_based":

        class MathNode(rc.library.StructuredToolCallLLM):
            def __init__(
                self,
                message_history: rc.llm.MessageHistory,
                output_model: BaseModel = math_output_model,
                llm_model: rc.llm.ModelBase = model,
            ):
                message_history = [x for x in message_history if x.role != "system"]
                message_history.insert(0, system_math_genius)
                super().__init__(
                    message_history=message_history,
                    llm_model=llm_model,
                    output_model=output_model,
                )

            @classmethod
            def connected_nodes(cls):
                return {rng_node}

            @classmethod
            def pretty_name(cls) -> str:
                return "Math Node"

        return MathNode
    else:
        raise ValueError(f"Unknown node fixture: {fixture_name}")


@pytest.fixture
def complex_node(request, model, person_output_model):
    system_complex = rc.llm.SystemMessage(
        "You are an all knowing sentient being. You can answer any question asked to you. You may make up any answer you want. Just provide all info asked for."
    )
    fixture_name = request.param

    if fixture_name == "easy_wrapper":
        sentient_node = rc.library.tool_call_llm(
            connected_nodes={
                rc.library.from_function(random.random)
            },  # providing a tool to the node becuase providing an empty set will cause an error
            pretty_name="Complex Node",
            system_message=system_complex,
            model=model,
            output_model=person_output_model,
        )
        return sentient_node
    elif fixture_name == "class_based":

        class SentientNode(rc.library.StructuredToolCallLLM):
            def __init__(
                self,
                message_history: rc.llm.MessageHistory,
                output_model: BaseModel = person_output_model,
                llm_model: rc.llm.ModelBase = model,
            ):
                message_history = [x for x in message_history if x.role != "system"]
                message_history.insert(0, system_complex)
                super().__init__(
                    message_history=message_history,
                    llm_model=llm_model,
                    output_model=output_model,
                )

            @classmethod
            def connected_nodes(cls):
                return {rc.library.from_function(random.random)}

            @classmethod
            def pretty_name(cls) -> str:
                return "Complex Node"

        return SentientNode
    else:
        raise ValueError(f"Unknown node fixture: {fixture_name}")

@pytest.fixture
def simple_function_taking_node(request, model, simple_tools, simple_output_model):
    """
    Returns the appropriate nodes based on the parametrized fixture name.
    """
    random_number = simple_tools
    system_mes = rc.llm.SystemMessage(
        "You are a helpful assistant that uses the random number tool to generate a random number between 1 and 100"
    )

    simple_node = rc.library.tool_call_llm(
        connected_nodes={random_number,
                        },
        pretty_name="Random Number Provider Node",
        system_message=system_mes,
        model=model,
        output_model=simple_output_model,
    )

    return simple_node

@pytest.fixture
def some_function_taking_travel_planner_node(request, model, travel_planner_tools, travel_planner_output_model):
    """
    Returns the appropriate nodes based on the parametrized fixture name.
    """
    convert_currency, available_locations, currency_used, average_location_cost = travel_planner_tools
    system_travel_planner = rc.llm.SystemMessage(
        "You are a travel planner that will plan a trip. you have access to AvailableLocations, ConvertCurrency, CurrencyUsed and AverageLocationCost tools. Use them when you need to."
    )

    travel_planner_node = rc.library.tool_call_llm(
        connected_nodes={
            convert_currency,
            rc.library.from_function(available_locations),
            currency_used,
            rc.library.from_function(average_location_cost),
        },
        pretty_name="Travel Planner Node",
        system_message=system_travel_planner,
        model=model,
        output_model=travel_planner_output_model,
    )

    return travel_planner_node

@pytest.fixture
def only_function_taking_travel_planner_node(request, model, travel_planner_tools, travel_planner_output_model):
    """
    Returns the appropriate nodes based on the parametrized fixture name.
    """
    convert_currency, available_locations, currency_used, average_location_cost = travel_planner_tools
    system_travel_planner = rc.llm.SystemMessage(
        "You are a travel planner that will plan a trip. you have access to AvailableLocations, ConvertCurrency, CurrencyUsed and AverageLocationCost tools. Use them when you need to."
    )

    travel_planner_node = rc.library.tool_call_llm(
        connected_nodes={
            convert_currency,
            available_locations,
            currency_used,
            average_location_cost,
        },
        pretty_name="Travel Planner Node",
        system_message=system_travel_planner,
        model=model,
        output_model=travel_planner_output_model,
    )

    return travel_planner_node

# ============================================= LIMITED TOOL CALLING LLM FIxTURES ================================================
@pytest.fixture
def travel_message_history():
    def _make(msg="I want to travel to New York from Vancouver for 4 days. Give me a budget summary for the trip in INR."):
        return rc.llm.MessageHistory([rc.llm.UserMessage(msg)])
    return _make

@pytest.fixture
def limited_tool_call_node_factory(model, travel_planner_tools):
    def _factory(max_tool_calls=1, system_message=None, tools=None, class_based=False):
        tools = tools or set([rc.library.from_function(tool) for tool in travel_planner_tools])
        sys_msg = system_message or rc.llm.SystemMessage(
            "You are a travel planner that will plan a trip. you have access to AvailableLocations, CurrencyUsed and AverageLocationCost tools. Use them when you need to."
        )
        tool_nodes = tools
        if not class_based:
            return rc.library.tool_call_llm(
                connected_nodes=tool_nodes,
                pretty_name="Limited Tool Call Test Node",
                system_message=sys_msg,
                model=model,
                max_tool_calls=max_tool_calls,
            )
        else:
            class LimitedToolCallTestNode(LimitedToolCallLLM):
                def __init__(self, message_history, model=model):
                    message_history.insert(0, sys_msg)
                    super().__init__(message_history, model, max_tool_calls=max_tool_calls)
                @classmethod
                def connected_nodes(cls):
                    return tool_nodes
                @classmethod
                def pretty_name(cls):
                    return "Limited Tool Call Test Node"
            return LimitedToolCallTestNode
    return _factory

@pytest.fixture
def reset_tools_called():
    def _reset(val=0):
        rc.context.put("tools_called", val)
    return _reset

# ============================================= END LIMITED TOOL CALLING LLM FIxTURES ================================================