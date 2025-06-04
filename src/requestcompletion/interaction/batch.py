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
):
    """
    Complete a node over multiple iterables, allowing for parallel execution.

    Note the results will be returned in the order of the iterables, not the order of completion.

    Args:
        node: The node type to create.
        *iterables: The iterables to map the node over.

    Returns:
        An iterable of results from the node.
    """
    contracts = [call(node, *args) for args in zip(*iterables)]
    return await asyncio.gather(*contracts)
