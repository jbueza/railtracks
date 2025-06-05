import asyncio

from typing import (
    List,
    Tuple,
    Iterable,
    Iterator,
    ParamSpec,
    Callable,
    Any,
    Dict,
    TypeVar,
)

from .call import call
from ..nodes.nodes import Node

_P = ParamSpec("_P")
_TOutput = TypeVar("_TOutput")


async def batch(
    node: Callable[..., Node[_TOutput]],
    *iterables: Iterable[Any],
    return_exceptions: bool = True,
):
    """
    Complete a node over multiple iterables, allowing for parallel execution.

    Note the results will be returned in the order of the iterables, not the order of completion.

    If one of the nodes returns an exception, the thrown exception will included as a response.

    Args:
        node: The node type to create.
        *iterables: The iterables to map the node over.
        return_exceptions: If True, exceptions will be returned as part of the results.
            If False, exceptions will be raised immediately and you will lose access to the results.
            Defaults to true.

    Returns:
        An iterable of results from the node.
    """
    contracts = [call(node, *args) for args in zip(*iterables)]

    results = await asyncio.gather(*contracts, return_exceptions=return_exceptions)
    return results
