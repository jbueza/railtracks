import pytest
import src.requestcompletion as rc
from pydantic import BaseModel, Field
from itertools import product

# ============ TEST CASES ===========
NODE_INIT_METHODS = ["easy_wrapper", "class_based"]     # !!! TODO: easy_usage_wrapper implementation 


simple_model_test_cases = list(product(NODE_INIT_METHODS, ["simple_model"]))
@pytest.mark.asyncio
@pytest.mark.parametrize("simple_node", simple_model_test_cases, indirect=True)
async def test_no_tools_connected(simple_node, simple_output_model):
    """Test basic functionality of returning a structured output."""
    with rc.Runner() as runner:
        message_history = rc.llm.MessageHistory([rc.llm.UserMessage("Generate a simple text and number.")])
        response = await runner.run(
            simple_node, message_history=message_history
        )
        print(response.answer)
        assert isinstance(response.answer, simple_output_model)
        assert isinstance(response.answer.text, str)
        assert isinstance(response.answer.number, int)


empty_model_test_cases = list(product(NODE_INIT_METHODS, ["empty_model"]))
@pytest.mark.asyncio
@pytest.mark.parametrize("simple_node", empty_model_test_cases, indirect=True)
async def test_empty_model(simple_node, empty_output_model):
    """Test when the output model is empty."""
    with rc.Runner() as runner:
        message_history = rc.llm.MessageHistory([rc.llm.UserMessage("Generate a simple text and number.")])
        response = await runner.run(
            simple_node, message_history=message_history
        )
        print(response.answer)
        print("type: ", type(response.answer))
        assert isinstance(response.answer, BaseModel)      # might be because of fictures, check the test case !!!TODO


@pytest.mark.asyncio
@pytest.mark.parametrize("travel_planner_node", NODE_INIT_METHODS, indirect=True)
async def test_structured_tool_call_llm(travel_planner_node, travel_planner_output_model):
    """Test the functionality of a ToolCallLLM node (using actual tools) with a structured output model."""
    with rc.Runner() as runner:
        message_history = rc.llm.MessageHistory([rc.llm.UserMessage("I live in Delhi. I am going to travel to Denmark for 3 days, followed by Germany for 2 days and finally New York for 4 days. Please provide me with a budget summary for the trip in INR.")])
        response = await runner.run(travel_planner_node, message_history=message_history)
        print(response.answer)
        assert isinstance(response.answer, travel_planner_output_model)
        assert isinstance(response.answer.travel_plan, str)
        assert isinstance(response.answer.Total_cost, float)
        assert isinstance(response.answer.Currency, str)

@pytest.mark.asyncio
@pytest.mark.parametrize("math_node", NODE_INIT_METHODS, indirect=True)
async def test_structured_tool_call_llm_with_terminal_llm_as_tool(math_node, math_output_model):
    """Test the functionality of a ToolCallLLM node (using terminalLLM as tool) with a structured output model."""
    with rc.Runner() as runner:
        message_history = rc.llm.MessageHistory([rc.llm.UserMessage("Start the Math node.")])
        response = await runner.run(math_node, message_history=message_history)
        print(response.answer)
        assert isinstance(response.answer, math_output_model)
        assert isinstance(response.answer.sum, float)
        assert isinstance(response.answer.random_numbers, list)
    