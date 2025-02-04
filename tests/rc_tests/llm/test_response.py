import railtownai_rc.llm as llm
from railtownai_rc.llm.response import Response


def test_streamer():
    text_string = "hello world"

    def streamer_func():
        for character in text_string:
            yield character

        return

    r = Response(streamer=streamer_func())
    full_message = ""
    for c in r.streamer:
        full_message += c

    assert full_message == text_string

    assert str(r) == "Response(<no-data>)"
