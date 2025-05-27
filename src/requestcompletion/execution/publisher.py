from __future__ import annotations

import asyncio
import concurrent.futures
import multiprocessing
import threading
import queue
import uuid
import warnings

from .messages import RequestCompletionMessage
from abc import ABC, abstractmethod

from typing import List, Callable, Dict, Literal, TypeVar, Generator, Generic, Coroutine, Awaitable

_T = TypeVar("_T")
_TOutput = TypeVar("_TOutput")


class Subscriber(Generic[_T]):
    """A simple wrapper class of a callback function."""

    # this could be done without a class, but I want to keep as extendable as possible.
    def __init__(self, callback: Callable[[_T], None]):
        self.callback = callback
        self.id = str(uuid.uuid4())

    def trigger(self, message: _T):
        """Trigger this subscriber with the given message."""
        self.callback(message)


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
        self._queue: queue.Queue[_T] = queue.Queue()
        self._subscribers: List[Subscriber[_T]] = []

        self._listener_futures: List[concurrent.futures.Future] = []

        self._killed = False
        self._executor = concurrent.futures.ThreadPoolExecutor()

        self.pub_loop = self._executor.submit(self._published_data_loop)

    def __enter__(self):
        """Enable the use of the publisher in a context manager."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Shutdown the publisher when exiting the context manager."""
        self.shutdown(force=True)

    def publish(self, message: _T):
        """Publish a message the publisher. This will trigger all subscribers to receive the message.

        Args:
            message: The message you would like to publish.

        """
        self._queue.put(message)

    def _published_data_loop(self):
        """
        A loop designed to be run in a thread that will continuously check for new messages in the queue and trigger
        subscribers as they are received
        """

        while not self._killed:
            try:
                message = self._queue.get(timeout=self.timeout)

                fs = [self._executor.submit(lambda sub: sub.trigger(message), s) for s in self._subscribers]
                # TODO: there has got to be a better fix here.
                for f in concurrent.futures.as_completed(fs):
                    try:
                        _ = f.result()  # trigger the error if present
                    except Exception as e:
                        warnings.warn("Error in subscriber callback: " + str(e), RuntimeWarning)

            except queue.Empty:
                continue

    def subscribe(self, callback: Callable[[_T], None]):
        """
        Subscribe the publisher so whenever we receive a message the callback will be triggered.

        Args:
            callback: The callback function that will be triggered when a message is published.

        Returns:
            str: A unique identifier for the subscriber. You can use this key to unsubscribe later.
        """
        sub = Subscriber(callback)
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

    def listener(
        self,
        message_filter: Callable[[_T], bool],
        result_mapping: Callable[[_T], _TOutput] = lambda x: x,
    ):
        def single_listener():
            returnable_result: RequestCompletionMessage | None = None
            # we are gonna use the asyncio.event system instead of threading
            listener_event = threading.Event()

            def special_subscriber(message: _T):
                nonlocal returnable_result
                if message_filter(message):
                    # this will trigger the end of the listener loop
                    returnable_result = message
                    listener_event.set()
                    return

            sub_id = self.subscribe(special_subscriber)
            while True:
                if listener_event.wait(timeout=self.timeout):
                    break
                if self._killed:
                    raise ValueError("Listener has been killed before receiving the correct message.")

            assert returnable_result is not None, "Listener should have received a message before returning."
            self.unsubscribe(sub_id)
            return result_mapping(returnable_result)

        future = self._executor.submit(single_listener)

        return future

    def shutdown(self, force: bool):
        self._killed = True

        self.pub_loop.result()
        self._executor.shutdown(wait=False, cancel_futures=force)

        return


def create_publisher() -> RCPublisher:
    return RCPublisher()
