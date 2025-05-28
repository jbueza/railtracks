import asyncio
import concurrent.futures
import inspect
import threading
from abc import ABC, abstractmethod
import time


from typing import Literal, TypeVar, Generic, Coroutine, Dict, get_args, Callable, List

from .execution_strategy import TaskExecutionStrategy
from .messages import (
    RequestCompletionMessage,
    RequestFinishedBase,
    RequestSuccess,
    RequestCreation,
    ExecutionConfigurations,
)
from .task import Task
from ..context import get_globals


class Job:
    def __init__(
        self,
        request_id: str,
        parent_node_id: str,
        child_node_id: str,
        status: Literal["opened", "closed"],
        result: Literal["success", "failure"] | None = None,
        start_time: float = None,
        end_time: float = None,
    ):
        self.request_id = request_id
        self.parent_node_id = parent_node_id
        self.child_node_id = child_node_id
        self.status = status
        self.result = result
        self.start_time = start_time
        self.end_time = end_time

    @classmethod
    def create_new(
        cls,
        task: Task,
    ):
        return cls(
            request_id=task.request_id,
            parent_node_id=task.node.uuid,
            child_node_id=task.node.uuid,
            status="opened",
            start_time=time.time(),
        )

    def end_job(self, result: Literal["success", "failure"]):
        self.result = result
        self.status = "closed"
        self.end_time = time.time()

    def __str__(self):
        return f"Job(request_id={self.request_id}, status={self.status}, result={self.result}, start_time={self.start_time}, end_time={self.end_time})"

    def __repr__(self):
        return self.__str__()


class CoordinatorState:
    # simple objects that stores the history of the coordinator
    # TODO implement accordingly
    def __init__(self):
        self.job_list: List[Job] = []

    @classmethod
    def empty(cls):
        return cls()

    def add_job(self, task: Task):
        """ """
        new_job = Job.create_new(task)
        self.job_list.append(new_job)

    def end_job(self, request_id: str, result: Literal["success", "failure"]):
        """
        End a job with the given request_id and result.
        """
        for job in self.job_list:
            if job.request_id == request_id and job.status == "opened":
                job.end_job(result)
                return

        raise ValueError(f"No open job found with request_id: {request_id}")

    def __str__(self):
        return ",".join([str(x) for x in self.job_list])


# Note the coordinator will be the concrete invoker of the commands
class Coordinator:

    def __init__(
        self,
        execution_modes: Dict[ExecutionConfigurations, TaskExecutionStrategy] = None,
    ):
        self.state = CoordinatorState.empty()
        assert set(execution_modes.keys()) == set(
            get_args(ExecutionConfigurations)
        ), "You must provide all execution modes."
        self.execution_strategy = execution_modes

    def start(self, publisher):
        publisher.subscribe(self.handle_item)

    def handle_item(self, item: RequestCompletionMessage):
        if isinstance(item, RequestFinishedBase):
            self.state.end_job(item.request_id, "success" if isinstance(item, RequestSuccess) else "failure")

    # TODO write up required params here
    async def submit(
        self,
        task: Task,
        mode: ExecutionConfigurations,
    ):
        self.state.add_job(task)

        return await self.execution_strategy[mode].execute(task)

    # TODO come up with logic here
    def system_detail(self) -> CoordinatorState:
        return self.state

    # TODO add params here
    def shutdown(self):
        for strategy in self.execution_strategy.values():
            strategy.shutdown()
