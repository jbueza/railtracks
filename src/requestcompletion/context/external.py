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
    """
    An immutable context that cannot be modified after it had been defined. You may only ask to `get` objects.
    """

    def __init__(self):
        self._context_var_store = {}

    def define(self, data: Dict[str, Any]) -> None:
        """
        Sets the values in the context. This will raise an error if the context has already been defined.

        Once set you cannot reset it.
        """
        if len(self._context_var_store) > 0:
            raise RuntimeError(
                "Cannot submit new context to ImmutableExternalContext after its been created."
            )

        for key, value in data.items():
            self._context_var_store[key] = value

    def get(self, key: str, *, default: Any | None = None):
        """
        Gets the value of the provided key from the context. If the key does not exist, it will return the default
        value if provided (and not None), otherwise it will raise a KeyError.
        """
        try:
            result = self._context_var_store[key]
            return result
        except KeyError:
            if default is not None:
                return default
            raise

    def put(
        self,
        key: str,
        value: Any,
    ):
        raise ImmutableContextError("Cannot set values. This context is immutable.")


class ImmutableContextError(RuntimeError):
    """
    Raised when trying to modify an ImmutableExternalContext.
    """

    pass
