import pytest
import requestcompletion as rc
from itertools import product

from src.requestcompletion.nodes.library import from_function

# ============ TEST CASES ===========
NODE_INIT_METHODS = ["easy_wrapper", "class_based"]

simple_model_test_cases = list(product(NODE_INIT_METHODS, ["simple_model"]))


@pytest.mark.asyncio
@pytest.mark.parametrize("simple_node", simple_model_test_cases, indirect=True, ids=lambda x: f"{x[0]}_with_{x[1]}")
async def test_structured_with_no_tool_calls(simple_node, simple_output_model):
    """Test basic functionality of returning a structured output."""
    with rc.Runner(executor_config=rc.ExecutorConfig(logging_setting="QUIET")) as runner:
        message_history = rc.llm.MessageHistory([rc.llm.UserMessage("Generate a simple text and number.")])
        response = await runner.run(simple_node, message_history=message_history)
        assert isinstance(response.answer, simple_output_model)
        assert isinstance(response.answer.text, str)
        assert isinstance(response.answer.number, int)


empty_model_test_cases = list(product(NODE_INIT_METHODS, ["empty_model"]))


@pytest.mark.asyncio
@pytest.mark.parametrize("simple_node", empty_model_test_cases, indirect=True, ids=lambda x: f"{x[0]}_with_{x[1]}")
async def test_empty_output_model(simple_node, empty_output_model):
    """Test when the output model is empty."""
    with rc.Runner(executor_config=rc.ExecutorConfig(logging_setting="QUIET")) as runner:
        message_history = rc.llm.MessageHistory([rc.llm.UserMessage("Generate a simple text and number.")])
        response = await runner.run(simple_node, message_history=message_history)
        assert isinstance(
            response.answer, empty_output_model
        ), f"Expected instance of {empty_output_model}, got {type(response.answer)}"


@pytest.mark.asyncio
@pytest.mark.parametrize("travel_planner_node", NODE_INIT_METHODS, indirect=True)
async def test_structured_with_tool_calls(travel_planner_node, travel_planner_output_model):
    """Test the functionality of a ToolCallLLM node (using actual tools) with a structured output model."""
    with rc.Runner(executor_config=rc.ExecutorConfig(timeout=50, logging_setting="QUIET")) as runner:
        message_history = rc.llm.MessageHistory(
            [
                rc.llm.UserMessage(
                    "I live in Delhi. I am going to travel to Denmark for 3 days, followed by Germany for 2 days and finally New York for 4 days. Please provide me with a budget summary for the trip in INR."
                )
            ]
        )
        response = await runner.run(travel_planner_node, message_history=message_history)
        assert isinstance(response.answer, travel_planner_output_model)
        assert isinstance(response.answer.travel_plan, str)
        assert isinstance(response.answer.Total_cost, float)
        assert isinstance(response.answer.Currency, str)


@pytest.mark.asyncio
@pytest.mark.parametrize("math_node", NODE_INIT_METHODS, indirect=True)
async def test_structured_with_terminal_llm_as_tool(math_node, math_output_model):
    """Test the functionality of a ToolCallLLM node (using terminalLLM as tool) with a structured output model."""
    with rc.Runner(executor_config=rc.ExecutorConfig(logging_setting="QUIET")) as runner:
        message_history = rc.llm.MessageHistory([rc.llm.UserMessage("Start the Math node.")])
        response = await runner.run(math_node, message_history=message_history)
        assert isinstance(response.answer, math_output_model)
        assert isinstance(response.answer.sum, float)
        assert isinstance(response.answer.random_numbers, list)


