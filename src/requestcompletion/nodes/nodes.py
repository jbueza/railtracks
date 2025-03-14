from __future__ import annotations
import uuid
import warnings
from copy import deepcopy

from ..llm import Tool, Parameter

from abc import ABC, abstractmethod
from functools import wraps

from typing import (
    TypeVar,
    Generic,
    Type,
    List,
    Dict,
    Callable,
    ParamSpec,
    Any,
)

from typing_extensions import Self


_TOutput = TypeVar("_TOutput")


# TODO think through if there is a better way to type this.
class NodeOutput(Generic[_TOutput]):
    # TODO: write docs
    @property
    def node_type(self) -> Type[Node]:
        return self._node_type

    @property
    def data(self) -> _TOutput:
        return self._data

    def __init__(
        self,
        node_type: Type[Node],
        data: _TOutput,
    ):
        self._node_type = node_type
        self._data = data


def check_flag(flag: bool, failure_message: str):
    def wrapper_decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if flag:
                return func(*args, **kwargs)
            else:
                warnings.warn(failure_message)

        return wrapper

    return wrapper_decorator


_TNode = TypeVar("_TNode", bound="Node")
_P = ParamSpec("_P")


# TODO add generic for required context object
class Node(ABC, Generic[_TOutput]):
    """An abstract base class which defines some the functionality of a node"""

    def __default_data_streamer(self, data: str):
        """
        A default data streamer designed to do nothing.
        """
        pass

    def __null_backend_connection(self, *args, **kwargs):
        """
        A placeholder method designed to throw an exception if it is ever called. It should prevent any node from accessing
        things like creating new nodes without some sort of connection to the state management system.
        """
        raise FatalException(
            self,
            "You cannot create nodes when a backend parameters have not been injected. Please use the `run` method instead.",
        )

    def __init__(
        self,
    ):
        # we need to set the default values for the methods. These methods are only used if some calls `invoke` without
        # injecting the backend details
        self.data_streamer: Callable[[str], None] = self.__default_data_streamer
        self._invoke_node: Callable[[Node, List[str]], List[NodeOutput]] = self.__null_backend_connection
        self._create_node: Callable[[Callable[_P, Node], _P.args, _P.kwargs], str] = self.__null_backend_connection

        # each fresh node will have a generated uuid that identifies it.
        self.uuid = str(uuid.uuid4())

    def inject(
        self,
        data_streamer: Callable[[str], None],
        create_node: Callable[[Callable[_P, Node], _P.args, _P.kwargs], str],
        invoke_node: Callable[[Node, List[str]], List[NodeOutput]],
    ):
        """
        Injects the given methods into the node. These will allow the node to properly connect to the rest of the system.
        """
        self.data_streamer = data_streamer
        self._invoke_node = invoke_node
        self._create_node = create_node

    def create(self, new_node: Callable[_P, Node] & Node, *args: _P.args, **kwargs: _P.kwargs):
        """
        Creates a node within the RC node framework with the provided arguments.

        Note that you must use this method to create a new node. If you try to create and call a node directly it will
        not use the rest of the system.

        Args:
            new_node: The node you would like to create.
            *args: The arguments to pass to the node.
            **kwargs: The keyword arguments to pass to the node

        Returns:
            An identifier for the node that was created.
        """
        return self._create_node(new_node, *args, **kwargs)

    def complete(self, request_id: List[str]) -> List[NodeOutput]:
        """
        Calls the provided nodes and returns the outputs.
        """
        return self._invoke_node(self, request_id)

    @classmethod
    @abstractmethod
    def pretty_name(cls) -> str:
        """
        Returns a pretty name for the node. This name is used to identify the node type of the system.
        """

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
            if k in ["data_streamer", "_invoke_node", "_create_node"]:
                # These do not need to be copied becuase they are not modifed by the node and are expensive to copy
                setattr(result, k, v)
                continue
            print(k, v)
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
