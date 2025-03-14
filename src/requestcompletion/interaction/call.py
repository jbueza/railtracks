import asyncio

from typing import ParamSpec, Callable, TypeVar

from ..run import get_active_runner, Runner
from ...nodes.nodes import Node

_TOutput = TypeVar("_TOutput")
_P = ParamSpec("_P")


async def call(node: Callable[_P, Node[_TOutput]], *args: _P.args, **kwargs: _P.kwargs):
    runner: Runner = get_active_runner()
    # we create a new context to prevent bleeding memory from the previous context.
    return runner.call(node, *args, **kwargs)




# TODO add support for any general user defined streaming object
def stream(item: str):
    runner: Runner = get_active_runner()
    return runner.stream(item)
