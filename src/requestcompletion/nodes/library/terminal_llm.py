from ...llm import MessageHistory, ModelBase, Message
from ..nodes import Node
from abc import ABC
from copy import deepcopy
from ...exceptions import RCNodeCreationException

class TerminalLLM(Node[str], ABC):
    """A simple LLM nodes that takes in a message and returns a response. It is the simplest of all llms."""

    def __init__(self, message_history: MessageHistory, model: ModelBase):
        """Creates a new instance of the TerminalLLM class

        Args:

        """
        super().__init__()
        self.model = model

        # ========= Creation Exceptions =========
        if any(not isinstance(m, Message) for m in message_history):
            raise RCNodeCreationException(
                message="Message history must be a list of Message objects",
                notes=[
                    "System messages must be of type rc.llm.SystemMessage (not string)",
                    "User messages must be of type rc.llm.UserMessage (not string)",
                ],
            )
        elif len(message_history) == 0:
            raise RCNodeCreationException(
                message="Message history must contain at least one message",
                notes=["No messages provided"],
            )
        elif message_history[0].role != "system":
            raise RCNodeCreationException(
                message="Missing SystemMessage: The first message in the message history must be a system message"
            )
        # ========= End Creation Exceptions =========
        self.message_hist = deepcopy(message_history)

    async def invoke(self) -> str | None:
        """Makes a call containing the inputted message and system prompt to the model and returns the response

        Returns:
            (TerminalLLM.Output): The response message from the model
        """

        returned_mess = self.model.chat(self.message_hist)

        self.message_hist.append(returned_mess.message)
        if returned_mess.message.role == "assistant":
            cont = returned_mess.message.content
            return cont

