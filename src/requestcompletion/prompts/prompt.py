import string
import yaml
from requestcompletion.context import get


def format_message_with_context(template: str) -> str:
    class ContextDict(dict):
        def __getitem__(self, key):
            return get(key)

        def __missing__(self, key):
            return f"{{{key}}} (missing from context)"  # Return the placeholder if not found

    return string.Formatter().vformat(template, (), ContextDict())


def load_prompts(path="prompts.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)


class PromptManager:
    def __init__(self, path="prompts.yaml"):
        self.prompts = load_prompts(path)

    def get(self, name, **kwargs):
        template = self.prompts[name]
        return template.format(**kwargs)

    def list_prompts(self):
        return list(self.prompts.keys())

    def get_prompt_placeholders(self, name):
        template = self.prompts[name]
        return [field_name for _, field_name, _, _ in string.Formatter().parse(template) if field_name]


class Prompt:
    def __init__(self, template: str, placeholders: dict = None):
        """
        :param template: The prompt template, e.g. "See the following text {prompt_text}"
        :param placeholders: Dict of placeholder configs, e.g. {"prompt_text": {"required": True, "default": None}}
        """
        self.template = template
        self.placeholders = placeholders or {}

    def format(self, context: dict) -> str:
        class ContextDict(dict):
            def __missing__(self, key):
                config = self.placeholders.get(key, {})
                if config.get("required", False):
                    raise KeyError(f"Missing required key '{key}' in context for prompt formatting.")
                return config.get("default", "")
        return self.template.format_map(ContextDict(context))

    def get_placeholders(self):
        import string
        return [field_name for _, field_name, _, _ in string.Formatter().parse(self.template) if field_name]
