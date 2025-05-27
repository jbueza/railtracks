from abc import abstractmethod, ABC
from typing import Generic, TypeVar, Literal, Dict

from .execution_strategy import ThreadedExecutionStrategy, ProcessExecutionStrategy, TaskExecutionStrategy
from ..nodes.nodes import Node


class Task(ABC):
    def __init__(
        self,
        request_id: str,
        node: Node,
    ):
        self.request_id = request_id
        self.node = node

    @property
    def invoke(self):
        return self.node.invoke
