from __future__ import annotations

import asyncio
import uuid
from copy import deepcopy

from ..llm import Tool
from abc import ABC, abstractmethod, ABCMeta

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

        # Check if the class methods are all classmethods, else raise an exception
        class_method_checklist = ["tool_info", "prepare_tool", "pretty_name"]
        for method_name in class_method_checklist:
            if method_name in dct and callable(dct[method_name]):
                method = dct[method_name]
                if not isinstance(method, classmethod):
                    from ..exceptions import RCNodeCreationException
                    raise RCNodeCreationException(
                        message=f"The '{method_name}' method must be a @classmethod.",
                        notes=[
                            f"Add @classmethod decorator to '{method_name}'.",
                            f"Signature should be: \n@classmethod\ndef {method_name}(cls): ..."
                        ]
                    )
        # special case for output_model structured_output node
        if 'output_model' in dct:
            method = dct['output_model']
            if not isinstance(method, classmethod):
                from ..exceptions import RCNodeCreationException
                raise RCNodeCreationException(
                    message="The 'output_model' method must be a @classmethod.",
                    notes=[
                        "Add @classmethod decorator to 'output_model'.",
                        "Signature should be: \n@classmethod\ndef 'output_model'(cls): ..."
                    ]
                )
            # # Additional check: output_model must return a pydantic model class
            # output_model = method.__func__(cls)
            # from pydantic import BaseModel
            # if not (isinstance(output_model, type) and issubclass(output_model, BaseModel)):
            #     from ..exceptions import RCNodeCreationException
            #     raise RCNodeCreationException(
            #             message="Output model cannot be empty/must be a pydantic model",
            #             notes=[
            #                 "The output_model classmethod must return a pydantic BaseModel subclass."
            #             ]
            #         )


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
