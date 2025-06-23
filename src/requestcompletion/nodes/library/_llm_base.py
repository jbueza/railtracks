from abc import ABC
from copy import deepcopy

from requestcompletion.exceptions.node_invocation.validation import check_message_history
from requestcompletion.nodes.nodes import Node, DebugDetails
import requestcompletion.llm as llm
from typing import NamedTuple, List, TypeVar, Generic

_T = TypeVar("_T")


RequestDetails = NamedTuple(
    "RequestDetails",
    [
        ("message_history", llm.MessageHistory),
        ("output", llm.Message),
        ("model_name", str),
        ("model_provider", str),

],
)
class LLMDebug(DebugDetails):
    def __init__(
            self,
            message_details: List[RequestDetails] = None,

    ):
        super().__init__()
        # This is done to prevent mutability concerns of an empty list default.
        if message_details is None:
            message_details = []

        self.message_details: List[RequestDetails] = message_details

class LLMBase(ABC, Node[_T], Generic[_T]):

    def __init__(self, model: llm.ModelBase, message_history: llm.MessageHistory):
        super().__init__()
        self.model = model
        check_message_history(
            message_history
        )  # raises NodeInvocationError if any of the checks fail
        self.message_hist = deepcopy(message_history)

    # TODO @levi insert prompt insertion here.