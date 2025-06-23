from ._base import OutputLessToolCallLLM
from ....llm import MessageHistory, ModelBase, SystemMessage
from abc import ABC


class LimitedToolCallLLM(OutputLessToolCallLLM[str], ABC):
    """
    An LLM node that allows only a limited number of tool call turns before forcing a final response.
    After the limit is reached, the LLM is prompted to respond directly without further tool calls.
    The deafult limit for tool calls is 1.
    """

    def __init__(
        self,
        message_history: MessageHistory,
        model: ModelBase,
        max_tool_calls: int = 1,
    ):
        """
        Args:
            message_history: Initial message history.
            model: The LLM model.
            max_tool_turns: Maximum number of tool call turns allowed. Deafult is set to a single toolcall

        Returns:
            String representing the final answer.
        """
        super().__init__(message_history, model, max_tool_calls=max_tool_calls)
        self.max_tool_calls = max_tool_calls
        assert self.message_hist[0].role == "system"
        # append a message to the system message, so that the LLM can plan out the tool calls
        self.message_hist[0] = SystemMessage(
            self.message_hist[0].content
            + "\n"
            + f"You are only allowed to make a maximum of {self.max_tool_calls} tool call(s) in total. "
            f"Do not exceed this limit. If you reach the limit, respond directly without any further tool calls. Extra tool "
            "calls will be ignored. Plan your tool usage carefully and do not exceed the limit under any circumstances."
        )

    def return_output(self) -> str:
        """Returns the last message in the message history."""
        return self.message_hist[-1].content

    # in the base class we throw exception, for this LLM we want to force a final answer
    async def _on_max_tool_calls_exceeded(self):
        returned_mess = self.model.chat_with_tools(self.message_hist, tools=[])
        self.message_hist.append(returned_mess.message)
