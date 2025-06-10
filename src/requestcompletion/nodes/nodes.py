from __future__ import annotations
import asyncio
import uuid
from copy import deepcopy
from ..exceptions.fatal import RCNodeCreationException
from ..llm import Tool
from abc import ABC, abstractmethod, ABCMeta
from pydantic import BaseModel
from typing import (
    TypeVar,
    Generic,
    Dict,
    ParamSpec,
    Any,
)
from typing_extensions import Self

_TOutput = TypeVar("_TOutput")

_TNode = TypeVar("_TNode", bound="Node")
_P = ParamSpec("_P")


class NodeCreationMeta(ABCMeta):
    def __init__(cls, name, bases, dct):
        super().__init__(name, bases, dct)

        # now we need to make sure the invoke method is a coroutine, if not we should automatically switch it here.
        method_name = "invoke"
        if method_name in dct and callable(dct[method_name]):
            method = dct[method_name]

            # a simple wrapper to convert any async function to a non async one.
            async def async_wrapper(self, *args, **kwargs):
                if asyncio.iscoroutinefunction(method):
                    return await method(self, *args, **kwargs)

            setattr(cls, method_name, async_wrapper)

        # ================= Checks for Creation ================
        # 1. Check if the class methods are all classmethods, else raise an exception
        class_method_checklist = ["tool_info", "prepare_tool", "pretty_name"]
        for method_name in class_method_checklist:
            if method_name in dct and callable(dct[method_name]):
                method = dct[method_name]
                if not isinstance(method, classmethod):
                    raise RCNodeCreationException(
                        message=f"The '{method_name}' method must be a @classmethod.",
                        notes=[
                            f"Add @classmethod decorator to '{method_name}'.",
                            f"Signature should be: \n@classmethod\ndef {method_name}(cls): ...",
                        ],
                    )
        # 2. special case for output_model for structured_llm node
        if "output_model" in dct and not getattr(cls, "__abstractmethods__", False):
            method = dct["output_model"]
            if not isinstance(method, classmethod):
                raise RCNodeCreationException(
                    message="\nThe 'output_model' method must be a @classmethod.",
                    notes=[
                        "Add @classmethod decorator to 'output_model'.",
                        "Signature should be: \n@classmethod\ndef 'output_model'(cls): ...",
                    ],
                )
            output_model = method.__func__(cls)
            if not output_model:
                raise RCNodeCreationException(
                    message="Output model is not provided.",
                    notes=[
                        "Check to see if the output_model is a pydantic model.",
                        "Output model cannot be empty.",
                        "The model fields must be defined in the output_model. Eg.-\n class MyModel(BaseModel): \n    field1: str = Field(description='field1 description')"
                    ]
                )
            elif not issubclass(output_model, BaseModel):
                raise RCNodeCreationException(
                    message=f"Output model must be a pydantic model, not {type(output_model)}.",
                    notes=[
                        "Check to see if the output_model is a pydantic model.",
                        "The model fields must be defined in the output_model. Eg.-\n class MyModel(BaseModel): \n    field1: str = Field(description='field1 description')"
                    ]
                )
            elif len(output_model.model_fields) == 0:
                raise RCNodeCreationException(
                    message="Output model has no fields defined.",
                    notes=[
                        "Check to see if the BaseModel has any fields defined.",
                        "Output model cannot be empty.",
                        "The model fields must be defined in the output_model. Eg.-\n class MyModel(BaseModel): \n    field1: str = Field(description='field1 description')"
                    ]
                )

        # 3. Check if the connected_nodes is not empty, special case for ToolCallLLM
        if "connected_nodes" in dct and not getattr(cls, "__abstractmethods__", False):
            method = dct["connected_nodes"]
            try:  # in case of class based init
                node_set = method.__func__(cls)
            except AttributeError:  # in case of easy_wrapper init
                dummy = object.__new__(cls)
                node_set = method(dummy)
            if not node_set:
                raise RCNodeCreationException(
                    message="connected_nodes must not return an empty set.",
                    notes=[
                        "Please provide a set nodes that can be used as tools by the ToolCallLLM node."
                    ],
                )
            elif not all(issubclass(x, Node) for x in node_set):
                raise RCNodeCreationException(
                    message="connected_nodes must return a set of Nodes.",
                    notes=[
                        "Ensure all the nodes provided as connected_nodes are of type Node.",
                        "If you have functions that you want to use as tools, please use the from_function method to convert them to Nodes.",
                    ],
                )
        # ================= End Creation Exceptions ================


class NodeState(Generic[_TNode]):
    """
    A stripped down representation of a Node which can be passed along the process barrier.
    """

    # This object should json serializable such that it can be passed across the process barrier
    # TODO come up with a more intelligent way to recreate the node
    def __init__(
        self,
        node: _TNode,
    ):
        self.node = node

    def instantiate(self) -> _TNode:
        """
        Creates a pass by reference copy of the node in the state.
        """
        return self.node


class Node(ABC, Generic[_TOutput], metaclass=NodeCreationMeta):
    """An abstract base class which defines some the functionality of a node"""

    def __init__(
        self,
    ):
        # each fresh node will have a generated uuid that identifies it.
        self.uuid = str(uuid.uuid4())

    @classmethod
    @abstractmethod
    def pretty_name(cls) -> str:
        """
        Returns a pretty name for the node. This name is used to identify the node type of the system.
        """
        pass

    @abstractmethod
    async def invoke(self) -> _TOutput:
        """
        The main method that runs when this node is called
        """
        pass

    def state_details(self) -> Dict[str, str]:
        """
        Places the __dict__ of the current object into a dictionary of strings.
        """
        di = {k: str(v) for k, v in self.__dict__.items()}
        return di

    @classmethod
    def tool_info(cls) -> Tool:
        """
        A method used to provide information about the node in the form of a tool definition.
        This is commonly used with LLMs Tool Calling tooling.
        """
        # TODO: finish implementing this method
        raise NotImplementedError(
            "You must implement the tool_info method in your node"
        )
        # detail = inspect.getdoc(cls)
        # if detail is None:
        #     warnings.warn(f"Node {cls.__name__} does not have a docstring. Using empty string instead.")
        #     detail = ""
        #
        # params = inspect.signature(cls.__init__).parameters
        #
        # tool = Tool(
        #     name=cls.pretty_name(),
        #     detail=detail,
        #     parameters=set(
        #         [
        #             Parameter(name=k, description=v.annotation, param_type="string")
        #             for k, v in params.items()
        #             if k != "self"
        #         ]
        #     ),
        # )

    @classmethod
    def prepare_tool(cls, tool_parameters: Dict[str, Any]) -> Self:
        """
        This method creates a new instance of the node by unpacking the tool parameters.

        If you would like any custom behavior please override this method.
        """
        return cls(**tool_parameters)  # noqa

    def safe_copy(self) -> Self:
        """
        A method used to create a new pass by value copy of every element of the node except for the backend connections.

        The backend connections include the data streamer, create_node_hook and invoke_node_hook.

        """
        cls = self.__class__
        result = cls.__new__(cls)
        for k, v in self.__dict__.items():
            setattr(result, k, deepcopy(v))
        return result

    def __repr__(self):
        return f"{self.pretty_name()}: {self.state_details()}"
