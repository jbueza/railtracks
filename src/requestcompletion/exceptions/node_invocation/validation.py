# from .exception_messages import get_message, get_notes
from ..execution import NodeInvocationError
from ...llm import Message, MessageHistory


def check_message_history(message_history: MessageHistory) -> None:
    if any(not isinstance(m, Message) for m in message_history):
        raise NodeInvocationError(
            message="Message history must be a list of Message objects",
            notes=[
                "System messages must be of type rc.llm.SystemMessage (not string)",
                "User messages must be of type rc.llm.UserMessage (not string)",
            ],
        )
    elif len(message_history) == 0:
        raise NodeInvocationError(
            message="Message history must contain at least one message",
            notes=["Please provide an initial message"],
        )
    elif message_history[0].role != "system":
        raise NodeInvocationError(
            message="Missing SystemMessage: The first message in the message history must be a system message"
        )
