import pytest
import requestcompletion as rc
from requestcompletion.llm import AssistantMessage, ToolMessage, ToolResponse, ModelBase
from requestcompletion.llm.response import Response
from pydantic import BaseModel, Field

# ============ Model ===========
@pytest.fixture
def model():
    class DummyModel(ModelBase):
        def __init__(self):
            self.message = "dummy content"

        def chat(self, messages):
            return Response(message=AssistantMessage(self.message))
        
        def structured(self, messages, schema):
            return Response(message=AssistantMessage(schema(text="dummy content", number=42)))
        
        def chat_with_tools(self, messages, tools):
            if len(messages) > 0 and isinstance(messages[-1], ToolMessage) and messages[-1].content.name == "last tool call":
                return Response(message=AssistantMessage("Final answer after tool calls exhausted."))  # mock model expects the tool call name
            return Response(message=AssistantMessage([ToolMessage(ToolResponse(result=self.message, identifier="test", name="test"))]))
        
        # ============ Not being used yet ===========
        def stream_chat(self, messages):
            return Response(message=None, streamer=lambda: "dummy content")
        # ============ Not being used yet ===========
    return DummyModel

# ============ Tools ===========
@pytest.fixture
def mock_tool():
    @rc.to_node
    def magic_number() -> int:
        return 42
    
    return magic_number

# ============ Output Models ===========
@pytest.fixture
def output_model():
    class OutputModel(BaseModel):
        value: int = Field(description="A value to extract")
    return OutputModel