import warnings

from ...llm import MessageHistory, ModelBase, SystemMessage
from ..nodes import Node

from abc import ABC


def terminal_llm(
    pretty_name: str | None = None,
    system_message: SystemMessage | None = None,
    model: ModelBase | None = None,
):
    class TerminalLLMNode(TerminalLLM):
        def __init__(
            self,
            message_history: MessageHistory,
            llm_model: ModelBase | None = None,
        ):
            if system_message is not None:
                if len([x for x in message_history if x.role == "system"]) > 0:
                    warnings.warn("System message already exists in message history. We will replace it.")
                    message_history = [x for x in message_history if x.role != "system"]
                    message_history.insert(0, system_message)
                else:
                    message_history.insert(0, system_message)

            if llm_model is not None:
                if model is not None:
                    warnings.warn(
                        "You have provided a model as a parameter and as a class variable. We will use the parameter."
                    )
            else:
                if model is None:
                    raise RuntimeError("You Must provide a model to the TerminalLLM class")
                llm_model = model

            super().__init__(message_history=message_history, model=llm_model)

        @classmethod
        def pretty_name(cls) -> str:
            if pretty_name is None:
                return "TerminalLLM"
            else:
                return pretty_name

    return TerminalLLMNode


class TerminalLLM(Node[str], ABC):
    """A simple LLM nodes that takes in a message and returns a response. It is the simplest of all llms."""

    def __init__(self, message_history: MessageHistory, model: ModelBase):
        """Creates a new instance of the TerminalLLM class

        Args:

        """
        super().__init__()
        self.model = model
        self.message_hist = message_history

    async def invoke(self) -> str:
        """Makes a call containing the inputted message and system prompt to the model and returns the response

        Returns:
            (TerminalLLM.Output): The response message from the model
        """

        returned_mess = self.model.chat(self.message_hist)

        self.message_hist.append(returned_mess.message)

        if returned_mess.message.role == "assistant":
            cont = returned_mess.message.content
            return cont
