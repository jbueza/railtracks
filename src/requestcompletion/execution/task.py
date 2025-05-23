from abc import abstractmethod, ABC
from typing import Generic, TypeVar, Literal, Dict

from .execution_strategy import ThreadedExecutionStrategy, ProcessExecutionStrategy, TaskExecutionStrategy
from ..nodes.nodes import Node


# TODO do we need some notion of a intermediate to return as a signal. This would be specifically useful for the return of a node.


class Task(ABC):
    def __init__(
        self,
        request_id: str,
        node: Node,
        executor: TaskExecutionStrategy,
    ):
        self.request_id = request_id
        self.node = node
        self.executor = executor

    @property
    def invoke(self):

