from __future__ import annotations

import multiprocessing
import queue
import threading
import warnings

from typing import Any, Callable, ParamSpec, TypeVar, NamedTuple, Generic, TYPE_CHECKING
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

if TYPE_CHECKING:
    from ..run import Runner

from ..nodes.nodes import Node

from ..context import set_parent_id, set_runner, get_runner, get_parent_id

_P = ParamSpec("_P")
_TOutput = TypeVar("_TOutput")


class Result(Generic[_TOutput]):

    def __init__(
        self,
        request_id: str,
        node: Node[_TOutput],
        *,
        result: _TOutput | None = None,
        error: Exception | None = None,
    ):
        if result is not None and error is not None:
            raise ValueError("Result and error cannot be both set")
        if result is None and error is None:
            raise ValueError("Result or error must be set")

        self.request_id = request_id
        self.node = node
        self.result = result
        self.error = error

    def __repr__(self):
        return f"Result(request_id={self.request_id}, result={self.result}, error={self.error})"


class RCWorkerManager:
    def __init__(
        self,
        *,
        thread_max_workers: int = 15,
        process_max_workers: int = 15,
    ):
        # TODO improve the logic here for config

        self._thread_queue = queue.SimpleQueue[Result]()
        self._process_queue: multiprocessing.Queue[Result] = multiprocessing.Queue()

        self._is_shutdown = False

        # TODO implement our own threading logic so we can track things however we want
        self._thread_executor = ThreadPoolExecutor(max_workers=thread_max_workers)
        self._process_executor = ProcessPoolExecutor(max_workers=process_max_workers)

    @staticmethod
    def wrap_function(runner_ref: Runner, request_id: str, node: Node[_TOutput], handler: Callable[[Result], None]):
        """Wrap a function to be run in the executor."""

        def wrapped_func():
            # setting the context variables for the thread of interest.
            set_parent_id(node.uuid)
            set_runner(runner_ref)
            try:
                result = node.invoke()
                response = Result(request_id, node=node, result=result)
            except Exception as e:
                response = Result(request_id, node=node, error=e)
            finally:
                returned_result = handler(response)
                if isinstance(returned_result, Exception):

                    raise returned_result

            return returned_result

        return wrapped_func

    def thread_submit(self, request_id: str, node: Node[_TOutput], handler: Callable[[Result], None]):
        """Submit a function to the thread executor."""
        print(f"{threading.get_ident()} submitting {node} to thread executor")
        runner_ref = get_runner()
        wrapped = self.wrap_function(runner_ref, request_id, node, handler)
        return self._thread_executor.submit(wrapped)

    def process_submit(self, request_id: str, node: Node[_TOutput], handler: Callable[[Result], None]):
        """Submit a function to the process executor."""
        runner_ref = get_runner()
        wrapped = self.wrap_function(runner_ref, request_id, node, handler)

        return self._process_executor.submit(wrapped)

    def shutdown(self, wait: bool = True):
        """Shutdown the executors waiting for all tasks to finish unless overriden by wait=False"""

        self._thread_executor.shutdown(wait=wait)
        self._process_executor.shutdown(wait=wait)
