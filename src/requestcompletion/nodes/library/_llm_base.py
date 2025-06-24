from abc import ABC
from copy import deepcopy


from requestcompletion.exceptions.node_invocation.validation import (
    check_message_history,
)
from requestcompletion.nodes.nodes import Node, DebugDetails
import requestcompletion.llm as llm
from requestcompletion.llm.response import Response
from typing import List, TypeVar, Generic

from ...prompts.prompt import inject_context

_T = TypeVar("_T")


class RequestDetails:
    """
    A named tuple to store details of each LLM request.
    """

    def __init__(
        self,
        message_input: llm.MessageHistory,
        output: llm.MessageHistory,
        model_name: str | None,
        model_provider: str | None,
    ):
        self.input = message_input
        self.output = output
        self.model_name = model_name
        self.model_provider = model_provider


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


class LLMBase(Node[_T], ABC, Generic[_T]):
    def __init__(self, model: llm.ModelBase, message_history: llm.MessageHistory):
        super().__init__()
        self.model = model
        check_message_history(
            message_history
        )  # raises NodeInvocationError if any of the checks fail
        self.message_hist = deepcopy(message_history)
        self._debug_details = LLMDebug()
        self.model.add_pre_hook(self.pre_llm_hook)
        self.model.add_post_hook(self.post_llm_hook)

    def pre_llm_hook(self, message_history: llm.MessageHistory) -> llm.MessageHistory:
        """Hook to modify messages before sending them to the model."""
        return inject_context(message_history)

    def post_llm_hook(self, message_history: llm.MessageHistory, response: Response):
        self._debug_details.message_details.append(
            RequestDetails(
                message_input=deepcopy(message_history),
                output=deepcopy(response.message),
                model_name=self.model.model_name,
                model_provider=self.model.model_provider,
            )
        )

        return response

    def debug_details(self):
        return self._debug_details
