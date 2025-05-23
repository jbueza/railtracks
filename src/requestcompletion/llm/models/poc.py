from src.requestcompletion.llm.models._litellm_wrapper import LiteLLMWrapper
from src.requestcompletion.llm import ToolCall, Tool, Parameter
from src.requestcompletion.llm.message import UserMessage, SystemMessage, AssistantMessage
from src.requestcompletion.llm.history import MessageHistory
from pydantic import BaseModel
import litellm
from typing import List
import json

# model = "gpt-3.5-turbo-1106"
# model = "gpt-4o"
model = "claude-3-sonnet-20240229"

def get_current_weather(location, unit="fahrenheit"):
    """Get the current weather in a given location"""
    if "tokyo" in location.lower():
        return json.dumps({"location": "Tokyo", "temperature": "10", "unit": "celsius"})
    elif "san francisco" in location.lower():
        return json.dumps({"location": "San Francisco", "temperature": "72", "unit": "fahrenheit"})
    elif "paris" in location.lower():
        return json.dumps({"location": "Paris", "temperature": "22", "unit": "celsius"})
    elif "new york" in location.lower():
        return json.dumps({"location": "New York", "temperature": "75", "unit": "fahrenheit"})
    else:
        return json.dumps({"location": location, "temperature": "unknown"})


def average_location_cost(location: str, num_days: int) -> float:
    """Returns the average cost of living in a location for a given number of days.
    Args:
        location (str): The location to get the cost of living for, e.g. "New York"
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
        "Vancouver": 200.0,
        "Toronto": 180.0,
    }
    daily_cost = daily_costs.get(location)
    if daily_cost is None:
        raise ValueError(f"Cost information not available for location: {location}")
    return daily_cost * num_days

def test_parallel_function_call():
    try:
        # Step 1: send the conversation and available functions to the model
        messages = [{"role": "user", "content": "Give me a summary for 2 day trip to New York. Use NewYork as an arg if ou are tool_calling"}]
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "average_location_cost",
                    "description": "Get the average cost of living in a location for a given number of days",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "The location to get the cost of living for.",
                            },
                            "num_days": {"type": "integer", "description": "The number of days for the trip"},
                        },
                        "required": ["location", "num_days"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_current_weather",
                    "description": "Get the current weather in a given location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "The city and state, e.g. San Francisco, CA",
                            },
                            "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                        },
                        "required": ["location"],
                    },
                },
            }
        ]
        response = litellm.completion(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="auto",  # auto is default, but we'll be explicit
        )
        print("\nFirst LLM Response:\n", response)
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        print("\nLength of tool calls", len(tool_calls))

        # Step 2: check if the model wanted to call a function
        if tool_calls:
            # Step 3: call the function
            # Note: the JSON response may not always be valid; be sure to handle errors
            available_functions = {
                "get_current_weather": get_current_weather,
                "average_location_cost": average_location_cost,
            }  
            messages.append(response_message)  # extend conversation with assistant's reply

            # Step 4: send the info for each function call and function response to the model
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_functions[function_name]
                function_args = json.loads(tool_call.function.arguments)
                print(function_args)
                function_response = function_to_call(**function_args)
                print(function_response)

                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": json.dumps(function_response),
                    }
                )  # extend conversation with function response

            second_response = litellm.completion(
                model=model,
                messages=messages,
            )  # get a new response from the model where it can see the function response
            print("\nSecond LLM response:\n", second_response)
            return second_response
    except Exception as e:
      print(f"Error occurred: {e}")

x = test_parallel_function_call()