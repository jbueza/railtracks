import pytest
from requestcompletion import Node
from requestcompletion.nodes.library.tool_calling_llms.tool_call_llm import ToolCallLLM
from requestcompletion.nodes.library.tool_calling_llms._base import OutputLessToolCallLLM
from requestcompletion.llm import MessageHistory, SystemMessage, UserMessage, AssistantMessage, Tool
from requestcompletion.exceptions import LLMError, NodeCreationError

# ---- ToolCallLLM tests ----

def test_tool_call_llm_return_output_returns_last_message_content(mock_llm, mock_tool):
    class DummyToolCallLLM(ToolCallLLM):
        @classmethod
        def pretty_name(cls):
            return "Dummy"
        
        def connected_nodes(self):
            return {mock_tool}
        
    mh = MessageHistory([SystemMessage("sys"), UserMessage("hi"), AssistantMessage("final answer")])
    node = DummyToolCallLLM(mh, mock_llm())
    assert node.return_output() == "final answer"

# ---- OutputLessToolCallLLM tests ----

def test_outputless_tool_call_llm_create_node_success(mock_llm, mock_tool):
    class DummyLLM(OutputLessToolCallLLM):
        @classmethod
        def pretty_name(cls):
            return "Dummy"
        def connected_nodes(self):
            return {mock_tool}
        def return_output(self):
            return None
    mh = MessageHistory([SystemMessage("sys"), UserMessage("hi")])
    node = DummyLLM(mh, mock_llm())
    tool_name = mock_tool.tool_info().name
    result = node.create_node(tool_name, {"foo": "bar"})
    assert result is not None

def test_outputless_tool_call_llm_create_node_no_match(mock_llm, mock_tool):
    class DummyLLM(OutputLessToolCallLLM):
        @classmethod
        def pretty_name(cls):
            return "Dummy"
        def connected_nodes(self):
            return {mock_tool}
        def return_output(self):
            return None
    mh = MessageHistory([SystemMessage("sys"), UserMessage("hi")])
    node = DummyLLM(mh, mock_llm())
    with pytest.raises(LLMError, match="doesn't match any of the tool names"):
        node.create_node("nonexistent_tool", {})

def test_outputless_tool_call_llm_create_node_multiple_match(mock_llm, mock_tool):
    tool1 = Tool(name="duplicate", detail="duplicate does something", parameters=None)
    tool2 = Tool(name="duplicate", detail="duplicate does something else", parameters=None)
    class node1(Node):
        @classmethod
        def pretty_name(cls):
            return "name1"
        @classmethod
        def tool_info(cls):
            return tool1
    class node2(Node):
        @classmethod
        def pretty_name(cls):
            return "name2"
        @classmethod
        def tool_info(cls):
            return tool2
    class DummyLLM(OutputLessToolCallLLM):
        @classmethod
        def pretty_name(cls):
            return "Dummy"
        def connected_nodes(self):
            return {node1, node2}
        def return_output(self):
            return None
    mh = MessageHistory([SystemMessage("sys"), UserMessage("hi")])
    node = DummyLLM(mh, mock_llm())
    with pytest.raises(NodeCreationError, match="multiple nodes"):
        node.create_node("duplicate", {})

@pytest.mark.asyncio
async def test_outputless_tool_call_llm_on_max_tool_calls_exceeded(mock_llm, mock_tool):
    class DummyLLM(OutputLessToolCallLLM):
        @classmethod
        def pretty_name(cls):
            return "Dummy"
        def connected_nodes(self):
            return {mock_tool}
        def return_output(self):
            return None
    mh = MessageHistory([SystemMessage("sys"), UserMessage("hi")])
    node = DummyLLM(mh, mock_llm(), max_tool_calls=0)
    with pytest.raises(LLMError, match="Maximum number of tool calls"):
        await node._on_max_tool_calls_exceeded()