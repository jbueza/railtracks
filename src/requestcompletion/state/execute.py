from __future__ import annotations

import asyncio
import uuid
from collections import deque


from typing import TypeVar, List, Callable, ParamSpec, Tuple, Dict

from .request import Cancelled, Failure
from ..context import parent_id

from ..nodes.nodes import Node, FatalException

from ..info import ExecutionInfo
from ..state.request import (
    RequestTemplate,
)
from ..utils.profiling import Stamp

import logging

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

        self.exception_history = deque[Exception](execution_info.exception_history)

        self.executor_config = execution_info.executor_config

        ## These are the elements which need to be created as new objects every time. They should not serialized.

        self._answer = None

        # each new instance of a state object should have its own logger.
        self.logger = logging.getLogger(__name__)

    def create_first_entry(self, start_node: Callable[_P, Node], *args: _P.args, **kwargs: _P.kwargs):
        """
        Creates the provided node in the system.

        This function will only work if the graph is empty

        Args:
            start_node: The node that you would like to start
            *args: The arguments to pass to the node
            **kwargs: The keyword arguments to pass to the node
        """
        assert len(self._request_heap.heap()) == 0, "The state must be empty to create a starting point"
        assert len(self._node_heap.heap()) == 0, "The state must be empty to create a starting point"

        created_node = start_node(*args, **kwargs)
        # we have this akward interaction with the parent_id context manager to make sure that the parent_id is set
        # this is the same logic as seen when a new node is created
        parent_id.set(created_node.uuid)

        first_stamp = self._stamper.create_stamp(
            f"Opened a new request between the start and the {created_node.pretty_name()}"
        )

        self._node_heap.update(created_node, first_stamp)
        request_id = self._request_heap.create(
            identifier="START",
            source_id=None,
            input_args=args,
            input_kwargs=kwargs,
            sink_id=created_node.uuid,
            stamp=first_stamp,
        )

        return request_id

    def add_stamp(self, message: str):
        """
        Manually adds a stamp with the provided message to the stamp generator

        Args:
            message: The message you would like to attach to the stamp

        Returns:
            None
        """
        self._stamper.create_stamp(message)

    async def execute(self, request_id: str):
        """Executes the graph starting at the provided request id."""
        # TODO: come up with a better algorithm for finding the start of execution.

        try:

            output = await asyncio.wait_for(self._run_request(request_id), timeout=self.executor_config.timeout)
            # Note that since this is the insertion requests, its output is our answer.
            self._answer = output

        except asyncio.TimeoutError:
            raise ExecutionException(
                failed_request=self._request_heap["START"],
                execution_info=self.info,
                final_exception=GlobalTimeOut(self.executor_config.timeout),
            )

    async def cancel(self, node_id: str):
        if node_id not in self._node_heap.heap():
            self.logger.warning(f"Node {node_id} not found in the heap")

        r_id = self._request_heap.get_request_from_child_id(node_id)
        self._request_heap.update(r_id, Cancelled, self._stamper.create_stamp(f"Cancelled request {r_id}"))

    async def _run_node(
        self,
        node: Node,
    ):
        """Runs the provided node and returns the output of the node."""

        return await node.invoke()

    def _create_node_and_request(
        self,
        parent_node_id: str,
        node: Callable[_P, Node],
        *args: _P.args,
        **kwargs: _P.kwargs,
    ) -> str:
        """
        Creates a node using the creator and then registers it with the registry. This will allow the register method to
        act on the node.

        Note this is the only way you can add node to the system.

        Side Effects:
        It will set the parent_id context manager variable to the new node id.

        Args:
            parent_node_id: The parent node id of the node you are creating (used for tracking of requests)
            node: The Node you would like to create
            *args: The arguments to pass to the node
            **kwargs: The keyword arguments to pass to the node

        Returns:
            The request id of the request created between parent and child.
        """

        # 1. Create the node here
        node = node(*args, **kwargs)

        # This is a critical registration step so other elements are away that we have officially created the node.
        parent_id.set(node.uuid)

        # 2. Add it to the node heap.
        sc = self._stamper.stamp_creator()
        self._node_heap.update(node, sc(f"Creating {node.pretty_name()}"))

        # 3. Attach the requests that will tied to this node.
        request_ids = self._create_new_request_set(parent_node_id, [node.uuid], [args], [kwargs], sc)

        # 4. Return the request id of the node that was created.
        return request_ids[0]

    async def call_nodes(
        self,
        parent_node_id: str,
        node: Callable[_P, Node[_TOutput]],
        *args: _P.args,
        **kwargs: _P.kwargs,
    ) -> _TOutput:
        """
        This function will handle the creation of the node and the subsequent running of the node returning the result.

        Important: If an exception was thrown during the execution of the request, it will pass through this function,
        and will be raised.

        Args:
            parent_node_id: The parent node id of the node you are calling.
            node: The node you would like to call.

        Returns:
            The output of the node that was run. It will match the output type of the child node that was run.

        """
        request_id = self._create_node_and_request(parent_node_id, node, *args, **kwargs)

        outputs: _TOutput = await self._run_request(request_id)
        return outputs

    # TODO handle the business around parent node with automatic checkpointing.
    def _create_new_request_set(
        self,
        parent_node: str,
        children: List[str],
        input_args: List[Tuple],
        input_kwargs: List[Dict[str, Tuple]],
        stamp_gen: Callable[[str], Stamp],
    ) -> List[str]:
        """
        Creates a new set of requests from the provided details. Essentially we will be creating a new request from the
        parent node to each of the children nodes. They will all share the stamp and will have a descriptive message
        attached to each of them

        Note that all the identifiers for the

        Args:
            parent_node: The identifier of the parent node which is calling the children.
            children: The list of node_ids that you would like to call.
            stamp_gen: A function that will create a new stamp of the same number.
        """

        # note it is assumed that all of the children id are valid and have already been created.
        assert all(
            [n in self._node_heap for n in children]
        ), "You cannot add a request for a node which has not yet been added"

        # to simplify we are going to create a new request for each child node with the parent as its source.
        request_ids = list(
            map(
                self._request_heap.create,
                [str(uuid.uuid4()) for _ in children],
                [parent_node] * len(children),
                children,
                input_args,
                input_kwargs,
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
        """
        Runs the request for the given request id.

        1. It will use the request to collect the identifier of the child node and then run the node.
        2. It will then handle any errors thrown during execution.
        3. It will save the new state to the state objects
        4. It will return the result of the request. (or if any error was raised during execution it will throw the error)

        Important: If an exception was thrown during the execution of the request, it will be be raised here.

        Args:
            request_id: The request you would like to run

        Returns:
            The result of the request. It will match the output type of the child node that was run.

        """
        child_node_id = self._request_heap[request_id].sink_id
        node = self._node_heap[child_node_id].node
        try:
            result = await self._run_node(node)
        except Exception as e:
            handled_error = self._handle_failed_request(request_id, e)
            result = handled_error

        stamp = self._stamper.create_stamp(f"Finished executing {node.pretty_name()}")
        self.logger.info(f"Finished running {node.pretty_name()}")

        self._request_heap.update(request_id, result, stamp)
        self._node_heap.update(node, stamp)

        if isinstance(result, Failure):
            raise result.exception

        return result

    def _handle_failed_request(self, request_id: str, exception: Exception):
        """
        Handles the provided exception for the given request identifier.

        If the given exception is a `FatalException` or if the config flag for `end_on_error` is set to be true, then
        the function will return a `ExecutionException` object wrapped in a `Failure` object.

        Otherwise, it will return a `Failure` object containing the exception that was thrown.

        Args:
            request_id: The request in which this error occurred
            exception: The exception thrown during this request.

        Returns:
            An object containing the error thrown during the request wrapped in a Failure object.

        Raises:
            ExecutionException: If the exception was a `FatalException`, or if the config flag for `end_on_error` is set
            to be true.

        """
        # before doing any handling we must make sure our exception history object is up to date.
        self.exception_history.append(exception)

        if self.executor_config.end_on_error:
            self.logger.critical(f"Encountered an Error: {exception}")
            ee = ExecutionException(
                failed_request=self._request_heap[request_id],
                execution_info=self.info,
                final_exception=exception,
            )
            return Failure(ee)

        # fatal exceptions should only be thrown if there is something seriously wrong.
        if isinstance(exception, FatalException):
            self.logger.critical(f"Fatal exception encountered: {exception}")
            ee = ExecutionException(
                failed_request=self._request_heap[request_id],
                execution_info=self.info,
                final_exception=exception,
            )
            return Failure(ee)

        # for any other error we want it to bubble up so the user can handle.
        self.logger.exception(f"Error in request {request_id}: {exception}")
        return Failure(exception)

    @property
    def info(self):
        """Returns the current state as an ExecutionInfo object."""
        return ExecutionInfo(
            node_heap=self._node_heap,
            request_heap=self._request_heap,
            stamper=self._stamper,
            exception_history=list(self.exception_history),
            executor_config=self.executor_config,
        )


class GlobalTimeOut(Exception):
    """A general exception to be thrown when a global timeout has been exceeded during execution."""

    def __init__(self, timeout: float):
        super().__init__(f"Execution timed out after {timeout} seconds")


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
