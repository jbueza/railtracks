import asyncio
import concurrent.futures
import logging
import threading
import warnings
from typing import TypeVar, ParamSpec, Callable, Coroutine, Any

import deprecated

from .config import ExecutorConfig
from .execution.coordinator import Coordinator
from .execution.execution_strategy import ThreadedExecutionStrategy, AsyncioExecutionStrategy
from .execution.messages import RequestCompletionMessage, RequestCreation, RequestFinishedBase, FatalFailure
from .execution.publisher import RCPublisher
from .execution.subscriber import stream_subscriber
from .utils.misc import output_mapping
from .utils.stream import DataStream, Subscriber
from .nodes.nodes import Node
from .utils.logging.config import prepare_logger, detach_logging_handlers


from .info import (
    ExecutionInfo,
)
from .state.state import RCState

from .context import (
    streamer,
    config,
    register_globals,
    ThreadContext,
    get_globals,
    delete_globals,
)

_TOutput = TypeVar("_TOutput")
_P = ParamSpec("_P")


class RunnerCreationError(Exception):
    """
    A basic exception to representing when a runner is created when one already exists.
    """

    pass


class RunnerNotFoundError(Exception):
    """
    A basic exception to representing when no runner can be found
    """

    pass


class Runner:
    """
    The main class used to run flows in the Request Completion framework.

    Example Usage:
    ```python
    import requestcompletion as rc

    with rc.Runner() as run:
        result = run.run_sync(RNGNode)
    ```
    """

    # singleton pattern
    _instance = None

    def __init__(
        self,
        subscriber: Callable[[str], None] = None,
        executor_config: ExecutorConfig = None,
    ):

        # first lets read from defaults if nessecary for the provided input config
        if executor_config is None:
            saved_config = config.get()
            if saved_config is None:
                executor_config = ExecutorConfig()
            else:
                print(f"Using saved executor config {saved_config.end_on_error}")
                executor_config = saved_config

        if subscriber is None:
            saved_subscriber = streamer.get()
            if saved_subscriber is None:
                subscriber = None
            else:
                subscriber = saved_subscriber

        # TODO see issue about logger
        prepare_logger(
            setting=executor_config.logging_setting,
        )
        self.publisher: RCPublisher[RequestCompletionMessage] = RCPublisher()

        register_globals(ThreadContext(publisher=self.publisher, parent_id=None))

        executor_info = ExecutionInfo.create_new()
        self.coordinator = Coordinator(execution_modes={"async": AsyncioExecutionStrategy()})
        self.rc_state = RCState(executor_info, executor_config, self.coordinator)
        self.subscriber = subscriber

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._close()

    async def prepare(self):
        """
        Prepares the publisher and attaches
        """

        await self.publisher.start()
        self.coordinator.start(self.publisher)
        self.setup_subscriber()

    def setup_subscriber(self):
        """
        Prepares and attaches the saved subscriber to the publisher attached to this runner.
        """

        if self.subscriber is not None:
            self.publisher.subscribe(stream_subscriber(self.subscriber))

    async def _run_base(
        self,
        start_node: Callable[_P, Node] | None = None,
        *args: _P.args,
        **kwargs: _P.kwargs,
    ):
        await self.prepare()

        if not self.rc_state.is_empty:
            raise RuntimeError("The run function can only be used to start not in the middle of a run.")

        start_request_id = "START"

        def message_filter(item: RequestCompletionMessage) -> bool:

            # we want to filter and collect the message that matches this request_id
            matches_request_id = isinstance(item, RequestFinishedBase) and item.request_id == start_request_id
            fatal_failure = isinstance(item, FatalFailure)

            return matches_request_id or fatal_failure

        fut = self.publisher.listener(message_filter, output_mapping)

        await self.publisher.publish(
            RequestCreation(
                current_node_id=None,
                new_request_id=start_request_id,
                running_mode="async",
                new_node_type=start_node,
                args=args,
                kwargs=kwargs,
            )
        )

        return await fut

    def run_sync(self, start_node: Callable[_P, Node] | None = None, *args: _P.args, **kwargs: _P.kwargs):
        """Runs the provided node synchronously."""
        asyncio.run(self._run_base(start_node, *args, **kwargs))

        return self.rc_state.info

    def _close(self):
        self.rc_state.shutdown()
        detach_logging_handlers()
        delete_globals()
        # by deleting all of the state variables we are ensuring that the next time we create a runner it is fresh

    @property
    def info(self) -> ExecutionInfo:
        """
        Returns the current state of the runner.

        This is useful for debugging and viewing the current state of the run.
        """
        return self.rc_state.info

    async def run(
        self,
        start_node: Callable[_P, Node] | None = None,
        *args: _P.args,
        **kwargs: _P.kwargs,
    ):
        """Runs the rc framework with the given start node and provided arguments."""

        # relevant if we ever want to have future support for optional start nodes
        fut = self._run_base(start_node, *args, **kwargs)

        await fut
        return self.rc_state.info

    async def cancel(self, node_id: str):
        raise NotImplementedError(
            "Currently we do not support cancelling nodes. Please contact Logan to add this feature."
        )
        # collects the parent id of the current node that is running that is gonna get cancelled
        await self.rc_state.cancel(node_id)

    # TODO implement this method and any additional logic in rc_state that is required.
    def from_state(self, executor_info: ExecutionInfo):
        raise NotImplementedError(
            "Currently we do not support running from a state object. Please contact Logan to add this feature."
        )
        # self.rc_state = RCState(executor_info)


def set_config(executor_config: ExecutorConfig):
    """
    Sets the executor config for the current runner.
    """
    try:
        get_globals()
    except KeyError:
        warnings.warn(
            "The executor config is being set after the runner has been created, changes will not be propagated to the current runner"
        )

    config.set(executor_config)


def set_streamer(subscriber: Callable[[str], None]):
    """
    Sets the data streamer for the current runner.
    """
    try:
        get_globals()
    except KeyError:
        warnings.warn(
            "The data streamer is being set after the runner has been created, changes will not be propagated to the current runner"
        )

    streamer.set(subscriber)
