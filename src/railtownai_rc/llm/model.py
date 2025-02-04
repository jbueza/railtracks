###
# In the following document, we will use the interface types defined in this module to interact with the llama index to
# route to a given model.
###
import warnings
from typing import Literal, List, Generator


from pydantic import BaseModel


from .history import MessageHistory
from .response import Response
from .tools import Tool

from abc import ABC, abstractmethod


class ModelBase(ABC):
    @abstractmethod
    def chat(self, messages: MessageHistory, **kwargs) -> Response: ...

    @abstractmethod
    def structured(self, messages: MessageHistory, schema: BaseModel, **kwargs) -> Response: ...

    @abstractmethod
    def stream_chat(self, messages: MessageHistory, **kwargs) -> Response: ...

    @abstractmethod
    def chat_with_tools(self, messages: MessageHistory, tools: List[Tool], **kwargs) -> Response: ...
