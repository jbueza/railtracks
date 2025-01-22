###
# In the following document, we will use the interface types defined in this module to interact with the llama index to
# route to a given model.
###
import warnings
from typing import Literal, List

from llama_index.llms.openai import OpenAI
from llama_index.llms.anthropic import Anthropic
from llama_index.core import Settings
from llama_index.core.llms import ChatResponse, ChatMessage
from llama_index.core.tools import FunctionTool

from pydantic import BaseModel

from .content import ToolCall
from .history import MessageHistory
from .message import AssistantMessage, Message
from .response import Response


def to_llama_chat(message: Message) -> ChatMessage:
    # TODO: complete this function. handling the special cases for content types.
    return ChatMessage(content=message.content, role=message.role)


class Model:
    def __init__(self, model_type: Literal["OpenAI", "Anthropic"], model_name: str, **kwargs):
        self.model = self.setup_model_object(model_type, model_name, **kwargs)

    @classmethod
    def _check_kwargs(cls, problematic_kwargs: List[str], **kwargs):
        """
        Checks the kwargs for the model to ensure that there is no conflicts related to our additional functionality
        tied to the wrapper.

        Args:
            **kwargs: The keyword arguments to be checked.

        Returns: None

        """
        # TODO: finish checking all the problematic params here
        for arg in problematic_kwargs:
            if arg in kwargs:
                warnings.warn(
                    f"You have set the {arg} flag. This will cause undetermined behavior. Please use the defined methods instead"
                )

    @classmethod
    def setup_model_object(cls, model_type: Literal["OpenAI", "Anthropic"], model_name: str, **kwargs):
        """
        Sets up and returns a model object based on the model type and name.

        This set up will include setting the tokenizer and preparing the model object you will interact with.

        Args:
            model_type: The type of model to be used.
            model_name: The string name of the model you would like to use.
            **kwargs: The keyword arguments you would like to pass into the model. Please refer to the documentation of
             the specific model for the available arguments.

        Returns:

        """
        if model_type == "OpenAI":
            # the default tokenizer `tiktoken` is good enough.
            return OpenAI(model_name, **kwargs)
        elif model_type == "Anthropic":
            # we will have to use a special tokenizer for this model.
            Settings.tokenizer = Anthropic().tokenizer
            return Anthropic(model_name, **kwargs)
        else:
            raise ValueError(f"Model type {model_type} not supported")

    def chat(self, messages: MessageHistory, tools: List[FunctionTool] = None, **kwargs):
        if len(tools) != 0:
            return self._chat_with_tool(messages, tools, **kwargs)

        return self._regular_chat(messages, **kwargs)

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

    def _regular_chat(self, messages: MessageHistory, **kwargs):
        response = self.model.chat([to_llama_chat(m) for m in messages], **kwargs)
        return Response(message=AssistantMessage(response.message.content))

    def _chat_with_tool(self, messages: MessageHistory, tools: List[FunctionTool], **kwargs):

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
