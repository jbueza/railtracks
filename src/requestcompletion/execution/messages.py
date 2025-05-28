from __future__ import annotations

import asyncio
from abc import ABC

from pydantic import BaseModel
from typing import Type, ParamSpec, Callable, Literal, TypeVar, TYPE_CHECKING, Generic

from ..nodes.nodes import Node, NodeState


# RC specific imports

ExecutionConfigurations = Literal["thread"]

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
        node_state: NodeState[Node[_TOutput]],
    ):

        self.request_id = request_id
        self.node_state = node_state

    @property
    def node(self) -> Node[_TOutput]:
        return self.node_state.instantiate()


class RequestSuccess(RequestFinishedBase):
    def __init__(self, *, request_id: str, node_state: NodeState[_TNode[_TOutput]], result: _TOutput):
        super().__init__(request_id=request_id, node_state=node_state)
        self.result = result


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


class RequestFailure(RequestFinishedBase):
    def __init__(
        self,
        *,
        request_id: str,
        node_state: NodeState[_TNode[_TOutput]],
        error: Exception,
    ):
        super().__init__(request_id=request_id, node_state=node_state)
        self.error = error


class FatalFailure(RequestCompletionMessage):
    def __init__(self, *, error: Exception):
        self.error = error


# TODO implement other message types
