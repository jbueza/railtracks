from typing import List, Callable, Optional, Type
from pydantic import BaseModel
from typing_extensions import Self


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

    def __str__(self):
        return f"Parameter(name={self._name}, type={self._param_type}, description={self._description}, required={self._required})"


class Tool:
    """
    A quasi immutable class designed to represent a single Tool object. This tool should be inserted into a model
    to allow the model to call the tool during generation.

    You pass in the key details in terms of the name, a short description, and a base model representing the parameters
    the model requires.
    """

    def __init__(self, name: str, detail: str, parameters: Optional[Type[BaseModel]] = None):
        """
        Creates a new instance of a tool object.

        Args:
            name: The name of the tool.
            detail: A detailed description of the tool.
            parameters: The parameters attached to this tool. If none, then there is no parameters for this model.
        """
        self._name = name
        self._detail = detail
        self._parameters = parameters

    @property
    def name(self):
        return self._name

    @property
    def detail(self):
        """
        Returns the string message attached to the detail of this tool
        """
        return self._detail

    @property
    def parameters(self):
        """
        Gets the parameters attached to this tool. If there are no parameters, this will return None.
        """
        return self._parameters

    def __str__(self):
        return f"Tool(name={self._name}, detail={self._detail}, parameters={self._parameters.model_json_schema()})"

    @classmethod
    def from_function(cls, function: Callable) -> Self:
        # TODO: complete the specialized logic. See github issue.
        pass

    # TODO: add a method to convert a node into a tool.
