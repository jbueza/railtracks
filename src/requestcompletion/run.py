import contextvars
from typing import TypeVar, ParamSpec, Callable

from src.requestcompletion.tools import DataStream, Subscriber
from ..nodes.nodes import Node


from .info import (
    ExecutionInfo,
)
from src.requestcompletion.state.execute import RCState


_TOutput = TypeVar("_TOutput")
_P = ParamSpec("_P")

parent_id = contextvars.ContextVar("parent_id")


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
        executor_info: ExecutionInfo,
    ):
        self.rc_state = RCState(executor_info)

        self._data_streamer = DataStream(
            subscribers=[
                (executor_info.subscriber if executor_info.subscriber is not None else Subscriber.null_concrete_sub()())
            ]
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # release the instance so it can be used again.
        self._instance = None

    # TODO: add async support
    async def run(
        self,
        start_node: Callable[_P, Node] | None = None,
        *args: _P.args,
        **kwargs: _P.kwargs,
    ):

        if start_node is not None:
            node = start_node(*args, **kwargs)
            self.rc_state.create_first_entry(node)
        else:
            raise RuntimeError("We currently do not support running without a start node.")

        return await self.rc_state.execute(node)

    async def cancel(self):
        # collects the parent id of the current node that is running that is gonna get cancelled
        parent_id.get()

    async def call(self, node: Callable[_P, Node[_TOutput]], *args: _P.args, **kwargs: _P.kwargs):
        await self.rc_state.call_nodes(node(*args, **kwargs))

    # TODO add support for any general user defined streaming object
    def stream(self, item: str):
        self._data_streamer.publish(item)


def get_active_runner():
    if Runner._instance is None:
        raise RunnerNotFoundError("There is no active runner. Please start one using `with Runner(...):`")
    return Runner._instance
