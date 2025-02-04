import uuid

import railtownai_rc as rc


def test_message_hist_string():
    message_hist = rc.llm.MessageHistory([rc.llm.UserMessage("What is going on in this beautiful world?")])

    assert str(message_hist) == "user: What is going on in this beautiful world?"


def test_multiline_hist_string():
    message_hist = rc.llm.MessageHistory(
        [
            rc.llm.UserMessage("What is going on in this beautiful world?"),
            rc.llm.AssistantMessage("Nothing much as of now"),
        ]
    )

    assert str(message_hist) == "user: What is going on in this beautiful world?\nassistant: Nothing much as of now"


def test_tool_call_in_mess_hist():
    message_hist = rc.llm.MessageHistory(
        [
            rc.llm.UserMessage("What is the current weather?"),
            rc.llm.AssistantMessage(
                [
                    rc.llm.ToolCall(
                        identifier=str(uuid.uuid4()), name="weather_forecast", arguments={"location": "New York"}
                    )
                ]
            ),
        ]
    )

    assert (
        str(message_hist) == "user: What is the current weather?\nassistant: weather_forecast({'location': 'New York'})"
    )


def test_multiple_tool_calls_in_mess_hist():
    message_hist = rc.llm.MessageHistory(
        [
            rc.llm.UserMessage("What is the current weather in New York and Madrid?"),
            rc.llm.AssistantMessage(
                [
                    rc.llm.ToolCall(
                        identifier=str(uuid.uuid4()), name="weather_forecast", arguments={"location": "New York"}
                    ),
                    rc.llm.ToolCall(
                        identifier=str(uuid.uuid4()), name="weather_forecast", arguments={"location": "Madrid"}
                    ),
                ]
            ),
        ]
    )

    assert str(message_hist) == (
        "user: What is the current weather in New York and Madrid?\n"
        "assistant: weather_forecast({'location': 'New York'}), weather_forecast({'location': 'Madrid'})"
    )
