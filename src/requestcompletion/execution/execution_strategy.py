import asyncio
import concurrent.futures
import inspect

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from .messages import RequestSuccess, RequestFailure
from .publisher import Publisher
from ..context import get_globals, register_globals, ThreadContext
from ..nodes.nodes import NodeState

if TYPE_CHECKING:
    from .task import Task


class TaskExecutionStrategy(ABC):

    def shutdown(self):
        pass

    @abstractmethod
    def execute(self, task: Task, publisher: Publisher):
        pass


class ConcurrentFuturesExecutor(TaskExecutionStrategy):
    def __init__(self, executor: concurrent.futures.Executor):
        self.executor: concurrent.futures.Executor | None = executor

    # TODO addd config here as required
    def shutdown(self):
        if self.executor is not None:
            self.executor.shutdown(wait=True)
            self.executor = None

    def execute(self, task: Task, publisher: Publisher):
        if inspect.iscoroutine(task.invoke):
            # TODO: make sure this doesn't brick things As long as the globals pass we should be fine.
            def non_async_wrapper():
                return asyncio.run(task.invoke())

            invoke_func = non_async_wrapper
        else:
            invoke_func = task.invoke

        parent_global_variables = get_globals()

        def wrapped_invoke(global_vars: ThreadContext):
            register_globals(global_vars)
            return invoke_func()

        try:
            f = self.executor.submit(wrapped_invoke, parent_global_variables)
            result = f.result()
            response = RequestSuccess(request_id=task.request_id, node_state=NodeState(task.node), result=result)
        except Exception as e:
            response = RequestFailure(request_id=task.request_id, node_state=NodeState(task.node), error=e)
        finally:
            publisher.publish(response)

        return response


class ThreadedExecutionStrategy(ConcurrentFuturesExecutor):

    # TODO add config as required here
    def __init__(self):
        super().__init__(concurrent.futures.ThreadPoolExecutor())


class ProcessExecutionStrategy(TaskExecutionStrategy):

    def __init__(self):
        self.executor = None

    def start(self):
        self.executor = concurrent.futures.ProcessPoolExecutor()

    # TODO add config
    def shutdown(self):
        if self.executor is not None:
            self.executor.shutdown(wait=True)
            self.executor = None

    async def execute(self, task: Task):
        if self.executor is None:
            raise RuntimeError("WTF Logan")

        if inspect.iscoroutine(task.invoke):

            def non_async_wrapper():
                return asyncio.run(task.invoke())

            invoke_func = non_async_wrapper
        else:
            invoke_func = task.invoke

        async def wrapped_task():
            loop = asyncio.get_event_loop()
            # TODO setup globals here properly
            try:
                result = await loop.run_in_executor(self.executor, invoke_func)
                response = RequestSuccess(request_id=task.request_id, node_state=NodeState(task.node), result=result)
            except Exception as e:
                response = RequestFailure(request_id=task.request_id, node_state=NodeState(task.node), error=e)
            finally:
                publisher = get_publisher()
                publisher.publish(response)

            return

        return await wrapped_task()


class AsyncExecutionStrategy(TaskExecutionStrategy):
    async def execute(self, task: Task):
        # Implement async execution logic here

        if not inspect.iscoroutine(task.invoke):
            # TODO raise a more general exception (principle of abstraction)
            raise RuntimeError("You cannot invoke a non-async function in async mode. ")

        async def wrapped_task():
            # TODO set any context variables here
            try:
                result = await task.invoke()
                response = RequestSuccess(request_id=task.request_id, node_state=NodeState(task.node), result=result)
            except Exception as e:
                response = RequestFailure(request_id=task.request_id, node_state=NodeState(task.node), error=e)
                raise
            finally:
                publisher = get_publisher()
                publisher.publish(response)

            return result

        return await wrapped_task()
