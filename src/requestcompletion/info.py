from __future__ import annotations

from typing import List, TypeVar, Callable

from .config import ExecutorConfig
from .utils.profiling import Stamp, StampManager
from .utils.stream import Subscriber
from .state.request import RequestForest
from .state.node import NodeForest
from .visuals.agent_viewer import AgentViewer


_TOutput = TypeVar("_TOutput")


# TODO add some the logic for an optional architecture requirement.
class ExecutionInfo:
    """
    A class that contains the full details of the state of a run at any given point in time.

    The class is designed to be used as a snapshot of the state which can be both used to view the state of the run and
    to be used to continue the run from the point it was saved.
    """
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
        """ Creates a new "empty" instance of the ExecutionInfo class with the default values. """
        return cls.create_new()

    @classmethod
    def create_new(
        cls,
        executor_config: ExecutorConfig = ExecutorConfig(),
    ) -> ExecutionInfo:
        """
        Creates a new empty instance of state variables with the provided executor configuration.

        Args:
            executor_config: The configuration to use for the executor.
        """
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
        """A convenience method used to view a graph representation of the run."""
        AgentViewer(self.all_stamps, self.request_heap, self.node_heap).display_graph()
