from __future__ import annotations

import asyncio
import uuid
from collections import deque


from typing import TypeVar, List, Callable, ParamSpec

from ..run import parent_id
from ...exceptions import (
    ResetException,
    FatalException,
    CompletionException,
)

from ...nodes import Node

from src.requestcompletion.context import BaseContext
from ..info import ExecutionInfo
from src.requestcompletion.state.request import (
    DeadRequestException,
    RequestTemplate,
)
from src.requestcompletion.tools import Stamp

import logging


_TContext = TypeVar("_TContext", bound=BaseContext)
_TOutput = TypeVar("_TOutput")
_P = ParamSpec("_P")


class RCState:
    """
    RCState is an internal RC object used to manage state of the request completion system. This object has a couple of
    major functions:
    1. It allows you to create a new state object every time you want to run the system.
    2. It allows you to invoke the graph at a given node and will handle the execution of the graph.
    3. It will handle all the exceptions that are thrown during the execution of the graph.
    4. It will handle the creation of new requests and the management of the state of the nodes.
    5. It will save all the details in the object so that you can access them later.
    6. Simple logging of action completed in the system.

    The object is designed to be a large state object that contains all important details about the running of the
    system during execution. It can be accessed after run, to collect important details that will aid debugging and
    allow for retrospective analysis of the system.
    """

    # the main role of this object is to augment the executor object with all the things it needs to track state as the
    #  the graph runs.
    def __init__(self, execution_info: ExecutionInfo):

        self._node_heap = execution_info.node_heap
        self._request_heap = execution_info.request_heap
        self._stamper = execution_info.stamper

        self.subscriber = execution_info.subscriber

        self.exception_history = deque[Exception](execution_info.exception_history)

        self.executor_config = execution_info.executor_config

        ## These are the elements which need to be created as new objects every time. They should not serialized.

        self._answer = None

        # each new instance of a state object should have its own logger.
        self.logger = logging.getLogger(__name__)

    def create_first_entry(self, start_node: Node):
        """
        Creates the first entry in the system. This will create the first request and node in the system.

        Note the system will not allow you to create a new entry if there is already an entry in the system.
        Args:
            start_node: The node that you would like to start
        """
        assert len(self._request_heap.heap()) == 0, "The state must be empty to create a starting point"
        assert len(self._node_heap.heap()) == 0, "The state must be empty to create a starting point"

        first_stamp = self._stamper.create_stamp(
            f"Opened a new request between the start and the {start_node.pretty_name()}"
        )

        self._node_heap.update(start_node, first_stamp)
        self._request_heap.create(
            identifier="START",
            source_id=None,
            sink_id=start_node.uuid,
            stamp=first_stamp,
        )

    def add_stamp(self, message: str):
        """
        Manually adds a stamp to the stamp generator in this object.

        Args:
            message: The message you would like to attach to the stamp

        Returns:
            None
        """
        self._stamper.create_stamp(message)

    # TODO make this a more general invoke method. you should not have to pass in the start node.
    #  it should be able to look at state and infer the next task.
    def invoke(
        self,
        start_node: Node,
    ):
        """
        This function will run the provided node and will automatically handle any calls to other nodes that are made
        during the execution of the node.

        Once this function has returned, the state of the object will update. You can access any details you would like
        to by accessing the components of the object.

        This should go without saying but this function creates a large amount of side effects, directly interacting
        with the state of the object.

        Args:
            start_node: The node which you would like to start the execution of the graph from.

        Returns:
            None

        """

        self.execute(start_node)

    async def execute(self, start_node: Node):
        # TODO: come up with a better algorithm for finding the start of execution.

        try:
            output = await asyncio.wait_for(self._run_node(start_node), timeout=self.executor_config.timeout)

            # before exit we must update the state objects one last time
            # this is a special case becuase in all other situations we call `_run_requests` and it handles the
            # updating of the state objects.
            stamp = self._stamper.create_stamp(f"Finished executing {start_node.pretty_name()}")
            self.logger.info(f"Finished running {start_node.pretty_name()}")
            self._request_heap.update("START", output, stamp)
            self._node_heap.update(start_node, stamp)
            self._answer = output
        except asyncio.TimeoutError:

            raise ExecutionException(
                failed_request=self._request_heap["START"],
                execution_info=self.info,
                final_exception=GlobalTimeOut(self.executor_config.timeout),
            )
        ### if the initial request throws a scorched earth exception will have to handle it here.
        except ScorchedEarthException as e:
            next_node = self._preform_scorched_earth(e.failed_request_id)
            if next_node is None:
                raise AssertionError(
                    "There is no possible reason for this to happen. The first request only has" "one line of execution"
                )
            # note we can't just pull the one from memory because its state could have changed during execution,
            #  so we need to hard revert first

            await self.execute(next_node)

    async def _run_node(
        self,
        node: Node,
    ):
        """
        This function is responsible for running a single node. It will run the node and then return the output of it.

        This node could have generators which will trigger the creation of other nodes. This function will handle this
        and spawn new processes to handle the new nodes.scp
        """
        # TODO verify that this is working as expected
        # right before a node is run we register the id of the parent so it can be accessed if the node ever calls `.run`
        parent_id.set(node.uuid)
        return await node.invoke()

    def _create_node(self, parent_node_id: str, node: Node) -> str:
        """
        Creates a node using the creator and then registers it with the registry. This will allow the register method to
        act on the node.

        Note this is the only way you can add node to the system.

        Args:
            node_creator: The function that will create the node
            *args: The arguments to pass to the node creator
            **kwargs: The keyword arguments to pass to the node

        Returns:
            A NodeTemplate object containing the node that was created
        """
        # 1. collect the current parent node via context

        # 2. Attach the registry components (i.e. hook for node creation and node invocation)
        assert node.uuid not in self._node_heap, f"Node {node.uuid} has already been created"
        sc = self._stamper.stamp_creator()
        self._node_heap.update(node, sc(f"Creating {node.pretty_name()}"))
        request_ids = self._create_new_request_set(parent_node_id, [node.uuid], sc)
        # only returns after the node was successfully added.
        return request_ids[0]

    async def call_nodes(
        self,
        node: Node[_TOutput],
    ) -> _TOutput:
        """
        This function will handle the creation of new requests and the running of the new requests. It will return the
        results of the requests.

        Note the returned list will match the order of the input list.

        Args:
            parent_node: The node that is calling the other nodes.
            node_ids: The list of nodes, you would like to call
            executor: A executor used for parallelization of the requests.

        Returns:
            A list of the response from the nodes, in the order matching the input list.

        """
        parent_node_id = parent_id.get()  # TODO get the parent node id from the context
        request_id = self._create_node(parent_node_id, node)

        outputs: _TOutput = await self._run_request(request_id)
        return outputs

    def _preform_scorched_earth(self, failed_request_id: str):
        """
        This function will handle the provided scorched earth exception triggering the full sequnce of events around it

        Specially, if the scorched earth exception is raised in the middle of the execution of a node we will follow
        this procedure:

        1. Revert the heap such that all siblings of the failed request are killed.
        2. Revert the nodes connected to those requests to prevent them from being run again.
        3. Return back the node we started on get return
        https://www.notion.so/railtownai/Error-Handling-Logic-78237175fd05464fab5cefa2122c8aa1?pvs=4#428cefb545bd46de9af97bc3e25736e8

        :param failed_request_id: The id of the request that the scorched earth exception was raised on

        Returns:
            The parent node after all the details have been reverted. This is the next node to be executed. It will
             return none if some other request has already made things none.
        """

        # 1. interface with the request heap to kill all the requests that we needed to kill
        try:
            all_requests, updated_stamp, fresh_request_id = self._request_heap.revert_heap(failed_request_id)
        except DeadRequestException:
            # the request we tried to fail has already been failed
            return

        # 2. figure out what are all the dead nodes
        all_nodes = set()
        for r in all_requests:
            if r.source_id is not None:
                all_nodes.add(r.source_id)
            all_nodes.add(r.sink_id)

        self._node_heap.hard_revert(all_nodes, updated_stamp)

        new_node_id = self._request_heap[fresh_request_id].sink_id

        return self._node_heap[new_node_id].node

    # Note it may seem weird to have to pass in the full state of the parent_node.
    #  this is going to be relevant when do more advanced automated checkpointing and recovery allowing us to restart
    #  etc.
    def _create_new_request_set(
        self,
        parent_node: str,
        children: List[str],
        stamp_gen: Callable[[str], Stamp],
    ) -> List[str]:
        """
        Creates a new set of requests from the provided details. Essentially we will be creating a new request from the
        parent node to each of the children nodes. They will all share the stamp and will have a descriptive message
        attached to each of them

        Note that all the identifiers for the

        Args:
            parent_node: The node that is calling the other nodes.
            children: The list of node_ids that you would like to call.
            stamp_gen: A function that will create a new stamp of the same number.
            executor: A executor used for parallelization of the requests.
        """
        # note it is assumed that all of the children id are valid and have already been created.
        assert all(
            [n in self._node_heap for n in children]
        ), "You cannot add a request for a node which has not yet been added"
        request_ids = list(
            map(
                self._request_heap.create,
                [str(uuid.uuid4()) for _ in children],
                [parent_node] * len(children),
                children,
                [
                    stamp_gen(
                        f"Adding request between {self._node_heap.id_type_mapping[parent_node]} and {self._node_heap.id_type_mapping[n]}"
                    )
                    for n in children
                ],
            )
        )

        return request_ids

    async def _run_request(self, request_id: str):
        child_node_id = self._request_heap[request_id].sink_id
        node = self._node_heap[child_node_id].node
        try:
            result = self._run_node(node)
        except FatalException as e:
            self.logger.critical(
                f"Fatal exception encountered: {e}. This is likely a problem with the framework, and not your fault."
            )
            raise e
        except Exception as e:
            self._handle_failed_request(request_id, e)
            result = e

        stamp = self._stamper.create_stamp(f"Finished executing {node.pretty_name()}")
        self.logger.info(f"Finished running {node.pretty_name()}")

        self._request_heap.update(request_id, result, stamp)
        self._node_heap.update(node, stamp)

        return result

    def _handle_failed_request(self, request_id: str, exception: Exception):
        """
        Error handling logic that takes in any node exception and handles it according to the logic presented in the
        notion documentation.

        Critically there are 3 different types of errors which are handled as follows:
        1.`FatalException`: This is a fatal error that will stop the execution of the graph. If this exception is raised
        we will propagate the error up as an Execution Exception.
        2. `ResetException`: This is a non fatal error that will trigger the scorched earth protocol.
        We will pass up a `ScorchedEarthException` which will be handled by the parent node.
        3. `CompletionException`: This is a special exception that is raised when a node would like to return a
        predefined completion message instead of an error. In this case we will return the completion protocol and not
        throw an error.

        There are a couple of other major things that this function will also check for:

        - If we have gone over our maximum number of exceptions it will trigger an `ExecutionException`
        - If we have turned off our scorched earth protocol it will throw an `ExecutionException`
        - If an unknown exception is provided it will be thrown up the chain to be handled by above modules.

        Args:
            request_id: The request in which this error occurred
            exception: The exception thrown during this request.

        Returns:
            The completion protocol if the exception was a `CompletionException` otherwise it will throw an exception

        Raises:
            ExecutionException: If the exception was a `FatalException`, the number of exceptions has exceeded the
            provided param, or you have turned off scorched earth protocol and a scorched earth exception had been
            raised.
            ScorchedEarthException: If the exception was a `ResetException` and scorched earth has been turned on.

        """
        self.exception_history.append(exception)

        if isinstance(exception, FatalException):
            self.logger.critical(f"Fatal exception encountered: {exception}")
            raise ExecutionException(
                failed_request=self._request_heap[request_id],
                execution_info=self.info,
                final_exception=exception,
            )

        if len(self.exception_history) >= self.executor_config.global_num_retries:
            self.logger.critical(f"Encountered our {len(self.exception_history)} exception: {exception}")
            raise ExecutionException(
                failed_request=self._request_heap[request_id],
                execution_info=self.info,
                final_exception=GlobalRetriesExceeded(self.executor_config.global_num_retries),
            )

        # now lets check if there is completion protocol
        if isinstance(exception, CompletionException):
            self.logger.warning(f"Completion protocol encountered: {exception}")
            return exception.completion_protocol

        # If this flag is not set then we won't want to use scorched earth
        if not self.executor_config.retry_upstream_request_on_failure:
            self.logger.critical(
                f"Non fatal exception encountered but config indicates it should be thrown: {exception}"
            )
            raise ExecutionException(
                failed_request=self._request_heap[request_id],
                execution_info=self.info,
                final_exception=exception,
            )

        if isinstance(exception, ResetException):
            self.logger.error(f"Non fatal exception encountered (completing scorched earth protocol): {exception}")
            # Now we can raise the special ScorchedEarthException so it can be handled properly.
            raise ScorchedEarthException(request_id, exception)

        # note if there is an unknown exception it should be re-raised here.
        self.logger.critical(f"A unknown error was encountered: {exception}")
        raise exception

    @property
    def info(self):
        return ExecutionInfo(
            node_heap=self._node_heap,
            request_heap=self._request_heap,
            stamper=self._stamper,
            context=self._context,
            subscriber=self.subscriber,
            exception_history=list(self.exception_history),
            executor_config=self.executor_config,
        )


