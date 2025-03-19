from __future__ import annotations

from typing import List, TypeVar, Callable

from .config import ExecutorConfig
from .tools.profiling import Stamp, StampManager
from .tools.stream import Subscriber
from .state.request import RequestForest
from .state.node import NodeForest
from .visuals.agent_viewer import AgentViewer


_TOutput = TypeVar("_TOutput")


# TODO add some the logic for an optional architecture requirement.
class ExecutionInfo:
    def __init__(
        self,
        request_heap: RequestForest,
        node_heap: NodeForest,
        stamper: StampManager,
        exception_history: List[Exception] = None,
        executor_config: ExecutorConfig = ExecutorConfig(),
    ):
        self.request_heap = request_heap
        self.node_heap = node_heap
        self.stamper = stamper
        self.exception_history = exception_history or []
        self.executor_config = executor_config

    @classmethod
    def default(cls):
        return cls.create_new()

    @classmethod
    def create_new(
        cls,
        executor_config: ExecutorConfig = ExecutorConfig(),
    ) -> ExecutionInfo:
        request_heap = RequestForest()
        node_heap = NodeForest()
        stamper = StampManager()

        return ExecutionInfo(
            request_heap=request_heap,
            node_heap=node_heap,
            stamper=stamper,
            exception_history=[],
            executor_config=executor_config,
        )

    @property
    def answer(self) -> _TOutput:
        """Convenience method to access the answer of the run."""
        return self.request_heap.answer

    @property
    def all_stamps(self) -> List[Stamp]:
        """Convenience method to access all the stamps of the run."""
        return self.stamper.all_stamps

    def view_graph(self):
        AgentViewer(self.all_stamps, self.request_heap, self.node_heap).display_graph()
