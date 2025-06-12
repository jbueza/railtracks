from typing import ParamSpec, Callable, TypeVar, Union
from types import FunctionType

from ..run import Runner
from ..context import get_globals
from ..pubsub.messages import (
    RequestCreation,
    RequestCompletionMessage,
    RequestFinishedBase,
)

from ..pubsub.utils import output_mapping


from ..nodes.nodes import Node
from ..state.request import RequestTemplate
from ..nodes.library.function import from_function

_TOutput = TypeVar("_TOutput")
_P = ParamSpec("_P")


async def call(
    node: Callable[_P, Union[Node[_TOutput], _TOutput]],
    *args: _P.args,
    **kwargs: _P.kwargs,
):
    """
    Call a node from within a node inside the framework. This will return a coroutine that you can interact with
    in whatever way using the `asyncio` framework.

    Usage:
    ```python
    # for sequential operation
    result = await call(NodeA, "hello world", 42)

    # for parallel operation
    tasks = [call(NodeA, "hello world", i) for i in range(10)]
    results = await asyncio.gather(*tasks)
    ```

    Args:
        node: The node type you would like to create
        *args: The arguments to pass to the node
        **kwargs: The keyword arguments to pass to the node
    """
    try:
        context = get_globals()
    except KeyError:
        # If function is passed, we will convert it to a node
        if isinstance(node, FunctionType):
            node = from_function(node)
        with Runner() as runner:
            await runner.run(node, *args, **kwargs)
            return runner.info.answer

    if not context.publisher.is_running():
        raise NotImplementedError(
            "We do not support running rc.call after the runner has been created. Use `Runner.run` instead."
        )

    publisher = context.publisher

    # generate a unique request ID for this request. We need to hold this reference here because we will use it to
    # filter for its completion
    request_id = RequestTemplate.generate_id()

    def message_filter(message: RequestCompletionMessage) -> bool:
        """
        Filters out the message waiting for any messages which match the request_id of the current request.
        """
        # we want to filter and collect the message that matches this request_id
        if isinstance(message, RequestFinishedBase):
            return message.request_id == request_id
        return False

    # note we set the listener before we publish the messages ensure that we do not miss any messages
    # I am actually a bit worried about this logic and I think there is a chance of a bug popping up here.
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
