from __future__ import annotations

import asyncio
import concurrent.futures
import contextvars
import multiprocessing
import threading
import queue
import uuid
import warnings
from logging.config import listen

from .messages import RequestCompletionMessage
from abc import ABC, abstractmethod

from typing import List, Callable, Dict, Literal, TypeVar, Generator, Generic, Coroutine, Awaitable


from ..utils.logging.create import get_rc_logger

_T = TypeVar("_T")
_TOutput = TypeVar("_TOutput")

logger = get_rc_logger(__name__)


class Subscriber(Generic[_T]):
    """A simple wrapper class of a callback function."""

    # this could be done without a class, but I want to keep as extendable as possible.
    def __init__(
        self,
        callback: Callable[[_T], None] | Callable[[_T], Coroutine[None, None, None]],
        name: str | None = None,
    ):
        self.callback = callback
        self.name = name if name is not None else callback.__name__
        self.id = str(uuid.uuid4())

    async def trigger(self, message: _T):
        """Trigger this subscriber with the given message."""
        try:
            result = self.callback(message)
            if asyncio.iscoroutine(result):
                await result
        except Exception as e:
            print(e)
            # logger.exception(f'Error while triggering "%s": %s', self.name, e)


class RCPublisher(Generic[_T]):
    """
    A simple publisher object with some basic functionality to publish and suvbscribe to messages.

    Note a couple of things:
    - Message will be handled in the order they came in (no jumping the line)
    - If you add a subscriber during the operation it will handle any new messages that come in after the subscription
        took place
    - Calling the shutdown method will kill the publisher forever. You will have to make a new one after.
    """

    # TODO check thread safety.
    timeout = 0.001

    def __init__(
        self,
    ):
        self._queue: asyncio.Queue[_T] = asyncio.Queue()
        self._subscribers: List[Subscriber[_T]] = []

        self._killed = True

        self.pub_loop = None

    async def __aenter__(self):
        """Enable the use of the publisher in a context manager."""
        await self.start()
        return self

    async def start(self):
        # you must set the kill variables first or the publisher loop will early exit.
        self._killed = False
        self.pub_loop = asyncio.create_task(self._published_data_loop(), name="Publisher Loop")

    async def __aexit__(self, exc_type, exc_value, traceback):
        """Shutdown the publisher when exiting the context manager."""
        await self.shutdown()

    async def publish(self, message: _T):
        """Publish a message the publisher. This will trigger all subscribers to receive the message.

        Args:
            message: The message you would like to publish.

        """
        if self._killed:
            raise RuntimeError("Publisher is not currently running.")

        await self._queue.put(message)

    async def _published_data_loop(self):
        """
        A loop designed to be run in a thread that will continuously check for new messages in the queue and trigger
        subscribers as they are received
        """
        while not self._killed:
            try:
                message = await asyncio.wait_for(self._queue.get(), timeout=self.timeout)

                try:
                    contracts = [sub.trigger(message) for sub in self._subscribers]

                    await asyncio.gather(*contracts)

                except Exception as e:
                    pass

                # will only reach this section after all the messages have been handled

            except asyncio.TimeoutError:
                continue

    def subscribe(
        self,
        callback: Callable[[_T], None] | Callable[[_T], Coroutine[None, None, None]],
        name: str | None = None,
    ) -> str:
        """
        Subscribe the publisher so whenever we receive a message the callback will be triggered.

        Args:
            callback: The callback function that will be triggered when a message is published.
            name: Optional name for the subscriber, mainly used for debugging.

        Returns:
            str: A unique identifier for the subscriber. You can use this key to unsubscribe later.

        """
        sub = Subscriber(callback, name)
        self._subscribers.append(sub)
        return sub.id

    def unsubscribe(self, identifier: str):
        """
        Unsubscribe the publisher so the given subscriber will no longer receive messages.

        Args:
            identifier: The unique identifier of the subscriber to remove.

        Raises:
            KeyError: If no subscriber with the given identifier exists.
        """
        index_to_remove = [index for index, sub in enumerate(self._subscribers) if sub.id == identifier]
        if not index_to_remove:
            raise KeyError(f"No subscriber with identifier {identifier} found.")

        index_to_remove = index_to_remove[0]
        self._subscribers.pop(index_to_remove)

    async def listener(
        self,
        message_filter: Callable[[_T], bool],
        result_mapping: Callable[[_T], _TOutput] = lambda x: x,
        listener_name: str | None = None,
    ):
        async def single_listener():
            returnable_result: RequestCompletionMessage | None = None
            # we are gonna use the asyncio.event system instead of threading
            listener_event = asyncio.Event()

            async def special_subscriber(message: _T):
                nonlocal returnable_result
                if message_filter(message):
                    # this will trigger the end of the listener loop
                    returnable_result = message
                    listener_event.set()
                    return

            sub_id = self.subscribe(
                callback=special_subscriber,
                name=listener_name,
            )

            while True:
                try:
                    await asyncio.wait_for(listener_event.wait(), timeout=self.timeout)
                    break
                except asyncio.TimeoutError:
                    pass

                if self._killed:
                    raise ValueError("Listener has been killed before receiving the correct message.")

            assert returnable_result is not None, "Listener should have received a message before returning."
            self.unsubscribe(sub_id)
            return result_mapping(returnable_result)

        return await single_listener()

    async def shutdown(self):
        self._killed = True
        await self.pub_loop

        return


def create_publisher() -> RCPublisher:
    return RCPublisher()
