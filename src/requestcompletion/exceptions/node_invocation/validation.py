# from .exception_messages import get_message, get_notes
from ..execution import NodeInvocationError
from ...llm import Message, MessageHistory, ModelBase
import warnings

def check_message_history(message_history: MessageHistory) -> None:
    if any(not isinstance(m, Message) for m in message_history):
        raise NodeInvocationError(
            message="Message history must be a list of Message objects",
            notes=[
                "System messages must be of type rc.llm.SystemMessage (not string)",
                "User messages must be of type rc.llm.UserMessage (not string)",
            ],
            fatal=True
        )
    elif len(message_history) == 0:
        raise NodeInvocationError(
            message="Message history must contain at least one message",
            notes=["Please provide an initial message"],
            fatal=True
        )
    elif message_history[0].role != "system":
        raise NodeInvocationError(
            message="Missing SystemMessage: The first message in the message history must be a system message",
            fatal=True
        )
    elif len(message_history) == 1:
        warnings.warn("Only SystemMessage was provided. This is not recommended. Please provide at least one UserMessage.")


def check_model(model: ModelBase):
    if model is None:
        raise NodeInvocationError(
            message="You must provide a moddel to this node.",
            notes=["You can provide the model during the time of node creation using easy_usage_wrappers. \nEg:\n_ = rc.library.terminal_llm(..., model=rc.llm.OpenAILLM('gpt-4o'))",
                    "You can insert the model during the time of node invocation using the 'model' parameter. \nEg:\n_ = rc.call(node, model=rc.llm.OpenAILLM('gpt-4o'))"],
            fatal=True
        )
