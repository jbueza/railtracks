import string
from ..context import get
from ..context.central import get_config
from ..llm import MessageHistory, Message


class KeyOnlyFormatter(string.Formatter):
    def get_value(self, key, args, kwargs):
        # Always treat key as a string and look up in kwargs (your context dict)
        return kwargs[str(key)]


def fill_prompt(prompt: str) -> str:
    class ContextDict(dict):
        def __getitem__(self, key):
            return get(key)

        def __missing__(self, key):
            return f"{{{key}}}"  # Return the placeholder if not found

    return KeyOnlyFormatter().vformat(prompt, (), ContextDict())


def inject_context(message_history: MessageHistory):
    """
    Injects the context from the current request into the prompt.

    Args:
        message_history (MessageHistory): The prompts to inject context into.

    """
    if get_config().prompt_injection:
        for i, message in enumerate(message_history):
            if message.inject_prompt and isinstance(message.content, str):
                message_history[i] = Message(
                    role=message.role.value, content=fill_prompt(message.content)
                )

    return message_history
