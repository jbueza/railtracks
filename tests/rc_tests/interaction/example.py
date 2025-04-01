import pytest
from typing import List
import src.requestcompletion as rc
import asyncio


def model():
    return rc.llm.OpenAILLM("gpt-4o")
    
def tool_call_llm_system_messages():
    system_currency_converter = rc.llm.SystemMessage("You are a currency converter that will convert currencies. you have access to AvailabelCurrencies and ConvertCurrency tools. Use them when you need to.")
    system_travel_planner = rc.llm.SystemMessage("You are a travel planner that will plan a trip. you have access to AvailableLocations, CurrencyUsed and AverageLocationCost tools. Use them when you need to.")
    return system_currency_converter, system_travel_planner

def curreny_converter_tools():
    def available_currencies() -> List[str]:
        """Returns a list of available currencies.
        Args:
        Returns:
            List[str]: A list of available currencies.
        """
        return ["USD", "EUR", "INR"]
    
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
    
    return available_currencies, convert_currency

def travel_planner_tools():
    def available_locations() -> List[str]:
        """Returns a list of available locations.
        Args:
        Returns:
            List[str]: A list of available locations.
        """
        return ["New York", "Los Angeles", "Chicago", "Delhi", "Mumbai", "Bangalore", "Paris", "Denmark", "Sweden", "Norway", "Germany"]
    
    def currency_used(location: str) -> str:
        """Returns the currency used in a location.
        Args:
            location (str): The location to get the currency used for.
        Returns:
            str: The currency used in the location.
        """
        location_currency_map = {
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
        currency_used =  location_currency_map.get(location)
        if currency_used is None:
            raise ValueError(f"Currency not found for location: {location}")
        return currency_used
    
    
    def average_location_cost(location: str, num_days: int) -> float:
        """Returns the average cost of living in a location for a given number of days.
        Args:
            location (str): The location to get the cost of living for.
            num_days (int): The number of days for the trip.
        Returns:
            float: The average cost of living in the location.
        """
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

    return available_locations, currency_used, average_location_cost


def tool_calling_nodes():
    """
    Returns the appropriate nodes based on the parametrized fixture name.
    """
    available_currencies, convert_currency = curreny_converter_tools()
    available_locations, currency_used, average_location_cost = travel_planner_tools()
    system_currency_converter, system_travel_planner = tool_call_llm_system_messages()
    
    AvailableCurrencies = rc.library.from_function(available_currencies)
    ConvertCurrency = rc.library.from_function(convert_currency)
    AvailableLocations = rc.library.from_function(available_locations)
    CurrencyUsed = rc.library.from_function(currency_used)
    AverageLocationCost = rc.library.from_function(average_location_cost)

    currrency_converter_node = rc.library.tool_call_llm(connected_nodes=[AvailableCurrencies, ConvertCurrency], pretty_name="Currency Converter Node", system_message=system_currency_converter, model=model())
    travel_planner_node = rc.library.tool_call_llm(connected_nodes=[AvailableLocations, CurrencyUsed, AverageLocationCost], pretty_name="Travel Planner Node", system_message=system_travel_planner, model=model())
    
    return currrency_converter_node, travel_planner_node

if __name__ == "__main__":
    currrency_converter_node, travel_planner_node = tool_calling_nodes()
    
    async def travel_summarizer_node(message_history: rc.llm.MessageHistory):
        # First node call
        travel_planner_response = await rc.call(travel_planner_node, message_history=message_history)
        message_history.append(rc.llm.AssistantMessage("The travel plan: " + str(travel_planner_response)))

        response = await rc.call(currrency_converter_node, message_history=message_history)
        return response

    TrravelSummarizerNode = rc.library.from_function(travel_summarizer_node)

    async def main():
        with rc.Runner() as runner:
            message_history = rc.llm.MessageHistory([rc.llm.UserMessage("I live in Delhi. I want to go to Denmark for 3 days, then to Germany for 2 days. Please provide me with a budget summary for the trip.")])
            response = await runner.run(TrravelSummarizerNode, message_history=message_history)
            print(response)

    asyncio.run(main())
