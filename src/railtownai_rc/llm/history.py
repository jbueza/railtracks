from typing import List, TypeVar

from .message import Message


class MessageHistory(List[Message]):

    def __str__(self):
        return "\n".join([str(message) for message in self])
