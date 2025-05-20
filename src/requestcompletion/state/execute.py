import multiprocessing
import queue
import warnings

from typing import Any, Callable, ParamSpec, TypeVar, NamedTuple
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

from ..nodes.nodes import Node

_P = ParamSpec("_P")
_TOutput = TypeVar("_TOutput")


class Result:
    def __init__(
        self,
        request_id: str,
        node: Node,
        *,
        result: Any | None = None,
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
        thread_max_workers: int = None,
        process_max_workers: int = None,
    ):
        # TODO improve the logic here for config

        self._thread_queue = queue.SimpleQueue[Result]()
        self._process_queue: multiprocessing.Queue[Result] = multiprocessing.Queue()

        self._is_shutdown = False
        self._thread_executor = ThreadPoolExecutor(max_workers=thread_max_workers)
        self._process_executor = ProcessPoolExecutor(max_workers=process_max_workers)

    def thread_submit(self, request_id: str, node: Node):
        """Submit a function to the thread executor."""

        def wrapped_func():
            try:
                result = node.invoke()
            except Exception as e:
                response = Result(request_id, node=node, error=e)
                self._thread_queue.put(response)
                print(response)
                raise e

            print(result)
            self._thread_queue.put(Result(request_id, node=node, result=result))
            return result

        return self._thread_executor.submit(wrapped_func)

    def process_submit(self, request_id: str, node: Node):
        """Submit a function to the process executor."""

        def wrapped_func():
            try:
                result = node.invoke()
            except Exception as e:
                result = Result(request_id, node=node, error=e)
                self._process_queue.put(result)
                raise e

            self._process_queue.put(Result(request_id, node=node, result=result))
            return result

        return self._process_executor.submit(wrapped_func)

    def shutdown(self, wait: bool = True):
        """Shutdown the executors waiting for all tasks to finish unless overriden by wait=False"""
        if not self._thread_queue.empty():
            warnings.warn(
                "Thread queue is not empty, when a shutdown occurred, the state may not fully reflect the correct system state."
            )

        if not self._process_queue.empty():
            warnings.warn(
                "Process queue is not empty, when a shutdown occurred, the state may not fully reflect the correct system state."
            )

        self._is_shutdown = True

        self._process_queue.close()

        self._thread_executor.shutdown(wait=wait)
        self._process_executor.shutdown(wait=wait)

    def thread_result_iter(self, refresh: float = 0.01):
        while not self._is_shutdown:
            try:
                result = self._thread_queue.get(timeout=refresh)
                yield result
            except queue.Empty:
                continue

        return

    def process_result_iter(self, refresh: float = 0.01):
        while not self._is_shutdown:
            try:
                result = self._process_queue.get(timeout=refresh)
                yield result
            except queue.Empty:
                continue

        return
