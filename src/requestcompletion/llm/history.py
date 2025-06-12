from typing import List

from .message import Message


class MessageHistory(List[Message]):
    def __str__(self):
        return "\n".join([str(message) for message in self])
