from typing import TypeVar, Type

from ...llm import MessageHistory, ModelBase
from src.requestcompletion.nodes.nodes import Node, ResetException

from pydantic import BaseModel
from abc import ABC, abstractmethod

_TOutput = TypeVar("_TOutput", bound=BaseModel)


class StructuredLLM(Node[_TOutput], ABC):

    # TODO: allow for more general (non-pydantic) outputs
    @classmethod
    @abstractmethod
    def output_model(cls) -> Type[_TOutput]: ...

    def __init__(self, message_history: MessageHistory, model: ModelBase):
        """Creates a new instance of the TerminalLLM class

        Args:

        """
        super().__init__()
        self.model = model
        self.message_hist = message_history

    def invoke(self) -> _TOutput:
        """Makes a call containing the inputted message and system prompt to the model and returns the response

        Returns:
            (TerminalLLM.Output): The response message from the model
        """
        try:
            returned_mess = self.model.structured(self.message_hist, schema=self.output_model())
        except Exception as e:
            raise ResetException(node=self, detail=f"{e}")

        self.message_hist.append(returned_mess.message)

        if returned_mess.message.role == "assistant":
            cont = returned_mess.message.content
            if cont is None:
                raise ResetException(node=self, detail="The LLM returned no content")
            if isinstance(cont, self.output_model()):
                return cont
            raise ResetException(node=self, detail="The LLM returned content does not match the expected return type")

        raise ResetException(
            node=self,
            detail="ModelLLM returned an unexpected message type.",
        )
