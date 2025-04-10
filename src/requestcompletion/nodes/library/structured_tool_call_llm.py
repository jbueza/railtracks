from ._tool_call_llm_base import OutputLessToolCallLLM
from ...llm import MessageHistory, ModelBase
from pydantic import BaseModel
from abc import ABC


class StructuredToolCallLLM(OutputLessToolCallLLM[str], ABC):

    def __init__(self, 
                 message_history: MessageHistory, 
                 llm_model: ModelBase,
                 output_model: BaseModel):
        
        super().__init__(message_history, llm_model)
        self.output_model = output_model


    def return_output(self) -> BaseModel:   # TODO: strcuted llm call and checks for the output model
        """Returns the BaseModel to struture the output as a pydantic model"""
        return self.output_model
