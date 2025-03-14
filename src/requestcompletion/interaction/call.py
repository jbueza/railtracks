import asyncio
import warnings

from typing import ParamSpec, Callable, TypeVar

from ..run import get_active_runner, Runner
from ..context import parent_id
from ..nodes.nodes import Node

_TOutput = TypeVar("_TOutput")
_P = ParamSpec("_P")


async def call(node: Callable[_P, Node[_TOutput]], *args: _P.args, **kwargs: _P.kwargs):
    runner: Runner = get_active_runner()

    # we create a new context to prevent bleeding memory from the previous context.
    try:
        parent_node_id = parent_id.get()
        created_node = node(*args, **kwargs)
        parent_node_id.put(created_node.uuid)
        return await runner.call(parent_node_id, created_node)
    except (asyncio.TimeoutError, asyncio.CancelledError):
        try:
            node_to_cancel_id = parent_id.get()
            await runner.cancel(node_to_cancel_id)
        except LookupError:
            warnings.warn("Could not find the node to cancel.")


# TODO add support for any general user defined streaming object
def stream(item: str):
    runner: Runner = get_active_runner()
    return runner.stream(item)