@pytest.mark.asyncio
@pytest.mark.parametrize("complex_node", NODE_INIT_METHODS, indirect=True)
async def test_structured_with_complex_output_model(complex_node, person_output_model, simple_output_model):
    """Test the functionality of structured output model with complex output model."""
    with rc.Runner(executor_config=rc.ExecutorConfig(logging_setting="QUIET")) as runner:
        message_history = rc.llm.MessageHistory(
            [
                rc.llm.UserMessage(
                    "My name is John Doe. I am 30 years old. My favourite text is 'Hello World' and my favourite number is 1290."
                )
            ]
        )
        response = await runner.run(complex_node, message_history=message_history)
        assert isinstance(response.answer, person_output_model)
        assert isinstance(response.answer.name, str)
        assert isinstance(response.answer.age, int)
        assert isinstance(response.answer.Favourites, simple_output_model)
        assert isinstance(response.answer.Favourites.text, str)
        assert isinstance(response.answer.Favourites.number, int)


@pytest.mark.asyncio  # can remove this test once we have support for output_model with output_type = MessageHistory. See Line 30 in src/requestcompletion/nodes/library/easy_usage_wrappers/tool_call_llm.py
async def test_structured_tool_call_with_output_model_and_output_type(model, math_output_model):
    """Tool call llm init with output model and output_type = message_history should raise an error."""
    rng_node = rc.library.terminal_llm(
        pretty_name="RNG Tool",
        system_message=rc.llm.SystemMessage(
            "You are a helful assistant that can generate 5 random numbers between 1 and 100."
        ),
        model=model,
        tool_details="A tool used to generate 5 random integers between 1 and 100.",
        tool_params=None,
    )

    with pytest.raises(
            NotImplementedError, match="MessageHistory output type is not supported with output_model at the moment."
    ):
        _ = rc.library.tool_call_llm(
            connected_nodes={rng_node},
            pretty_name="Math Node",
            system_message=rc.llm.SystemMessage(
                "You are a math genius that calls the RNG tool to generate 5 random numbers between 1 and 100 and gives the sum of those numbers."
            ),
            model=model,
            output_type="MessageHistory",
            output_model=math_output_model,
        )


@pytest.mark.asyncio
@pytest.mark.parametrize("nested_tool_node", NODE_INIT_METHODS, indirect=True)
async def test_nested_tool_functionality(nested_tool_node):
    """Test the functionality of nested ToolCallLLM nodes."""
    with rc.Runner(executor_config=rc.ExecutorConfig(logging_setting="QUIET")) as runner:
        message_history = rc.llm.MessageHistory(
            [
                rc.llm.UserMessage(
                    "Use the nested tool to perform a task."
                )
            ]
        )
        response = await runner.run(nested_tool_node, message_history=message_history)
        assert response.answer is not None
        assert "nested" in response.answer.lower()


@pytest.mark.asyncio
async def test_tool_with_llm_tool_as_input():
    """Test a tool that uses another LLM tool as input."""
    def print_hello(true_to_call: bool = True):
        return "Hello!"

    # Define the child tool
    child_tool = rc.library.tool_call_llm(
        connected_nodes={from_function(print_hello)},
        pretty_name="Child_Tool",
        system_message=rc.llm.SystemMessage("Provide a simple response when asked."),
        model=rc.llm.OpenAILLM("gpt-4o"),
        tool_details="A tool that generates a simple response.",
        tool_params={rc.llm.Parameter(name="response_request", param_type="string",
                                      description="A sentence that requests a response.")},
    )

    # Define the parent tool that uses the child tool
    parent_tool = rc.library.tool_call_llm(
        connected_nodes={child_tool},
        pretty_name="Parent_Tool",
        system_message=rc.llm.SystemMessage("Respond Hello using the child tool."),
        model=rc.llm.OpenAILLM("gpt-4o"),
    )

    # Run the parent tool
    with rc.Runner(executor_config=rc.ExecutorConfig(logging_setting="QUIET", timeout=1000)) as runner:
        message_history = rc.llm.MessageHistory(
            [
                rc.llm.UserMessage(
                    "Give me a response."
                )
            ]
        )
        response = await runner.run(parent_tool, message_history=message_history)

    assert response.answer is not None
