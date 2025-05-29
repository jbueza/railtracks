import pytest
from src.requestcompletion.llm.models._litellm_wrapper import (
    _parameters_to_json_schema,
    _to_litellm_tool,
    _to_litellm_message,
)
from src.requestcompletion.llm.message import AssistantMessage
from src.requestcompletion.llm.content import ToolCall
from src.requestcompletion.llm.tools import Tool, Parameter
from pydantic import BaseModel


# =================================== START _parameters_to_json_schema Tests ==================================
def test_parameters_to_json_schema_with_dict():
    """
    Test _parameters_to_json_schema with a dictionary input.
    """
    parameters = {
        "properties": {
            "param1": {"type": "string", "description": "A string parameter."},
            "param2": {"type": "integer", "description": "An integer parameter."},
        },
    }
    schema = _parameters_to_json_schema(parameters)
    assert schema == parameters


def test_parameters_to_json_schema_with_pydantic_model():
    """
    Test _parameters_to_json_schema with a Pydantic model input.
    """
    class ExampleModel(BaseModel):
        param1: str
        param2: int

    schema = _parameters_to_json_schema(ExampleModel)
    assert schema["type"] == "object"
    assert "properties" in schema
    assert "param1" in schema["properties"]
    assert "param2" in schema["properties"]

def test_parameters_to_json_schema_with_parameters_set(tool_with_parameters_set):
    """
    Test _parameters_to_json_schema with a set of Parameter objects.
    """
    schema = _parameters_to_json_schema(tool_with_parameters_set.parameters)
    assert schema["type"] == "object"
    assert "properties" in schema
    assert "param1" in schema["properties"]
    assert schema["properties"]["param1"]["type"] == "string"
    assert schema["properties"]["param1"]["description"] == "A string parameter."
    assert "required" in schema
    assert "param1" in schema["required"]

def test_parameters_to_json_schema_with_parameters_set(tool_with_parameters_basemodel):
    """
    Test _parameters_to_json_schema with a set of Parameter objects.
    """
    schema = _parameters_to_json_schema(tool_with_parameters_basemodel.parameters)
    assert schema["type"] == "object"
    assert "properties" in schema
    assert "param1" in schema["properties"]
    assert schema["properties"]["param1"]["type"] == "string"
    assert schema["properties"]["param1"]["description"] == "A string parameter."
    assert "required" in schema
    assert "param1" in schema["required"]

def test_parameters_to_json_schema_with_parameters_dictionary(tool_with_parameters_dictionary):
    """
    Test _parameters_to_json_schema with a dictionary of Parameter objects.
    """
    schema = _parameters_to_json_schema(tool_with_parameters_dictionary.parameters)
    assert schema["type"] == "object"
    assert "properties" in schema
    assert "param1" in schema["properties"]
    assert schema["properties"]["param1"]["type"] == "string"
    assert schema["properties"]["param1"]["description"] == "A string parameter."
    assert "required" in schema
    assert "param1" in schema["required"]
    assert "additionalProperties" in schema
    assert schema["additionalProperties"] is False

def test_parameters_to_json_schema_invalid_input():
    """
    Test _parameters_to_json_schema with invalid input.
    """
    with pytest.raises(TypeError):
        _parameters_to_json_schema(123)
# =================================== END _parameters_to_json_schema Tests ====================================


# =================================== START _to_litellm_tool Tests ==================================
def test_to_litellm_tool(tool):
    """
    Test _to_litellm_tool with a valid Tool instance.
    """
    litellm_tool = _to_litellm_tool(tool)
    assert litellm_tool["type"] == "function"
    assert "function" in litellm_tool
    assert litellm_tool["function"]["name"] == "example_tool"
    assert litellm_tool["function"]["description"] == "This is an example tool."
    assert "parameters" in litellm_tool["function"]
# =================================== END _to_litellm_tool Tests ====================================


# =================================== START _to_litellm_message Tests ==================================
def test_to_litellm_message_user_message(user_message):
    """
    Test _to_litellm_message with a UserMessage instance.
    """
    litellm_message = _to_litellm_message(user_message)
    assert litellm_message["role"] == "user"
    assert litellm_message["content"] == "This is a user message."


def test_to_litellm_message_assistant_message(assistant_message):
    """
    Test _to_litellm_message with an AssistantMessage instance.
    """
    litellm_message = _to_litellm_message(assistant_message)
    assert litellm_message["role"] == "assistant"
    assert litellm_message["content"] == "This is an assistant message."


def test_to_litellm_message_tool_message(tool_message):
    """
    Test _to_litellm_message with a ToolMessage instance.
    """
    litellm_message = _to_litellm_message(tool_message)
    assert litellm_message["role"] == "tool"
    assert litellm_message["name"] == "example_tool"
    assert litellm_message["tool_call_id"] == "123"
    assert litellm_message["content"] == "success"


def test_to_litellm_message_tool_call_list(tool_call):
    """
    Test _to_litellm_message with a list of ToolCall instances.
    """
    tool_calls = [tool_call]
    message = AssistantMessage(content=tool_calls)
    litellm_message = _to_litellm_message(message)
    assert litellm_message.role == "assistant"
    assert len(litellm_message.tool_calls) == 1
    assert litellm_message.tool_calls[0].function.name == "example_tool"
# =================================== END _to_litellm_message Tests ====================================