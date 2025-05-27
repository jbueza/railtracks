from __future__ import annotations

import asyncio
import concurrent.futures
import multiprocessing
import threading
import queue
import warnings

from .messages import RequestCompletionMessage
from abc import ABC, abstractmethod

from typing import List, Callable, Dict, Literal, TypeVar, Generator, Generic, Coroutine, Awaitable

_T = TypeVar("_T")
_TOutput = TypeVar("_TOutput")


ExecutionConfigurations = Literal["thread"]


class Subscriber(Generic[_T]):
    def __init__(self, callback: Callable[[_T], None]):
        self.callback = callback

    def trigger(self, message: _T):
        self.callback(message)


class AsyncSubscriber(Generic[_T]):
    def __init__(self, callback: Callable[[_T], Awaitable[None]]):
        self.callback = callback

    async def trigger(self, message: _T):
        await self.callback(message)


# this is the top level class which should be run at the root. You should pass around a simpler object accross threads or processes.
class RCPublisher(Generic[_T]):
    timeout = 0.1

    def __init__(
        self,
    ):
        self._queue: queue.Queue[_T] = queue.Queue()
        self._subscribers: List[Subscriber[_T]] = []

        self._killed = False
        self._subscriber_futures: List[concurrent.futures.Future[None]] = []
        self._executor = concurrent.futures.ThreadPoolExecutor()

        self._executor.submit(self._published_data_loop)

    def publish(self, message: _T):
        self._queue.put(message)

    def _published_data_loop(self):
        while not self._killed:
            try:
                message = self._queue.get(timeout=self.timeout)

                results = self._executor.map(lambda sub: sub.trigger(message), self._subscribers)

                for r in results:
                    pass

            except queue.Empty:
                continue
            except Exception as e:
                print(e)

    def subscribe(self, callback: Callable[[_T], None]):

        sub = Subscriber(callback)
        self._subscribers.append(sub)

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

            self.subscribe(special_subscriber)
            listener_event.wait()
            assert returnable_result is not None, "Listener should have received a message before returning."
            return result_mapping(returnable_result)

        future = self._executor.submit(single_listener)
        return future

    def shutdown(self, force: bool):
        self._killed = True
        self._executor.shutdown(wait=True, cancel_futures=force)
        for f in self._subscriber_futures:
            f.result()

        return


def create_publisher() -> RCPublisher:
    return RCPublisher()
