###
# In the following document, we will use the interface types defined in this module to interact with the llama index to
# route to a given model.
###
from typing import List, Callable

from pydantic import BaseModel


from .history import MessageHistory
from .response import Response
from .tools import Tool

from abc import ABC, abstractmethod


class ModelBase(ABC):
    def __init__(
            self,
            pre_hook: List[Callable[[MessageHistory], MessageHistory]] | None = None,
            post_hook: List[Callable[[MessageHistory, Response], Response]] | None = None,
            exception_hook: List[Callable[[MessageHistory, Exception], None]] | None = None,
    ):
        if pre_hook is None:
            pre_hook: List[Callable[[MessageHistory], MessageHistory]] = []

        if post_hook is None:
            post_hook: List[Callable[[MessageHistory, Response], Response]] = []

        if exception_hook is None:
            exception_hook: List[Callable[[MessageHistory, Exception], None]] = []

        self._pre_hook = pre_hook
        self._post_hook = post_hook
        self._exception_hook = exception_hook


    def add_pre_hook(self, hook: Callable[[MessageHistory], MessageHistory]) -> None:
        """Adds a pre-hook to modify messages before sending them to the model."""
        self._pre_hook.append(hook)

    def add_post_hook(self, hook: Callable[[MessageHistory, Response], Response]) -> None:
        """Adds a post-hook to modify the response after receiving it from the model."""
        self._post_hook.append(hook)

    def add_exception_hook(self, hook: Callable[[MessageHistory, Exception], None]) -> None:
        """Adds an exception hook to handle exceptions during model interactions."""
        self._exception_hook.append(hook)

    def remove_pre_hooks(self) -> None:
        """Removes the pre-hook."""
        self._pre_hook = []

    def remove_post_hooks(self) -> None:
        """Removes the post-hook."""
        self._post_hook = []

    def remove_exception_hooks(self) -> None:
        """Removes the exception hook."""
        self._exception_hook = []

    @abstractmethod
    def model_name(self) -> str | None:
        return None

    @classmethod
    @abstractmethod
    def model_type(cls) -> str | None:
        return None

    def chat(
        self, messages: MessageHistory, **kwargs
    ) -> Response:
        """Chat with the model using the provided messages."""
        for hook in self._pre_hook:
            hook(messages)
        try:
            result = self._chat(messages, **kwargs)
        except Exception as e:
            for hook in self._exception_hook:
                hook(messages, e)
            raise e

        for hook in self._post_hook:
            result = hook(messages, result)

        return result

    def structured(
        self, messages: MessageHistory, schema: BaseModel, **kwargs
    ) -> Response:
        """Structured interaction with the model using the provided messages and schema."""
        for hook in self._pre_hook:
            hook(messages)

        try:
            result = self._structured(messages, schema, **kwargs)
        except Exception as e:
            for hook in self._exception_hook:
                hook(messages, e)
            raise e

        for hook in self._post_hook:
            result = hook(messages, result)

        return result

    def stream_chat(
        self, messages: MessageHistory, **kwargs
    ) -> Response:
        """Stream chat with the model using the provided messages."""
        # TODO figure out how to make this work with streamed tasks.
        for hook in self._pre_hook:
            hook(messages)

        result = self._stream_chat(messages, **kwargs)

        for hook in self._post_hook:
            result = hook(messages, result)

        return result

    def chat_with_tools(
        self, messages: MessageHistory, tools: List[Tool], **kwargs
    ) -> Response:
        """Chat with the model using the provided messages and tools."""
        for hook in self._pre_hook:
            hook(messages)

        try:
            result = self._chat_with_tools(messages, tools, **kwargs)
        except Exception as e:
            for hook in self._exception_hook:
                hook(messages, e)
            raise e

        for hook in self._post_hook:
            result = hook(messages, result)

        return result

    @abstractmethod
    def _chat(self, messages: MessageHistory, **kwargs) -> Response:
        pass

    @abstractmethod
    def _structured(
        self, messages: MessageHistory, schema: BaseModel, **kwargs
    ) -> Response:
        pass

    @abstractmethod
    def _stream_chat(self, messages: MessageHistory, **kwargs) -> Response:
        pass

    @abstractmethod
    def _chat_with_tools(
        self, messages: MessageHistory, tools: List[Tool], **kwargs
    ) -> Response:
        pass
