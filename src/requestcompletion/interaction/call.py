import asyncio
import warnings
import time

from typing import ParamSpec, Callable, TypeVar

from ..context import get_parent_id
from ..execution.messages import RequestCreation
from ..run import get_runner, Runner, RunnerNotFoundError

from ..nodes.nodes import Node
from ..state.request import RequestTemplate

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
    publish = get_publisher()
    parent_id = get_parent_id()

    # TODO will need to create a reference here to await for that to finish
    # first create the reference identifier

    # figure out a way to wait for the completion of this request and attach the subscriber
    request_id = RequestTemplate.generate_id()

    publish(
        RequestCreation(
            current_node_id=get_parent_id(),
            new_request_id=request_id,
            running_mode="",
            new_node_type=node,
            args=args,
            kwargs=kwargs,
        )
    )

    wait_for(request_id)

    # return once the request is complete with its value.


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
