from typing import Callable, Set, Type, Tuple, List, Dict, Any

import requestcompletion as rc


def create_top_level_node(test_function: Callable, model_provider: str = "openai"):
    """
    Creates a top-level node for testing function nodes.

    Args:
        test_function: The function to test.
        usr_prompt: The user prompt to use for testing.

    Returns:
        A ToolCallLLM node that can be used to test the function.
    """

    class TopLevelNode(rc.library.ToolCallLLM):
        def __init__(self, message_history: rc.llm.MessageHistory):
            message_history.insert(0, rc.llm.SystemMessage(self.system_message()))

            super().__init__(
                message_history=message_history,
                model=self.create_model(),
            )

        @classmethod
        def system_message(cls) -> str:
            return "You are a helpful assistant that can call the tools available to you to answer user queries"

        @classmethod
        def create_model(cls):
            if model_provider == "openai":
                return rc.llm.OpenAILLM("gpt-4o")
            elif model_provider == "anthropic":
                return rc.llm.AnthropicLLM("claude-3-5-sonnet-20241022")
            else:
                raise ValueError(f"Invalid model provider: {model_provider}")

        @classmethod
        def connected_nodes(cls):
            return {rc.library.from_function(test_function)}

        @classmethod
        def pretty_name(cls) -> str:
            return "Top Level Node"

    return TopLevelNode
