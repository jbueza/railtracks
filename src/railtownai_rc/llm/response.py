from .message import Message
from typing import Generator


class Response:

    def __init__(self, message: Message | None = None, streamer: Generator[str, None, None] | None = None):
        """
        Creates a new instance of a response object.

        Args:
            message: The message that was returned as part of this.
            streamer: A generator that streams the response as a collection of chunked strings.
        """
        self._message = message
        self._streamer = streamer

    @property
    def message(self):
        return self._message

    @property
    def streamer(self):
        return self._streamer

    def __str__(self):
        if self._message is not None:
            return str(self._message)
        else:
            return "Response(<no-data>)"

    def __repr__(self):
        return f"Response(message={self._message}, streamer={self._streamer})"
