import asyncio
from typing import Union, Coroutine, Callable, Any

from .messages import Streaming, RequestCompletionMessage


def stream_subscriber(
    sub_callback: Callable[[Any], Union[None, Coroutine[None, None, None]]],
) -> Callable[[RequestCompletionMessage], Coroutine[None, None, None]]:
    """
    Converts the basic streamer callback into a subscriber handler designed to take in `RequestCompletionMessage`
    """

    async def subscriber_handler(item: RequestCompletionMessage):
        if isinstance(item, Streaming):
            result = sub_callback(item.streamed_object)
            if asyncio.iscoroutine(result):
                await result

    return subscriber_handler
