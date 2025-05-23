import asyncio
from abc import ABC

from pydantic import BaseModel
from typing import Type, ParamSpec, Callable, Literal, TypeVar, TYPE_CHECKING, Generic

# RC specific imports
if TYPE_CHECKING:
    from ..nodes.nodes import Node, NodeState
    from .coordinator import Coordinator

    _P = ParamSpec("_P")
    _TOutput = TypeVar("_TOutput")
    _TNode = TypeVar("_TNode", bound=Node)


class RequestCompletionMessage(ABC, BaseModel):
    listener


# TODO add generic typung for all these types
class _RequestFinishedBase(ABC, RequestCompletionMessage):
    request_id: str
    node_state: NodeState[Node[_TOutput]]

    @property
    def node(self) -> Node[_TOutput]:
        return self.node_state.instantiate()


class RequestSuccess(_RequestFinishedBase):
    result: _TOutput


class RequestCreation(RequestCompletionMessage):
    current_node_id: str
    new_request_id: str
    running_mode: Coordinator.RunningMode
    new_node_type: Callable[_P, _TNode[_TOutput]]
    # TODO: check the typing of this
    args: _P.args
    kwargs: _P.kwargs


class RequestFailure(_RequestFinishedBase):
    error: Exception


# TODO implement other message types
