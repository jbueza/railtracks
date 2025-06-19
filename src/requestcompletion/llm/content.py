from __future__ import annotations

from typing import List, Any, Dict, AnyStr

from pydantic import BaseModel, Field

from ..prompts.prompt import format_message_with_context


####################################################################################################
# Simple helper Data Structures for common responses #
####################################################################################################

class ToolCall(BaseModel):
    """
    A simple model object that represents a tool call.

    This simple model represents a moment when a tool is called.
    """

    identifier: str = Field(description="The identifier attached to this tool call.")
    name: str = Field(description="The name of the tool being called.")
    arguments: Dict[str, Any] = Field(
        description="The arguments provided as input to the tool."
    )

    def __str__(self):
        return f"{self.name}({self.arguments})"


class Content(BaseModel):
    """
    A base model that represents the content of a message.
    """


class ToolCallList(Content):
    """
    A simple model object that represents a list of tool calls.

    This simple model should be used when adding a list of tool calls to a message.
    """
    tool_calls: List[ToolCall] = Field(
        description="A list of tool calls that were made during the conversation."
    )

    def __init__(self, tool_calls):
        # Allow positional argument for tool_calls
        if not isinstance(tool_calls, list):
            raise TypeError("tool_calls must be a list of ToolCall")

        super().__init__(tool_calls=tool_calls)

    @property
    def to_llm(self):
        """
        Convert the ToolCallList to a format suitable for LLM processing.
        """
        return self.tool_calls


class ToolResponse(Content):
    """
    A simple model object that represents a tool response.

    This simple model should be used when adding a response to a tool.
    """

    identifier: str = Field(
        description="The identifier attached to this tool response. This should match the identifier of the tool call."
    )
    name: str = Field(description="The name of the tool that generated this response.")
    result: AnyStr = Field(description="The result of the tool call.")

    def __str__(self):
        return f"{self.name} -> {self.result}"


class StringContent(Content):
    """
    A simple model object that represents a string content.

    This simple model should be used when adding a string content to a message.
    """

    string: str = Field(description="The string content of the message.")

    def __init__(self, string):
        # Allow positional argument for tool_calls
        if not isinstance(string, str):
            raise TypeError("base_model must be an instance of BaseModel")

        super().__init__(string=string)

    @property
    def to_llm(self):
        """
        Convert the StringContent to a format suitable for LLM processing.
        """
        return format_message_with_context(self.string)


class BaseModelContent(Content):
    """
    A simple model object that represents a base model content.

    This simple model should be used when adding a base model content to a message.
    """

    base_model: BaseModel = Field(
        description="The base model content of the message."
    )

    def __init__(self, base_model):
        # Allow positional argument for tool_calls
        if not isinstance(base_model, BaseModel):
            raise TypeError("base_model must be an instance of BaseModel")

        super().__init__(base_model=base_model)

    @property
    def to_llm(self):
        """
        Convert the BaseModelContent to a format suitable for LLM processing.
        """
        return self.content
