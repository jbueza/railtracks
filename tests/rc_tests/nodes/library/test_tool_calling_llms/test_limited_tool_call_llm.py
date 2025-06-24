import pytest
import requestcompletion as rc

from requestcompletion.exceptions import NodeCreationError, NodeInvocationError
from requestcompletion.llm import MessageHistory, UserMessage, SystemMessage, Message

from requestcompletion.nodes.library import from_function
from requestcompletion.nodes.library.tool_calling_llms.limited_tool_call_llm import LimitedToolCallLLM

class TestLimitedToolCallLLM:
    """ All tests for the LimitedToolCallLLM"""

    async def test_allows_only_one_toolcall_easy_wrapper(self, model, travel_planner_tools):
        """Test that LimitedToolCallLLM allows only one tool call turn before forcing a final answer."""
        test_node = rc.library.tool_call_llm(
            connected_nodes=set([from_function(tool) for tool in travel_planner_tools]),
            pretty_name="Limited Tool Call Test Node",
            system_message=rc.llm.SystemMessage(
                "You are a travel planner that will plan a trip. you have access to AvailableLocations, CurrencyUsed and AverageLocationCost tools. Use them when you need to."
            ),
            model=model,
            max_tool_calls=1,
        )

        message_history = MessageHistory(
            [UserMessage("I want to travel to New York from Vancouver for 4 days. Give me a budget summary for the trip in INR.")]
        )

        rc.context.put("tools_called", 0)
        response: Message = await rc.call(test_node, message_history=message_history)
        assert isinstance(response.content, str)
        assert rc.context.get("tools_called") == 1

    async def test_allows_only_one_toolcall_class_based(self, model, travel_planner_tools):
        """Test that LimitedToolCallLLM allows only one tool call turn before forcing a final answer."""
        
        class LimitedToolCallTestNode(LimitedToolCallLLM):
            """A test node for LimitedToolCallLLM that allows only 1 tool call turn."""
            def __init__(self, message_history: MessageHistory, model: rc.llm.ModelBase = model):
                message_history.insert(0, SystemMessage("You are a travel planner that will plan a trip. you have " \
                "access to AvailableLocations, CurrencyUsed and AverageLocationCost tools. Use them when you need to."))
                super().__init__(message_history, model, max_tool_calls=1)

            @classmethod
            def connected_nodes(cls):
                return set([from_function(tool) for tool in travel_planner_tools])
            
            @classmethod
            def pretty_name(cls) -> str:
                return "Limited Tool Call Test Node"

        message_history = MessageHistory(
            [UserMessage("I want to travel to New York from Vancouver for 4 days. Give me a budget summary for the trip in INR.")]
        )

        rc.context.put("tools_called", 0)
        response = await rc.call(LimitedToolCallTestNode, message_history=message_history)
        assert isinstance(response, str)
        assert rc.context.get("tools_called") == 1

    @pytest.mark.asyncio
    async def test_zero_tool_calls_forces_final_answer_easy_wrapper(self, model, travel_planner_tools):
        """Test that LimitedToolCallLLM with max_tool_calls=0 returns a final answer immediately."""
        test_node = rc.library.tool_call_llm(
            connected_nodes=set([from_function(tool) for tool in travel_planner_tools]),
            pretty_name="Limited Tool Call Test Node",
            system_message=rc.llm.SystemMessage(
                "You are a travel planner that will plan a trip. you have access to AvailableLocations, CurrencyUsed and AverageLocationCost tools. Use them when you need to."
            ),
            model=model,
            max_tool_calls=0,
        )

        message_history = MessageHistory(
            [UserMessage("Plan a trip to Paris for 2 days.")]
        )

        rc.context.put("tools_called", 0)
        response: Message = await rc.call(test_node, message_history=message_history)
        assert isinstance(response.content, str)
        assert rc.context.get("tools_called") == 0

    @pytest.mark.asyncio
    async def test_zero_tool_calls_forces_final_answer_class_based(self, model, travel_planner_tools):
        """Test that LimitedToolCallLLM with max_tool_calls=0 returns a final answer immediately."""
        class ZeroToolCallNode(LimitedToolCallLLM):
            def __init__(self, message_history: MessageHistory, model: rc.llm.ModelBase = model):
                message_history.insert(0, SystemMessage("You are a travel planner."))
                super().__init__(message_history, model, max_tool_calls=0)

            @classmethod
            def connected_nodes(cls):
                return set([from_function(tool) for tool in travel_planner_tools])

            @classmethod
            def pretty_name(cls) -> str:
                return "Zero Tool Call Node"

        message_history = MessageHistory(
            [UserMessage("Plan a trip to Paris for 2 days.")]
        )
        rc.context.put("tools_called", 0)
        response = await rc.call(ZeroToolCallNode, message_history=message_history)
        assert isinstance(response, str)
        assert rc.context.get("tools_called") == 0

    @pytest.mark.asyncio
    async def test_multiple_tool_calls_limit_easy_wrapper(self, model, travel_planner_tools):
        """Test that LimitedToolCallLLM allows up to N tool calls and then returns a final answer (easy wrapper)."""
        test_node = rc.library.tool_call_llm(
            connected_nodes=set([from_function(tool) for tool in travel_planner_tools]),
            pretty_name="Multi Tool Call Node",
            system_message=rc.llm.SystemMessage(
                "You are a travel planner."
            ),
            model=model,
            max_tool_calls=5,
        )

        message_history = MessageHistory(
            [UserMessage("Plan a trip to Paris, Berlin, and New York for 2 days each.")]
        )
        rc.context.put("tools_called", 0)
        response: Message = await rc.call(test_node, message_history=message_history)
        assert isinstance(response.content, str)
        assert rc.context.get("tools_called") <= 5

    @pytest.mark.asyncio
    async def test_multiple_tool_calls_limit_class_based(self, model, travel_planner_tools):
        """Test that LimitedToolCallLLM allows up to N tool calls and then returns a final answer."""
        class MultiToolCallNode(LimitedToolCallLLM):
            def __init__(self, message_history: MessageHistory, model: rc.llm.ModelBase = model):
                message_history.insert(0, SystemMessage("You are a travel planner."))
                super().__init__(message_history, model, max_tool_calls=5)

            @classmethod
            def connected_nodes(cls):
                return set([from_function(tool) for tool in travel_planner_tools])

            @classmethod
            def pretty_name(cls) -> str:
                return "Multi Tool Call Node"

        message_history = MessageHistory(
            [UserMessage("Plan a trip to Paris, Berlin, and New York for 2 days each.")]
        )
        rc.context.put("tools_called", 0)
        response = await rc.call(MultiToolCallNode, message_history=message_history)
        assert isinstance(response, str)
        assert rc.context.get("tools_called") <= 5

    @pytest.mark.asyncio
    async def test_negative_tool_calls_raises_easy_wrapper(self, model, travel_planner_tools):
        """Test that LimitedToolCallLLM raises if max_tool_calls is negative (easy wrapper)."""

        with pytest.raises(NodeCreationError, match="max_tool_calls must be a non-negative integer."):
            _ = rc.library.tool_call_llm(
                connected_nodes=set([from_function(tool) for tool in travel_planner_tools]),
                pretty_name="Negative Tool Call Node",
                system_message=rc.llm.SystemMessage(
                    "You are a travel planner."
                ),
                model=model,
                max_tool_calls=-1,
            )

    @pytest.mark.asyncio
    async def test_negative_tool_calls_raises_class_based(self, model, travel_planner_tools):
        """Test that LimitedToolCallLLM raises if max_tool_calls is negative."""
        class NegativeToolCallNode(LimitedToolCallLLM):
            def __init__(self, message_history: MessageHistory, model: rc.llm.ModelBase = model):
                message_history.insert(0, SystemMessage("You are a travel planner."))
                super().__init__(message_history, model, max_tool_calls=-1)

            @classmethod
            def connected_nodes(cls):
                return set([from_function(tool) for tool in travel_planner_tools])

            @classmethod
            def pretty_name(cls) -> str:
                return "Negative Tool Call Node"

        message_history = MessageHistory(
            [UserMessage("Plan a trip to Paris.")]
        )
        with pytest.raises(NodeInvocationError, match="max_tool_calls must be a non-negative integer."):    # invocation error because max_tool_calls can be injected at rc.call / run as well. 
            await rc.call(NegativeToolCallNode, message_history=message_history)


    @pytest.mark.asyncio
    async def test_context_reset_between_runs_easy_wrapper(self, model, simple_tools):
        """Test that tools_called context variable is reset between runs (easy wrapper)."""
        test_node = rc.library.tool_call_llm(
            connected_nodes={from_function(simple_tools)},
            pretty_name="Simple Tool Node",
            system_message=rc.llm.SystemMessage(
                "You are a number generator."
            ),
            model=model,
            max_tool_calls=1,
        )

        message_history = MessageHistory(
            [UserMessage("Give me a random number.")]
        )
        rc.context.put("tools_called", 0)
        response: Message = await rc.call(test_node, message_history=message_history)
        assert rc.context.get("tools_called") == 1

        # Reset context and run again
        rc.context.put("tools_called", 0)
        response2: Message = await rc.call(test_node, message_history=message_history)
        assert rc.context.get("tools_called") == 1

    @pytest.mark.asyncio
    async def test_works_with_different_tools_class_based(self, model, simple_tools):
        """Test LimitedToolCallLLM works with a different set of tools."""
        class SimpleToolNode(LimitedToolCallLLM):
            def __init__(self, message_history: MessageHistory, model: rc.llm.ModelBase = model):
                message_history.insert(0, SystemMessage("You are a number generator."))
                super().__init__(message_history, model, max_tool_calls=1)

            @classmethod
            def connected_nodes(cls):
                return {from_function(simple_tools)}

            @classmethod
            def pretty_name(cls) -> str:
                return "Simple Tool Node"

        message_history = MessageHistory(
            [UserMessage("Give me a random number.")]
        )
        rc.context.put("tools_called", 0)
        response = await rc.call(SimpleToolNode, message_history=message_history)
        assert isinstance(response, str)
        assert rc.context.get("tools_called") == 1

    @pytest.mark.asyncio
    async def test_works_with_different_tools_easy_wrapper(self, model, simple_tools):
        """Test LimitedToolCallLLM works with a different set of tools (easy wrapper)."""
        test_node = rc.library.tool_call_llm(
            connected_nodes={from_function(simple_tools)},
            pretty_name="Simple Tool Node",
            system_message=rc.llm.SystemMessage(
                "You are a number generator."
            ),
            model=model,
            max_tool_calls=1,
        )

        message_history = MessageHistory(
            [UserMessage("Give me a random number.")]
        )
        rc.context.put("tools_called", 0)
        response: Message = await rc.call(test_node, message_history=message_history)
        assert isinstance(response.content, str)
        assert rc.context.get("tools_called") == 1

    @pytest.mark.asyncio
    async def test_context_reset_between_runs_class_based(self, model, simple_tools):
        """Test that tools_called context variable is reset between runs."""
        class SimpleToolNode(LimitedToolCallLLM):
            def __init__(self, message_history: MessageHistory, model: rc.llm.ModelBase = model):
                message_history.insert(0, SystemMessage("You are a number generator."))
                super().__init__(message_history, model, max_tool_calls=1)

            @classmethod
            def connected_nodes(cls):
                return {from_function(simple_tools)}

            @classmethod
            def pretty_name(cls) -> str:
                return "Simple Tool Node"

        message_history = MessageHistory(
            [UserMessage("Give me a random number.")]
        )
        rc.context.put("tools_called", 0)
        response = await rc.call(SimpleToolNode, message_history=message_history)
        assert rc.context.get("tools_called") == 1

        # Reset context and run again
        rc.context.put("tools_called", 0)
        response2 = await rc.call(SimpleToolNode, message_history=message_history)      # this run should be unaffected by the previous run
        assert rc.context.get("tools_called") == 1

    def run_all_tests(self):
        self.test_allows_only_one_toolcall_class_based()
        self.test_zero_tool_calls_forces_final_answer_class_based()
        self.test_multiple_tool_calls_limit_class_based()
        self.test_negative_tool_calls_raises_class_based()
        self.test_works_with_different_tools_class_based()
        self.test_context_reset_between_runs_class_based()
 
@pytest.mark.asyncio
async def limited_tool_call_tests(model, travel_planner_tools):
    tests = TestLimitedToolCallLLM(model, travel_planner_tools)
    await tests.run_all_tests()
