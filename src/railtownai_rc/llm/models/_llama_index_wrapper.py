from abc import abstractmethod
from typing import List


from llama_index.core.llms import ChatMessage
from llama_index.core.tools import FunctionTool

from ..model import ModelBase

from ..message import Message
from ..response import Response
from ..history import MessageHistory
from ..message import AssistantMessage
from ..content import ToolCall
from ..tools import Tool

from pydantic import BaseModel


def to_llama_chat(message: Message) -> ChatMessage:
    # TODO: complete this function. handling the special cases for content types.
    return ChatMessage(content=message.content, role=message.role)


def to_llama_tool(tool: Tool) -> FunctionTool:
    # TODO: complete this function.
    pass


class LlamaWrapper(ModelBase):
    def __init__(self, model_name: str, **kwargs):
        self._model_type = self.model_type()
        self._model_name = model_name
        self.model = self.setup_model_object(model_name, **kwargs)

    @classmethod
    @abstractmethod
    def setup_model_object(cls, model_name: str, **kwargs):
        pass

    @classmethod
    @abstractmethod
    def model_type(cls) -> str:
        pass

    def chat(self, messages: MessageHistory, **kwargs):

        response = self.model.chat([to_llama_chat(m) for m in messages], **kwargs)
        return Response(message=AssistantMessage(response.message.content))

    def structured(self, messages: MessageHistory, schema: BaseModel, **kwargs):
        return self.model.structured_predict(schema, [to_llama_chat(m) for m in messages], **kwargs)

    def stream_chat(self, messages: MessageHistory, **kwargs):
        message = self.model.stream_chat([to_llama_chat(m) for m in messages], **kwargs)

        # we need to get creative to map the provided streamer
        def map_to_string():
            for m in message:
                yield m.delta
            return

        return Response(message=None, streamer=map_to_string())

    def chat_with_tools(self, messages: MessageHistory, tools: List[FunctionTool], **kwargs):

        response = self.model.chat_with_tools(
            tools, chat_history=[to_llama_chat(m) for m in messages], strict=True, **kwargs
        )

        tool_calls = self.model.get_tool_calls_from_response(response, error_on_no_tool_call=False)
        if len(tool_calls) == 0:
            message = AssistantMessage(content=response.message.content)
            return Response(
                message=message,
            )

        message = AssistantMessage(
            content=[
                ToolCall(identifier=t_c.tool_id, name=t_c.tool_name, arguments=t_c.tool_kwargs) for t_c in tool_calls
            ],
        )
        return Response(message=message)

    def __str__(self):
        return f"Model(type={self._model_type}, name={self._model_name})"
