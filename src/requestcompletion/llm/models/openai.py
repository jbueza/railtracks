from ._litellm_wrapper import LiteLLMWrapper

class OpenAILLM(LiteLLMWrapper):
    @classmethod
    def model_type(cls) -> str:
        return "OpenAI"