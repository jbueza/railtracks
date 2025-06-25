import pytest
from requestcompletion.nodes.library import tool_call_llm, LimitedToolCallLLM
from requestcompletion.llm import MessageHistory, ToolMessage, SystemMessage, UserMessage, AssistantMessage, ToolCall, ToolResponse


def test_limited_tool_call_llm_init_appends_system_message(model, mock_tool):
    """Test that the system message has the max tool calls limit."""
    class MockLimitedToolCallLLM(LimitedToolCallLLM):
       @classmethod
       def pretty_name(cls):
           return "Mock Limited Tool Call LLM"
       
       def connected_nodes(self):
           return {mock_tool}
        
    mh = MessageHistory([SystemMessage("system prompt"), UserMessage("hello")])
    node = MockLimitedToolCallLLM(mh, model(), max_tool_calls=2)
    assert "maximum of 2 tool call(s)" in node.message_hist[0].content

def test_limited_tool_call_llm_return_output(mock_tool, model):
    class MockLimitedToolCallLLM(LimitedToolCallLLM):
       @classmethod
       def pretty_name(cls):
           return "Mock Limited Tool Call LLM"
       
       def connected_nodes(self):
           return {mock_tool}
    
    mh = MessageHistory([SystemMessage("system prompt"), UserMessage("hello")])
    node = MockLimitedToolCallLLM(mh, model())
    node.message_hist.append(AssistantMessage(content="The answer"))
    assert node.return_output() == "The answer"

@pytest.mark.asyncio
async def test_limited_tool_call_llm_on_max_tool_calls_exceeded_appends_final_answer(mock_tool, model):
    class MockLimitedToolCallLLM(LimitedToolCallLLM):
       @classmethod
       def pretty_name(cls):
           return "Mock Limited Tool Call LLM"
       
       def connected_nodes(self):
           return {mock_tool}
    
    mh = MessageHistory([SystemMessage("system prompt"), 
                         UserMessage("hello"),
                         AssistantMessage([ToolCall(identifier="test", name="last tool call", arguments={})]),  # mock model expects the tool call name
                         ToolMessage(ToolResponse(identifier="test", name="last tool call", result="The answer"))
                        ])
    # if tool response has name "last tool call", then the mock model will return "Final answer after tool calls exhausted."
    node = MockLimitedToolCallLLM(mh, model())
    await node._on_max_tool_calls_exceeded()
    assert isinstance(node.message_hist[-1], AssistantMessage)
    assert node.message_hist[-1].content == "Final answer after tool calls exhausted."

def test_tool_call_llm_init_appends_system_message(model, mock_tool):
    ToolCallLLM = tool_call_llm(
        connected_nodes={mock_tool},
        pretty_name="Test ToolCallLLM",
        model=model(),
        max_tool_calls=2,
        system_message="system prompt"
    )
    mh = MessageHistory([UserMessage("hello")])
    node = ToolCallLLM(mh)
    assert "system prompt" in node.message_hist[0].content

def test_tool_call_llm_return_output_last_message(model, mock_tool):
    ToolCallLLM = tool_call_llm(
        connected_nodes={mock_tool},
        pretty_name="Test ToolCallLLM",
        model=model(),
        output_type="LastMessage"
    )
    mh = MessageHistory([SystemMessage("system prompt"), UserMessage("hello")])
    node = ToolCallLLM(mh)
    node.message_hist.append(AssistantMessage(content="The answer"))
    assert node.return_output().content == "The answer"

def test_tool_call_llm_connected_nodes(model, mock_tool):
    ToolCallLLM = tool_call_llm(
        connected_nodes={mock_tool},
        pretty_name="Test ToolCallLLM",
        model=model()
    )
    mh = MessageHistory([SystemMessage("system prompt"), UserMessage("hello")])
    node = ToolCallLLM(mh)
    assert mock_tool in node.connected_nodes()

def test_tool_call_llm_pretty_name_default(model, mock_tool):
    ToolCallLLM = tool_call_llm(
        connected_nodes={mock_tool},
        model=model()
    )
    assert "ToolCallLLM" in ToolCallLLM.pretty_name()

def test_tool_call_llm_with_output_type_message_history(model, mock_tool):
    ToolCallLLM = tool_call_llm(
        connected_nodes={mock_tool},
        pretty_name="Test ToolCallLLM",
        model=model(),
        output_type="MessageHistory"
    )
    mh = MessageHistory([SystemMessage("system prompt"), UserMessage("hello")])
    node = ToolCallLLM(mh)
    assert isinstance(node.return_output(), MessageHistory)
