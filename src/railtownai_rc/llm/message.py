from enum import Enum
from typing import Literal, Generic, Any, TypeVar

from .content import Content


_T = TypeVar("_T", bound=Content)


class Role(str, Enum):
    assistant = "assistant"
    user = "user"
    system = "system"
    tool = "tool"


class Message(Generic[_T]):
    def __init__(self, content: _T, role: Literal["assistant", "user", "system", "tool"]):
        """
        A simple class that represents a message that an LLM can read.

        Args:
            content: The content of the message. It can take on any of the following types:
                - str: A simple string message.
                - List[ToolCall]: A list of tool calls.
                - ToolResponse: A tool response.
                - BaseModel: A custom base model object.
            role: The role of the message (assistant, user, system, tool, etc.).
        """
        self.validate_content(content)
        self._content = content
        self._role = Role(role)

    @classmethod
    def validate_content(cls, content):
        pass

    @property
    def content(self) -> _T:
        """Collects the content of the message."""
        return self._content

    @property
    def role(self) -> Role:
        """Collects the role of the message."""
        return self._role

    def __str__(self):
        return f"{self.role}: {self.content}"
    
    def __repr__(self):
        return str(self)


class _StringOnlyContent(Message[str]):
    @classmethod
    def validate_content(cls, content: str):
        if not isinstance(content, str):
            raise ValueError(f"A {cls.__name__} needs a string but got {type(content)}")


class UserMessage(_StringOnlyContent):
    """
    A simple class that represents a user message.

    Note that we only support string input
    """

    def __init__(self, content: str):
        super().__init__(content=content, role="user")


class SystemMessage(_StringOnlyContent):
    """
    A simple class that represents a system message.
    """

    def __init__(self, content: str):
        super().__init__(content=content, role="system")


class AssistantMessage(Message[_T], Generic[_T]):
    """
    A simple class that represents a message from the assistant.
    """

    def __init__(self, content: _T):
        super().__init__(content=content, role="assistant")


# TODO further constrict the possible return type of a ToolMessage.
class ToolMessage(Message[_T], Generic[_T]):
    """
    A simple class that represents a message that is a tool call answer.
    """

    def __init__(self, content: _T, identifier: str | None = None):
        super().__init__(content=content, role="tool")
        self.identifier = identifier
