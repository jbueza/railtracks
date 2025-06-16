from ...llm import MessageHistory, ModelBase
from ..nodes import Node
from abc import ABC
from copy import deepcopy
from ...exceptions.node_invocation.validation import check_message_history
from ...exceptions import LLMError


class TerminalLLM(Node[str], ABC):
    """A simple LLM nodes that takes in a message and returns a response. It is the simplest of all llms."""

    def __init__(self, message_history: MessageHistory, model: ModelBase):
        """Creates a new instance of the TerminalLLM class

        Args:

        """
        super().__init__()
        self.model = model
        check_message_history(
            message_history
        )  # raises NodeInvocationError if any of the checks fail
        self.message_hist = deepcopy(message_history)

    async def invoke(self) -> str | None:
        """Makes a call containing the inputted message and system prompt to the model and returns the response

        Returns:
            (TerminalLLM.Output): The response message from the model
        """
        try:
            returned_mess = self.model.chat(self.message_hist)
        except Exception as e:
            raise LLMError(
                reason=f"Exception during model chat: {str(e)}",
                message_history=self.message_hist,
                exception_message=str(e),
            )

        self.message_hist.append(returned_mess.message)
        if returned_mess.message.role == "assistant":
            cont = returned_mess.message.content
            if cont is None:
                raise LLMError(
                    reason="ModelLLM returned None content",
                    message_history=self.message_hist,
                )
            return cont

        raise LLMError(
            reason="ModelLLM returned an unexpected message type.",
            message_history=self.message_hist,
        )
