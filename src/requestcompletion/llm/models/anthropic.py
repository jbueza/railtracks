from ._litellm_wrapper import LiteLLMWrapper

class AnthropicLLM(LiteLLMWrapper):
    @classmethod
    def model_type(cls) -> str:
        return "Anthropic"
