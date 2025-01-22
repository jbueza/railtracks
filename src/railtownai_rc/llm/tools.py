from copy import deepcopy
from typing import List, Self, Callable


class Parameter:

    def __init__(self, name: str, param_type: str, description: str = "", required: bool = True):
        """
        Creates a new instance of a parameter object.

        Args:
            name: The name of the parameter.
            param_type: The type of the parameter.
            description: A description of the parameter.
            required: Whether the parameter is required. Defaults to True.
        """
        self._name = name
        self._param_type = param_type
        self._description = description
        self._required = required

    @property
    def name(self):
        return self._name

    @property
    def param_type(self):
        return self._param_type

    @property
    def description(self):
        return self._description

    @property
    def required(self):
        return self._required


class Tool:

    def __init__(self, name: str, detail: str = "", parameters: List[Parameter] = None):
        """
        Creates a new instance of a tool object.

        Args:
            name: The name of the tool.
            detail: A detailed description of the tool.
            parameters: The parameters attached to this tool.
        """
        self._name = name
        self._detail = detail
        self._parameters = parameters or []

    @property
    def name(self):
        return self._name

    @property
    def detail(self):
        return self._detail

    @property
    def parameters(self):
        # pass by value of the list entries.
        return [x for x in self._parameters]

    @classmethod
    def from_function(cls, function: Callable) -> Self:
        # TODO: complete the specialized logic.
        pass
