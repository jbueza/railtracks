import string
import yaml
from requestcompletion.context import get


def inject_context(prompt: str) -> str:
    class ContextDict(dict):
        def __getitem__(self, key):
            return get(key)

        def __missing__(self, key):
            return f"{{{key}}} (missing from context)"  # Return the placeholder if not found

    return string.Formatter().vformat(prompt, (), ContextDict())
