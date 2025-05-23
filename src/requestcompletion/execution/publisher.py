import asyncio
import multiprocessing

from .publisher_base import RCPublisher, MessageType

from typing import List, Callable, Dict


class Publisher(RCPublisher):

    def __init__(self):
        self._message_queue: Dict[str, multiprocessing.Queue[MessageType]] = {}
        self.queue_lock

    def start(self, runner_id: str):
        pass

    def shutdown(self, runner_id: str, force: bool = False):
        pass

    def publish(self, runner_id: str, message: MessageType):
        pass

    def subscribe(self, runner_id: str, callback: Callable[[MessageType], None]):
        pass

    async def wait_for(self, runner_id: str, condition: Callable[[MessageType], bool]) -> MessageType:
        pass
