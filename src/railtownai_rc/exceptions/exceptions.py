import inspect
from typing import TypeVar, Generic, Callable

from ..nodes import Node
from ..run.info import ExecutionInfo
from ..run.state.request import RequestTemplate

####################################################################################################
# Node Exceptions
# I have chosen to have explicit exception subtypes instead of passing in those details as arguments to single base case
#  This was a design choice that could be challenged. I have no major issues either way.
####################################################################################################


_TOutput = TypeVar("_TOutput")


class NodeException(Exception):
    """
    An internal exception designed to be thrown in the inside of a node. The many subtypes of this node are the one
    that should be thrown in the node.
    """

    def __init__(
        self,
        node: Node,
        detail: str,
    ):
        """Creates a new instance of an exception thrown inside a node

        Args:
            node (Node): The node that caused the error
            detail (str): A detailed message about the error
        """
        message = f"Error in {node.pretty_name()}, {detail}"

        self.node = node
        self.detail = detail

        super().__init__(message)


class CompletionException(NodeException, Generic[_TOutput]):

    def __init__(
        self,
        node: Node[_TOutput],
        detail: str,
        completion_protocol: _TOutput,
    ):
        """
        The lowest level of severity of an error encountered during a node.

        It is an error which has an accompanied value which should be treated as the completion of the node.

        Example:
                class APICall(Node):
                    ...
                    def invoke(self, data_streamer: DataStream):
                        ...
                        if response.status_code == 200:
                            return str(response.json())
                        else:
                            raise CompletionException(self, "API call failed", "Unable to collect any information")

        Args:
            node: The node that caused the error
            detail: A detailed message about the error
            completion_protocol: The value that should be treated as the completion of the node
        """
        self.completion_protocol = completion_protocol
        super().__init__(node, detail)


# Note in the below 2 exceptions we implement the __init__ method so we can provide explicit docstring for users to
#  interact with.
class FatalException(NodeException):
    def __init__(self, node, detail):
        """
        The highest level of severity of an error encountered during a node. When this error is thrown, the entire
        execution of the graph will end.

        Args:
            node: The node that caused the error
            detail: A detailed description of the error.
        """

        super().__init__(node, detail)


class ResetException(NodeException):
    def __init__(self, node, detail):
        """
        The middle level of a severity of an error encountered during a node. When this error is thrown, the parent that
        called this node into action will reset and try again. This approach is called "ScorchedEarth".

        This exception is designed to be thrown when errors happen that were unexpected but do not indicate a fatal
        error in the system.

        Args:
            node: The node that caused the error
            detail: A detailed description of the error.
        """
        super().__init__(node, detail)


class MalformedFunctionException(Exception):
    """
    A special exception type that is thrown when a one of the update function or post node function in RC have
     malformed types

    This exception should be human-readable because it will be surfaced to the user.
    """

    # TODO point this exception stack trace to the bad function and not the internals.

    def __init__(self, bad_function: Callable, message: str):
        """
        Creates a new instance of a MalformedTypeException

        Args:
            bad_function (Callable): The function that lead to the error
            message (str): The descriptive message about the specific issue that occurred
        """
        super().__init__(message)
        self.bad_function = bad_function

    def __str__(self):
        return f"MalformedTypeException: {super().__str__()}\n{self.collect_function_info()}"

    def collect_function_info(self):
        """
        Converts the provided function into
        """
        name = self.bad_function.__name__
        try:
            source_code = inspect.getsource(self.bad_function)
        except OSError:
            source_code = "Unknown"
        try:
            line_number = inspect.getsourcelines(self.bad_function)[1]
        except OSError:
            line_number = "Unknown"

        source_file = inspect.getsourcefile(self.bad_function)
        if source_file is None:
            source_file = "Unknown"

        return f"({name} in {source_file} at line {line_number})\n{source_code}"
