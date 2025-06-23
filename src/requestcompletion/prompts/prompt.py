import string
import yaml
from ..context import get
from ..llm import MessageHistory, Message


def fill_prompt(prompt: str) -> str:
    class ContextDict(dict):
        def __getitem__(self, key):
            return get(key)

        def __missing__(self, key):
            return f"{{{key}}} (missing from context)"  # Return the placeholder if not found

    return string.Formatter().vformat(prompt, (), ContextDict())


def inject_context(message_history: MessageHistory) -> MessageHistory:
    """
    Injects the context from the current request into the prompt.

    Args:
        message_history (str): The prompt to inject context into.

    Returns:
        str: The prompt with the context injected.
    """
    for i, message in enumerate(message_history):
        if isinstance(message.content, str):
            message_history[i] = Message(
                role=message.role.value,
                content=fill_prompt(message.content)
            )

    return message_history
