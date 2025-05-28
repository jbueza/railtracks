from __future__ import annotations

import asyncio
import concurrent.futures
import inspect

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from .messages import RequestSuccess, RequestFailure

from ..context import get_globals, register_globals, ThreadContext, update_parent_id
from ..nodes.nodes import NodeState

if TYPE_CHECKING:
    from .task import Task


class TaskExecutionStrategy(ABC):

    def shutdown(self):
        pass

    @abstractmethod
    async def execute(self, task: Task):
        pass


class AsyncioExecutionStrategy(TaskExecutionStrategy):

    def shutdown(self):
        pass

    async def execute(self, task: Task):
        invoke_func = task.invoke

        publisher = get_globals().publisher

        try:
            result = await invoke_func()
            response = RequestSuccess(request_id=task.request_id, node_state=NodeState(task.node), result=result)
        except Exception as e:
            response = RequestFailure(request_id=task.request_id, node_state=NodeState(task.node), error=e)
        finally:
            await publisher.publish(response)

        return response


class ConcurrentFuturesExecutor(TaskExecutionStrategy):
    def __init__(self, executor: concurrent.futures.Executor):
        self.executor: concurrent.futures.Executor | None = executor

    # TODO addd config here as required
    def shutdown(self):
        if self.executor is not None:
            self.executor.shutdown(wait=True)
            self.executor = None

    def execute(self, task: Task):
        if inspect.iscoroutine(task.invoke):
            # TODO: make sure this doesn't brick things As long as the globals pass we should be fine.
            def non_async_wrapper():
                return asyncio.run(task.invoke())

            invoke_func = non_async_wrapper
        else:
            invoke_func = task.invoke

        parent_global_variables = get_globals()

        publisher = parent_global_variables.publisher

        def wrapped_invoke(global_vars: ThreadContext):
            register_globals(
                global_vars.prepare_new(
                    new_parent_id=task.node.uuid,
                )
            )
            try:
                result = invoke_func()
                response = RequestSuccess(request_id=task.request_id, node_state=NodeState(task.node), result=result)
            except Exception as e:
                response = RequestFailure(request_id=task.request_id, node_state=NodeState(task.node), error=e)
            finally:
                publisher.publish(response)

        f = self.executor.submit(wrapped_invoke, parent_global_variables)

        return f


class ThreadedExecutionStrategy(ConcurrentFuturesExecutor):

    # TODO add config as required here
    def __init__(self):
        super().__init__(concurrent.futures.ThreadPoolExecutor())


class ProcessExecutionStrategy(TaskExecutionStrategy):

    def __init__(self):
        raise NotImplementedError("We do not support Process Task Execution Strategy yet.")
