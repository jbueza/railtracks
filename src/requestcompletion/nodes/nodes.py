from __future__ import annotations

import asyncio
import uuid
import warnings
from copy import deepcopy

from ..llm import Tool

from abc import ABC, abstractmethod, ABCMeta
import inspect

from typing import (
    TypeVar,
    Generic,
    Type,
    List,
    Dict,
    Callable,
    ParamSpec,
    Any,
    Coroutine,
)

from typing_extensions import Self


_TOutput = TypeVar("_TOutput")


_TNode = TypeVar("_TNode", bound="Node")
_P = ParamSpec("_P")


class EnsureInvokeCoroutineMeta(ABCMeta):
    def __init__(cls, name, bases, dct):
        super().__init__(name, bases, dct)

        # now we need to make sure the invoke method is a coroutine, if not we should automatically switch it here.
        method_name = "invoke"
        if method_name in dct and callable(dct[method_name]):
            method = dct[method_name]
            if not inspect.iscoroutinefunction(method):

                # a simple async wrapper of the sequential method.
                async def async_wrapper(self, *args, **kwargs):
                    return await asyncio.to_thread(method(self, *args, **kwargs))

                setattr(cls, method_name, async_wrapper)


# TODO add generic for required context object
class Node(ABC, Generic[_TOutput], metaclass=EnsureInvokeCoroutineMeta):
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

    @abstractmethod
    async def invoke(self) -> Coroutine[Any, Any, _TOutput]:
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
        raise NotImplementedError("You must implement the tool_info method in your node")
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


class NodeException(Exception):
    """
    An internal exception designed to be thrown in the inside of a node. The many subtypes of this node are the one
    that should be thrown in the node.
    """

    def __init__(
        self,
        node: Node,
        detail: str,
    ):
        """Creates a new instance of an exception thrown inside a node

        Args:
            node (Node): The node that caused the error
            detail (str): A detailed message about the error
        """
        message = f"Error in {node.pretty_name()}, {detail}"

        self.node = node
        self.detail = detail

        super().__init__(message)


class CompletionException(NodeException, Generic[_TOutput]):

    def __init__(
        self,
        node: Node[_TOutput],
        detail: str,
        completion_protocol: _TOutput,
    ):
        """
        The lowest level of severity of an error encountered during a node.

        It is an error which has an accompanied value which should be treated as the completion of the node.

        Example:
                class APICall(Node):
                    ...
                    def invoke(self, data_streamer: DataStream):
                        ...
                        if response.status_code == 200:
                            return str(response.json())
                        else:
                            raise CompletionException(self, "API call failed", "Unable to collect any information")

        Args:
            node: The node that caused the error
            detail: A detailed message about the error
            completion_protocol: The value that should be treated as the completion of the node
        """
        self.completion_protocol = completion_protocol
        super().__init__(node, detail)


# Note in the below 2 exceptions we implement the __init__ method so we can provide explicit docstring for users to
#  interact with.
class FatalException(NodeException):
    def __init__(self, node, detail):
        """
        The highest level of severity of an error encountered during a node. When this error is thrown, the entire
        execution of the graph will end.

        Args:
            node: The node that caused the error
            detail: A detailed description of the error.
        """

        super().__init__(node, detail)


class ResetException(NodeException):
    def __init__(self, node, detail):
        """
        The middle level of a severity of an error encountered during a node. When this error is thrown, the parent that
        called this node into action will reset and try again. This approach is called "ScorchedEarth".

        This exception is designed to be thrown when errors happen that were unexpected but do not indicate a fatal
        error in the system.

        Args:
            node: The node that caused the error
            detail: A detailed description of the error.
        """
        super().__init__(node, detail)
