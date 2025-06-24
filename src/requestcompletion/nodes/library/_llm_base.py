from __future__ import annotations
from abc import ABC
from copy import deepcopy

from typing_extensions import Self

from requestcompletion.exceptions.node_invocation.validation import check_message_history
from requestcompletion.nodes.nodes import Node, DebugDetails
import requestcompletion.llm as llm
from requestcompletion.llm.response import Response
from typing import List, TypeVar, Generic


_T = TypeVar("_T")

class RequestDetails:
    """
    A named tuple to store details of each LLM request.
    """
    def __init__(
            self,
            message_input: llm.MessageHistory,
            output: llm.Message,
            model_name: str | None,
            model_provider: str | None,
    ):
        self.input = message_input
        self.output = output
        self.model_name = model_name
        self.model_provider = model_provider

    def __repr__(self):
        return f"RequestDetails(model_name={self.model_name}, model_provider={self.model_provider}, input={self.input}, output={self.output})"


class LLMBase(Node[_T], ABC, Generic[_T]):

    def __init__(self, model: llm.ModelBase, message_history: llm.MessageHistory):
        super().__init__()
        self.model = model
        check_message_history(
            message_history
        )  # raises NodeInvocationError if any of the checks fail
        self.message_hist = deepcopy(message_history)

        self._details["llm_details"] = []

        self.attach_llm_hooks()

    def attach_llm_hooks(self):
        """Attach pre and post hooks to the model."""
        self.model.add_pre_hook(self.pre_llm_hook)
        self.model.add_post_hook(self.post_llm_hook)

    def detach_llm_hooks(self):
        """Detach pre and post hooks from the model."""
        self.model.remove_pre_hooks()
        self.model.remove_post_hooks()

    def pre_llm_hook(self, message_history: llm.MessageHistory) -> llm.MessageHistory:
        """Hook to modify messages before sending them to the model."""
        # TODO @levi
        return message_history

    def post_llm_hook(self, message_history: llm.MessageHistory, response: Response):
        self._details["llm_details"].append(
            RequestDetails(
                message_input=deepcopy(message_history),
                output=deepcopy(response.message),
                model_name=self.model.model_name(),
                model_provider=self.model.model_type(),
            )
        )

        return response

    def safe_copy(self) -> Self:
        new_instance: LLMBase = super().safe_copy() # noqa: Type checking broken.

        # This has got to be one of the weirdest things I've seen working with python
        # basically if we don't reattach the hooks, the `self` inserted into the model hooks will be the old memory address
        # so those updates will go to the old instance instead of the new one.
        new_instance.detach_llm_hooks()
        new_instance.attach_llm_hooks()
        # now that we have reattached the correct memory address to the llm the hooks will update properly.

        return new_instance

