from __future__ import annotations

import contextvars
import queue
import threading
import warnings
from typing import TYPE_CHECKING, Callable, Literal

from .execution.publisher import RCPublisher, ExecutionConfigurations

if TYPE_CHECKING:
    from .run import Runner

config = contextvars.ContextVar("executor_config", default=None)
streamer = contextvars.ContextVar("data_streamer", default=None)

_local_store = threading.local()


class ThreadContext:

    def __init__(
        self,
        publisher: RCPublisher,
        parent_id: str | None,
    ):
        self._parent_id = parent_id
        self._publisher = publisher

    # Not super pythonic but it allows us to slap in debug statements on the getters and setters with ease
    @property
    def parent_id(self):
        return self._parent_id

    @parent_id.setter
    def parent_id(self, value: str):
        self._parent_id = value

    @property
    def publisher(self):
        return self._publisher

    @publisher.setter
    def publisher(self, value: RCPublisher):
        self._publisher = value

    def prepare_new(self, new_parent_id: str) -> ThreadContext:
        return ThreadContext(
            publisher=self._publisher,
            parent_id=new_parent_id,
        )


def get_globals() -> ThreadContext:
    """
    Get the global variables for the current thread.
    """
    if not hasattr(_local_store, "global_var"):
        raise KeyError("No global variable set")

    return _local_store.global_var


def register_globals(global_var: ThreadContext):
    """
    Register the global variables for the current thread.
    """
    if hasattr(_local_store, "global_var"):
        warnings.warn("Overwriting previous global variable")

    _local_store.global_var = global_var
