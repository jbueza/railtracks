import string
import yaml
from ..context import get
from ..llm import MessageHistory


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
    for message in message_history:
        if message.role == "system":
            continue
        if message.content is None:
            continue
        if isinstance(message.content, str):
            message.content = fill_prompt(message.content)
        elif isinstance(message.content, dict):
            message_history[i].content = yaml.safe_dump(
                fill_prompt(yaml.safe_dump(message.content))
            )
        else:
            raise TypeError(
                f"Unsupported content type: {type(message.content)}. Expected str or dict."
            )
