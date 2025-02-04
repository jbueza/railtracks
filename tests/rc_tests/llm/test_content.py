import uuid

from pydantic import BaseModel
from railtownai_rc.llm import ToolResponse, ToolCall
from railtownai_rc.llm.content import stringify_content


def test_tool_call_str():
    tool_call = ToolCall(
        identifier=str(uuid.uuid4()),
        name="test",
        arguments={},
    )

    assert str(tool_call) == "test({})"


def test_tool_call_str_with_arguments():
    tool_call = ToolCall(
        identifier=str(uuid.uuid4()),
        name="test",
        arguments={"arg1": 1, "arg2": "2"},
    )

    assert str(tool_call) == "test({'arg1': 1, 'arg2': '2'})"


def test_tool_response_str():
    tool_response = ToolResponse(
        identifier=str(uuid.uuid4()),
        name="test",
        result="result",
    )

    assert str(tool_response) == "test -> result"


def test_stringify_content_str():
    assert stringify_content("test") == "test"


def test_stringify_content_tool_response():
    tool_response = ToolResponse(
        identifier=str(uuid.uuid4()),
        name="test",
        result="result",
    )

    assert stringify_content(tool_response) == "test -> result"


def test_stringify_content_tool_call():
    tool_call = [
        ToolCall(
            identifier=str(uuid.uuid4()),
            name="test",
            arguments={},
        )
    ]

    assert stringify_content(tool_call) == "test({})"


def test_stringify_content_base_model():
    class TestModel(BaseModel):
        name: str

    test_model = TestModel(name="test")

    assert stringify_content(test_model) == '{"name":"test"}'
