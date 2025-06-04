from __future__ import annotations

import contextvars
import warnings
from functools import wraps

from src.requestcompletion.pubsub.publisher import RCPublisher


config = contextvars.ContextVar("executor_config", default=None)
streamer = contextvars.ContextVar("data_streamer", default=None)
thread_context: contextvars.ContextVar[ThreadContext | None] = contextvars.ContextVar(
    "thread_context", default=None
)


class ThreadContext:
    """
    The ThreadContext class is used to store global variables designed to be used in the RC system.

    The tooling in the class is very tightly dependent on the requirements of the RC system.
    """

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
        """
        Prepares a new ThreadContext with a new parent ID.

        Note: the previous publisher will copied by reference into the next object.
        """

        return ThreadContext(
            publisher=self._publisher,
            parent_id=new_parent_id,
        )


def register_global_wrapper(parent_id: str | None = None):
    """
    A decorator designed to wrap a function registering the global variables before executing it.
    """
    parent_global_variables = get_globals()

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Register the global variables before executing the function
            register_globals(
                parent_global_variables.prepare_new(new_parent_id=parent_id)
            )

            return func(*args, **kwargs)

        return wrapper

    return decorator


def get_globals() -> ThreadContext:
    """
    Get the global variables for the current thread.
    """
    if thread_context.get() is None:
        raise KeyError("No global variable set")

    return thread_context.get()


def register_globals(global_var: ThreadContext):
    """
    Register the global variables for the current thread.
    """
    if thread_context.get():
        warnings.warn("Overwriting previous global variable")

    thread_context.set(global_var)


def update_parent_id(new_parent_id: str):
    """
    Update the parent ID of the current thread's global variables.
    """
    current_context = thread_context.get()
    if current_context is None:
        raise KeyError("No global variable set")

    current_context.parent_id = new_parent_id
    thread_context.set(current_context)


def delete_globals():
    thread_context.set(None)
