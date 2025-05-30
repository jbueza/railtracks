from __future__ import annotations

import asyncio
from abc import ABC

from pydantic import BaseModel
from typing import Type, ParamSpec, Callable, Literal, TypeVar, TYPE_CHECKING, Generic, Any

from ..nodes.nodes import Node, NodeState


# RC specific imports

ExecutionConfigurations = Literal["async"]

_P = ParamSpec("_P")
_TOutput = TypeVar("_TOutput")
_TNode = TypeVar("_TNode", bound=Node)


class RequestCompletionMessage(ABC):
    pass


# TODO add generic typing for all these types
class RequestFinishedBase(RequestCompletionMessage, ABC):
    def __init__(
        self,
        *,
        request_id: str,
        node_state: NodeState[Node[_TOutput]] | None,
    ):

        self.request_id = request_id
        self.node_state = node_state

    @property
    def node(self) -> Node[_TOutput] | None:
        if self.node_state is None:
            return None

        return self.node_state.instantiate()

    def __repr__(self):
        return f"{self.__class__.__name__}(request_id={self.request_id}, node_state={self.node_state})"


class RequestSuccess(RequestFinishedBase):
    def __init__(self, *, request_id: str, node_state: NodeState[_TNode[_TOutput]], result: _TOutput):
        super().__init__(request_id=request_id, node_state=node_state)
        self.result = result

    def __repr__(self):
        return f"{self.__class__.__name__}(request_id={self.request_id}, node_state={self.node_state}, result={self.result})"


class RequestCreation(RequestCompletionMessage):
    def __init__(
        self,
        *,
        current_node_id: str | None,
        new_request_id: str,
        running_mode: ExecutionConfigurations,
        new_node_type: Type[_TNode[_TOutput]],
        args,
        kwargs,
    ):
        self.current_node_id = current_node_id
        self.new_request_id = new_request_id
        self.running_mode = running_mode
        self.new_node_type = new_node_type
        self.args = args
        self.kwargs = kwargs

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(current_node_id={self.current_node_id}, "
            f"new_request_id={self.new_request_id}, running_mode={self.running_mode}, "
            f"new_node_type={self.new_node_type.__name__}, args={self.args}, kwargs={self.kwargs})"
        )


class RequestFailure(RequestFinishedBase):
    def __init__(
        self,
        *,
        request_id: str,
        node_state: NodeState[_TNode[_TOutput]] | None,
        error: Exception,
    ):
        super().__init__(request_id=request_id, node_state=node_state)
        self.error = error

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(request_id={self.request_id}, "
            f"node_state={self.node_state}, error={self.error})"
        )


class FatalFailure(RequestCompletionMessage):
    def __init__(self, *, error: Exception):
        self.error = error

    def __repr__(self):
        return f"{self.__class__.__name__}(error={self.error})"


class Streaming(RequestCompletionMessage):
    def __init__(self, *, streamed_object: Any, node_id: str):
        self.streamed_object = streamed_object
        self.node_id = node_id

    def __repr__(self):
        return f"{self.__class__.__name__}(streamed_object={self.streamed_object}, node_id={self.node_id})"
