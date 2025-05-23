from abc import ABC, abstractmethod
from typing import Union, Callable

from .messages import RequestCreation, RequestSuccess, RequestCompletionMessage


class RCPublisher(ABC):
    """An abstract base class that defines the interface for a publisher and subscriber to interact with messages in the RC system."""

    @abstractmethod
    def start(self, runner_id: str):
        pass

    @abstractmethod
    def shutdown(self, runner_id: str, force: bool = False):
        """Release the resources held by that runner id"""
        pass

    @abstractmethod
    def publish(self, runner_id: str, message: RequestCompletionMessage):
        """Publish a message"""
        pass

    @abstractmethod
    def subscribe(self, runner_id: str, callback: Callable[[RequestCompletionMessage], None]):
        """Subscribe to messages"""
        pass

    @abstractmethod
    async def wait_for(self, runner_id: str, condition: Callable[[MessageType], bool]):
        pass
