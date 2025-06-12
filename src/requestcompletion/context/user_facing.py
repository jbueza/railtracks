from .external import ImmutableExternalContext
from typing import Any

protected_context = ImmutableExternalContext()


def get(
    key: str,
    default: Any | None = None,
):
    """
    Get a value from the external context.

    :param key: The key to retrieve.
    :param default: The default value to return if the key is not found.
    :return: The value associated with the key or the default value.
    """
    return protected_context.get(key, default=default)


def put(
    key: str,
    value: Any,
):
    """
    Set a value in the external context.

    :param key: The key to set.
    :param value: The value to associate with the key.
    """
    protected_context.put(key, value)
