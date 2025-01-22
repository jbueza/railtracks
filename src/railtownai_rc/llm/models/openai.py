from ._llama_index_wrapper import LlamaWrapper
from llama_index.llms.openai import OpenAI


class OpenAILLM(LlamaWrapper):
    @classmethod
    def setup_model_object(cls, model_name: str, **kwargs):
        return OpenAI(model_name, **kwargs)

    @classmethod
    def model_type(cls) -> str:
        return "OpenAI"
