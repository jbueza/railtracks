from __future__ import annotations

import asyncio
from abc import ABC

from pydantic import BaseModel
from typing import Type, ParamSpec, Callable, Literal, TypeVar, TYPE_CHECKING, Generic

from ..nodes.nodes import Node, NodeState


# RC specific imports
if TYPE_CHECKING:
    from .publisher import ExecutionConfigurations

    _P = ParamSpec("_P")
    _TOutput = TypeVar("_TOutput")
    _TNode = TypeVar("_TNode", bound=Node)


class RequestCompletionMessage(ABC, BaseModel):
    pass


# TODO add generic typung for all these types
class RequestFinishedBase(RequestCompletionMessage, ABC):
    request_id: str
    node_state: NodeState[Node[_TOutput]]

    @property
    def node(self) -> Node[_TOutput]:
        return self.node_state.instantiate()


class RequestSuccess(RequestFinishedBase):
    result: _TOutput


class RequestCreation(RequestCompletionMessage):
    current_node_id: str | None
    new_request_id: str
    running_mode: "ExecutionConfigurations"
    new_node_type: Callable[_P, _TNode[_TOutput]]
    # TODO: check the typing of this
    args: _P.args
    kwargs: _P.kwargs


class RequestFailure(RequestFinishedBase):
    error: Exception


# TODO implement other message types
