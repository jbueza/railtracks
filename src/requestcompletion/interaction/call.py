import asyncio
import warnings

from typing import ParamSpec, Callable, TypeVar

from ..run import get_active_runner, Runner
from ..context import parent_id
from ..nodes.nodes import Node

_TOutput = TypeVar("_TOutput")
_P = ParamSpec("_P")


async def call(node: Callable[_P, Node[_TOutput]], *args: _P.args, **kwargs: _P.kwargs):
    """
    Call another node from within a node inside the framework. This will return a coroutine that you can interact with
    in whatever way using the `asyncio` framework.

    Args:
        node: The node type you would like to create
        *args: The arguments to pass to the node
        **kwargs: The keyword arguments to pass to the node


    """
    runner: Runner = get_active_runner()

    # the reference to current node running must be collected and passed into the state object
    p_n_id = parent_id.get()
    # but we also must update the variable so if the child node makes its own calls it is operating on the correct ID.

    try:
        return await runner.call(p_n_id, node, *args, **kwargs)
    except (asyncio.TimeoutError, asyncio.CancelledError):
        child_id = parent_id.get()
        if child_id == p_n_id:
            warnings.warn("The child node was not created before the call was cancelled.")
            return

        await runner.cancel(child_id)
    finally:
        # reset the parent id to the original value
        parent_id.set(p_n_id)


# TODO add support for any general user defined streaming object
def stream(item: str):
    runner: Runner = get_active_runner()
    return runner.stream(item)
