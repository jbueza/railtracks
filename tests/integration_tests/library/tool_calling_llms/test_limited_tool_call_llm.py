import pytest
import requestcompletion as rc
from requestcompletion.exceptions import NodeCreationError, NodeInvocationError

@pytest.mark.asyncio
@pytest.mark.parametrize("class_based", [True, False], ids=["class_based", "easy_usage_wrapper"])
async def test_allows_only_one_toolcall(limited_tool_call_node_factory, travel_message_history, reset_tools_called, class_based):
    node = limited_tool_call_node_factory(max_tool_calls=1, class_based=class_based)
    message_history = travel_message_history()
    reset_tools_called()
    response = await rc.call(node, message_history=message_history)
    if class_based:
        assert isinstance(response, str)
    else:
        assert isinstance(response.content, str)
    assert rc.context.get("tools_called") == 1

@pytest.mark.asyncio
@pytest.mark.parametrize("class_based", [True, False], ids=["class_based", "easy_usage_wrapper"])
async def test_zero_tool_calls_forces_final_answer(limited_tool_call_node_factory, travel_message_history, reset_tools_called, class_based):
    node = limited_tool_call_node_factory(max_tool_calls=0, class_based=class_based)
    message_history = travel_message_history("Plan a trip to Paris for 2 days.")
    reset_tools_called()
    response = await rc.call(node, message_history=message_history)
    if class_based:
        assert isinstance(response, str)
    else:
        assert isinstance(response.content, str)
    assert rc.context.get("tools_called") == 0

@pytest.mark.asyncio
@pytest.mark.parametrize("class_based", [True, False], ids=["class_based", "easy_usage_wrapper"])
async def test_multiple_tool_calls_limit(limited_tool_call_node_factory, travel_message_history, reset_tools_called, class_based):
    node = limited_tool_call_node_factory(max_tool_calls=5, class_based=class_based)
    message_history = travel_message_history("Plan a trip to Paris, Berlin, and New York for 2 days each.")
    reset_tools_called()
    response = await rc.call(node, message_history=message_history)
    if class_based:
        assert isinstance(response, str)
    else:
        assert isinstance(response.content, str)
    assert rc.context.get("tools_called") <= 5

@pytest.mark.asyncio
@pytest.mark.parametrize("class_based", [True, False], ids=["class_based", "easy_usage_wrapper"])
async def test_negative_tool_calls_raises(limited_tool_call_node_factory, travel_message_history, class_based):
    if not class_based:
        with pytest.raises(NodeCreationError, match="max_tool_calls must be a non-negative integer."):
            limited_tool_call_node_factory(max_tool_calls=-1, class_based=False)
    else:
        node = limited_tool_call_node_factory(max_tool_calls=-1, class_based=True)
        message_history = travel_message_history("Plan a trip to Paris.")
        with pytest.raises(NodeInvocationError, match="max_tool_calls must be a non-negative integer."):
            await rc.call(node, message_history=message_history)

@pytest.mark.asyncio
@pytest.mark.parametrize("class_based", [True, False], ids=["class_based", "easy_usage_wrapper"])
async def test_context_reset_between_runs(limited_tool_call_node_factory, travel_message_history, reset_tools_called, class_based):
    @rc.to_node
    def magic_number():
        #  incrementing count for testing purposes
        count = rc.context.get("tools_called", -1)
        rc.context.put("tools_called", count + 1)
        return 42
    
    node = limited_tool_call_node_factory(max_tool_calls=1, class_based=class_based, tools=[magic_number])
    message_history = travel_message_history("Get the magic number and divide it by 2.")
    reset_tools_called()
    response = await rc.call(node, message_history=message_history)
    assert rc.context.get("tools_called") == 1
    reset_tools_called()
    response2 = await rc.call(node, message_history=message_history)
    assert rc.context.get("tools_called") == 1
