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

    # we create a new context to prevent bleeding memory from the previous context.

    created_node = node(*args, **kwargs)

    # the reference to current node running must be collected and passed into the state object
    p_n_id = parent_id.get()
    # but we also must update the variable so if the child node makes its own calls it is operating on the correct ID.
    prev_token = parent_id.set(created_node.uuid)
    try:

        return await runner.call(p_n_id, created_node)
    except (asyncio.TimeoutError, asyncio.CancelledError):
        try:
            node_to_cancel_id = parent_id.get()
            await runner.cancel(node_to_cancel_id)
        except LookupError:
            warnings.warn("Could not find the node to cancel.")
    finally:
        # finally after the child is finished operating we need to pop the identifer off the stack getting back the
        #  original identifier.
        parent_id.reset(prev_token)


# TODO add support for any general user defined streaming object
def stream(item: str):
    runner: Runner = get_active_runner()
    return runner.stream(item)
