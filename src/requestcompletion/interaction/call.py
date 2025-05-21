import asyncio
import warnings
import time

from typing import ParamSpec, Callable, TypeVar

from ..context import get_parent_id
from ..run import get_runner, Runner, RunnerNotFoundError

from ..nodes.nodes import Node

_TOutput = TypeVar("_TOutput")
_P = ParamSpec("_P")


async def call(node: Callable[_P, Node[_TOutput]], *args: _P.args, **kwargs: _P.kwargs):
    """
    Call a node from within a node inside the framework. This will return a coroutine that you can interact with
    in whatever way using the `asyncio` framework.

    Args:
        node: The node type you would like to create
        *args: The arguments to pass to the node
        **kwargs: The keyword arguments to pass to the node


    """
    # there are 4 cases that we need to handle in this function.
    # 1. The runner exists and the parent node id is set
    #  - in this case we can just call the node and return the result.
    # 2. The runner exists and the parent node id is not set
    #  - This is the case where this is actually the first node is called, however this is no different from case 1
    # 3. The runner does not exist and the parent node id is set.
    #  - This makes no sense and means a system invariant has been broken.
    # 4. The runner does not exist and the parent node id is not set.
    #  - In this case we have to start the system from scratch and create a new runner.

    runner: Runner = get_runner()
    if runner is None:
        # in the case that a runner doesn't exists we will need to wrap it.
        # we will use the default values in the system (see config.py)
        with Runner() as runner:
            response = await runner.run(node, *args, **kwargs)

            return response.answer

    # the reference to current node running must be collected and passed into the state object
    p_n_id = get_parent_id()
    # but we also must update the variable so if the child node makes its own calls it is operating on the correct ID.

    try:
        # note the call function should be able to handle when the parent node id is none.
        return await runner.call(p_n_id, node, *args, **kwargs)
    except (asyncio.TimeoutError, asyncio.CancelledError):
        # TODO complete the cancelleation logic
        await runner.cancel()


# TODO add support for any general user defined streaming object
def stream(item: str):
    runner: Runner = get_runner()
    if runner is None:
        raise RuntimeError("You cannot stream if there is no runner set.")
    return runner.stream(item)


def submit(
    node: Callable[_P, Node[_TOutput]],
    *args: _P.args,
    **kwargs: _P.kwargs,
):
    """
    Submit a node to the executor. This will return a coroutine that you can interact with
    in whatever way using the `asyncio` framework.

    Args:
        node: The node type you would like to create
        *args: The arguments to pass to the node
        **kwargs: The keyword arguments to pass to the node

    """
    runner: Runner = get_runner()
    if runner is None:

        # in the case that a runner doesn't exists we will need to wrap it.
        # we will use the default values in the system (see config.py)
        with Runner() as runner:
            response = runner.submit(None, node, *args, **kwargs)

            return response

    p_n_id = get_parent_id()
    # but we also must update the variable so if the child node makes its own calls it is operating on the correct ID.

    # TODO think through the cancelleation logic here.
    # note the call function should be able to handle when the parent node id is none.
    f = runner.submit(p_n_id, node, *args, **kwargs)
    print(f"4. [{time.time():.3f}]")
    return f
