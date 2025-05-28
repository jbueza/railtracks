import asyncio
import warnings
import time

from typing import ParamSpec, Callable, TypeVar

from ..context import get_globals
from ..execution.messages import (
    RequestCreation,
    RequestCompletionMessage,
    RequestFinishedBase,
    RequestSuccess,
    RequestFailure,
)

from ..utils.misc import output_mapping


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
    context = get_globals()
    publisher = context.publisher

    # TODO will need to create a reference here to await for that to finish
    # first create the reference identifier

    # figure out a way to wait for the completion of this request and attach the subscriber
    request_id = RequestTemplate.generate_id()

    def message_filter(message: RequestCompletionMessage) -> bool:
        # we want to filter and collect the message that matches this request_id
        if isinstance(message, RequestFinishedBase):
            return message.request_id == request_id
        return False

    # TODO ensure we don't miss any messages here (e.g. what if the request returns really fast)
    f = publisher.listener(message_filter, output_mapping)

    await publisher.publish(
        RequestCreation(
            current_node_id=context.parent_id,
            new_request_id=request_id,
            running_mode="async",
            new_node_type=node,
            args=args,
            kwargs=kwargs,
        )
    )

    return await f


def stream(item: str):
    # TODO implement streaming functionality
    publisher = get_globals().publisher
    publisher.publish("hello world")
