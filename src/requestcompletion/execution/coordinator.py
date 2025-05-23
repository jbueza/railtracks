import asyncio
import concurrent.futures
import inspect
import threading
from abc import ABC, abstractmethod


from typing import Literal, TypeVar, Generic, Coroutine, Dict, get_args

from .messages import RequestSuccess, RequestFailure
from .task import Task
from ..nodes.nodes import Node, NodeState


class CoordinatorState:
    # simple objects that stores the history of the coordinator
    # TODO implement accordingly
    def __init__(self):
        pass

    @classmethod
    def empty(cls):
        return cls()


# Note the coordinator will be the concrete invoker of the commands
class Coordinator:

    RunningMode = Literal["thread", "process", "async"]

    def __init__(
        self,
        execution_modes: Dict[RunningMode, TaskExecutionStrategy] = None,
    ):
        self.state = CoordinatorState.empty()
        assert set(execution_modes.keys()) == set(
            get_args(Coordinator.RunningMode)
        ), "You must provide all execution modes."
        self.execution_strategy = execution_modes

    def start(self):
        # TODO add config here
        for strategy in self.execution_strategy.values():
            strategy.start()

        # TODO attach the relevant subscriber's here

    # TODO write up required params here
    async def submit(
        self,
        task: Task,
        mode: RunningMode,
    ):
        # TODO write up the logic to update state object
        return await self.execution_strategy[mode].execute(task)

    # TODO come up with logic here
    def system_detail(self) -> CoordinatorState:
        return self.state

    # TODO add params here
    def shutdown(self):
        for strategy in self.execution_strategy.values():
            strategy.shutdown()
