import contextvars
from typing import Dict, Any

from abc import ABC, abstractmethod


class ExternalContext(ABC):

    @abstractmethod
    def define(self, data: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def get(self, key: str, *, default: Any | None = None):
        pass

    @abstractmethod
    def put(
        self,
        key: str,
        value: Any,
    ):
        pass

    def __setitem__(self, key, value):
        self.put(key, value)

    def __getitem__(self, item):
        return self.get(item, default=None)


class ImmutableExternalContext(ExternalContext):

    def __init__(self):
        self._context_var_store: Dict[str, contextvars.ContextVar] = {}

    def define(self, data: Dict[str, Any]) -> None:
        if len(self._context_var_store) > 0:
            raise RuntimeError(
                "Cannot submit new context to ImmutableExternalContext after its been created."
            )

        for key, value in data.items():
            context_var = contextvars.ContextVar(key)
            context_var.set(value)
            self._context_var_store[key] = context_var

    def get(self, key: str, *, default: Any | None = None):
        try:
            result = self._context_var_store[key].get()
            return result
        except LookupError:
            if default is not None:
                return default
            else:
                raise KeyError(f"Key '{key}' is not in context object.") from None

    def put(
        self,
        key: str,
        value: Any,
    ):
        raise ImmutableContextError(
            f"Cannot set values. This context is immutable."
        )


class ImmutableContextError(RuntimeError):
    """
    Raised when trying to modify an ImmutableExternalContext.
    """

    pass
