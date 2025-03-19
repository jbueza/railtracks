import asyncio
import threading
from typing import TypeVar, ParamSpec, Callable

from .config import ExecutorConfig
from .tools.stream import DataStream, Subscriber
from .nodes.nodes import Node


from .info import (
    ExecutionInfo,
)
from .state.execute import RCState

from .context import parent_id


_TOutput = TypeVar("_TOutput")
_P = ParamSpec("_P")


class RunnerCreationError(Exception):
    pass


class RunnerNotFoundError(Exception):
    pass


class Runner:
    # singleton pattern
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is not None:
            raise RunnerCreationError(
                "You can only create one instance of Runner at a time. To create a other you must create a new process instead (see docs for more details)."
            )
        cls._instance = super(Runner, cls).__new__(cls)
        return cls._instance

    def __init__(
        self,
        subscriber: Callable[[str], None] = None,
        executor_config: ExecutorConfig = ExecutorConfig(),
    ):

        executor_info = ExecutionInfo.create_new(executor_config=executor_config)
        executor_config = executor_config

        self.rc_state = RCState(executor_info)
        if subscriber is None:
            self._data_streamer = DataStream()
        else:

            class DynamicSubscriber(Subscriber[str]):
                def handle(self, item: str) -> None:
                    subscriber(item)

            self._data_streamer = DataStream(subscribers=[DynamicSubscriber()])

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        Runner._instance = None

    def run_sync(self, start_node: Callable[..., Node] | None = None, *args, **kwargs):
        # If no loop is running, create one and run the coroutine.
        result = asyncio.run(self.run(start_node, *args, **kwargs))
        return result

    async def run(
        self,
        start_node: Callable[_P, Node] | None = None,
        *args: _P.args,
        **kwargs: _P.kwargs,
    ):

        if start_node is not None:
            node = start_node(*args, **kwargs)
            parent_id.set(node.uuid)
            self.rc_state.create_first_entry(node)
        else:
            raise RuntimeError("We currently do not support running without a start node.")
        try:
            await self.rc_state.execute(node)
        finally:
            threading.Thread(self._data_streamer.stop(self.rc_state.executor_config.force_close_streams)).start()

        return self.rc_state.info

    async def cancel(self, node_id: str):
        raise NotImplementedError(
            "Currently we do not support cancelling nodes. Please contact Logan to add this feature."
        )
        # collects the parent id of the current node that is running that is gonna get cancelled
        await self.rc_state.cancel(node_id)

    # TODO implement this method and any additional logic in rc_state that is required.
    def from_state(self, executor_info: ExecutionInfo):
        raise NotImplementedError(
            "Currently we do not support running from a state object. Please contact Logan to add this feature."
        )
        # self.rc_state = RCState(executor_info)

    async def call(self, parent_node_id: str, node: Node):
        return await self.rc_state.call_nodes(parent_node_id, node)

    # TODO add support for any general user defined streaming object
    def stream(self, item: str):
        self._data_streamer.publish(item)


def get_active_runner():
    if Runner._instance is None:
        raise RunnerNotFoundError("There is no active runner. Please start one using `with Runner(...):`")
    return Runner._instance
