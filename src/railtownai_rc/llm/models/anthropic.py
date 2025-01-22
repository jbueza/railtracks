from ._llama_index_wrapper import LlamaWrapper
from llama_index.core import Settings
from llama_index.llms.anthropic import Anthropic


class AnthropicLLM(LlamaWrapper):
    @classmethod
    def setup_model_object(cls, model_name: str, **kwargs):
        Settings.tokenizer = Anthropic().tokenizer
        return Anthropic(model_name, **kwargs)

    @classmethod
    def model_type(cls) -> str:
        return "Anthropic"