class ScorchedEarthException(Exception):
    """
    A special exception to be thrown to allow specific information about a reset exception to passed from the child
    request to the parent.
    """

    def __init__(self, failed_request_id: str, original_exception: ResetException):
        """
        Creates a new instance of a ScorchedEarthException

        Args:
            failed_request_id: The request id of the one that failed
            original_exception: The ResetException which triggered
        """
        self.original_exception = original_exception
        self.failed_request_id = failed_request_id

    def __str__(self):
        return f"Scorched Earth Exception in {self.failed_request_id[:5] if len(self.failed_request_id) > 5 else self.failed_request_id}: {self.original_exception}"


class GlobalTimeOut(Exception):
    """A general exception to be thrown when a global timeout has been exceeded during execution."""

    def __init__(self, timeout: float):
        super().__init__(f"Execution timed out after {timeout} seconds")


class GlobalRetriesExceeded(Exception):
    """A general exception to be thrown when the number of global retries has been exceeded during execution."""

    def __init__(self, global_retries: int):
        super().__init__(f"Execution timed out after {global_retries} retries were tried.")


class ExecutionException(Exception):
    """A general exception thrown when an error occurs during the execution of the graph."""

    def __init__(
        self,
        failed_request: RequestTemplate,
        execution_info: ExecutionInfo,
        final_exception: Exception,
    ):
        """
        Creates a new instance of an ExecutionException

        Args:
            failed_request: The request that failed during the execution that triggered this exception
            final_exception: The last exception that was thrown during the execution (this is likely the one that cause the execution exception)
        """
        self.failed_request = failed_request
        self.execution_info = execution_info
        self.final_exception = final_exception
        super().__init__(
            f"The final nodes exception was {final_exception}, in the failed request {failed_request}."
            f"A complete history of errors seen is seen here: \n {self.exception_history}"
        )

    @property
    def exception_history(self):
        return self.execution_info.exception_history


async def some_func():
    return await api_call()
