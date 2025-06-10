from .provider_wrapper import ProviderLLMWrapper


class OpenAILLM(ProviderLLMWrapper):
    @classmethod
    def model_type(cls) -> str:
        return "OpenAI"
