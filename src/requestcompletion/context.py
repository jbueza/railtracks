from __future__ import annotations

import contextvars
import queue
import threading
import warnings
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from .run import Runner

config = contextvars.ContextVar("executor_config", default=None)
streamer = contextvars.ContextVar("data_streamer", default=None)

_local_store = threading.local()


class ThreadContext:

    def __init__(
        self,
    ):
        self._parent_id = None
        self._active_runner = None

    def __new__(cls, *args, **kwargs):
        if not hasattr(_local_store, "thread_context"):
            _local_store.thread_context = super(ThreadContext, cls).__new__(cls)

        return _local_store.thread_context

    @property
    def parent_id(self):
        return self._parent_id

    @parent_id.setter
    def parent_id(self, value: str):
        self._parent_id = value

    @property
    def active_runner(self):
        return self._active_runner

    @active_runner.setter
    def active_runner(self, value: "Runner"):
        self._active_runner = value

    def reset(self):
        self._parent_id = None
        self._active_runner = None


def set_runner(runner: "Runner"):
    """
    Set the active runner for the current thread.
    """
    _local_store.active_runner = runner


def get_runner() -> Runner | None:
    """
    Get the active runner for the current thread.
    """
    attr = getattr(_local_store, "active_runner", None)
    return attr


def set_parent_id(parent_id: str):
    """
    Set the parent id for the current thread.
    """
    _local_store.parent_id = parent_id


def get_parent_id() -> str | None:
    """
    Get the parent id for the current thread.
    """
    return getattr(_local_store, "parent_id", None)


def reset_context():
    """
    Reset the context for the current thread.
    """
    _local_store.active_runner = None
    _local_store.parent_id = None
