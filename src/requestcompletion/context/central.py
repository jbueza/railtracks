from __future__ import annotations

import contextvars
import warnings
from typing import Any

from requestcompletion.context.external import MutableExternalContext, ExternalContext


from requestcompletion.config import ExecutorConfig
from requestcompletion.context.internal import InternalContext


external_context: contextvars.ContextVar[ExternalContext] = contextvars.ContextVar(
    "external_context", default=MutableExternalContext()
)
config: contextvars.ContextVar[ExecutorConfig | None] = contextvars.ContextVar(
    "executor_config", default=None
)
thread_context: contextvars.ContextVar[InternalContext | None] = contextvars.ContextVar(
    "thread_context", default=None
)


def get_globals() -> InternalContext:
    """
    Get the global variables for the current thread.
    """
    if thread_context.get() is None:
        raise KeyError("No global variable set")

    return thread_context.get()


def register_globals(global_var: InternalContext):
    """
    Register the global variables for the current thread.
    """
    # TODO modify this to fail fast.
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

    new_context = current_context.prepare_new(new_parent_id)

    thread_context.set(new_context)


def delete_globals():
    thread_context.set(None)


def get(
    key: str,
    /,
    default: Any | None = None,
):
    """
    Get a value from the context object

    Args:
        key (str): The key to retrieve.
        default (Any | None): The default value to return if the key does not exist. If set to None and the key does not exist, a KeyError will be raised.
    Returns:
        Any: The value associated with the key, or the default value if the key does not exist.

    Raises:
        KeyError: If the key does not exist and no default value is provided.
    """
    context = external_context.get()
    return context.get(key, default=default)


def put(
    key: str,
    value: Any,
):
    """
    Set a value in the external context.

    :param key: The key to set.
    :param value: The value to associate with the key.
    """
    context = external_context.get()
    context.put(key, value)
