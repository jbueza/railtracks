from ._tool_call_llm_base import OutputLessToolCallLLM
from ...llm import MessageHistory, ModelBase, SystemMessage, UserMessage
from .structured_llm import structured_llm
from ...interaction.call import call
from pydantic import BaseModel
from abc import ABC


class StructuredToolCallLLM(OutputLessToolCallLLM[str], ABC):

    def __init__(
        self,
        message_history: MessageHistory,
        llm_model: ModelBase,
        output_model: BaseModel,
    ):

        super().__init__(message_history, llm_model)
        system_structured = SystemMessage(
            "You are a structured LLM that can convert the response into a structured output."
        )
        self.structured_resp_node = structured_llm(output_model, system_message=system_structured, model=self.model)

    async def return_output(self) -> BaseModel:
        last_message = self.message_hist[-1]
        try:
            return await call(
                self.structured_resp_node, message_history=MessageHistory([UserMessage(last_message.content)])
            )
        except Exception as e:
            raise ValueError(f"Failed to parse assistant response into structured output: {e}")
