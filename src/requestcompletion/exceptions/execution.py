from .base import RCException

from ..state.request import RequestTemplate
from ..info import ExecutionInfo

class RCNodeInvocationException(RCException):
    """
    General error for execution problems in graph, including node or orchestration failures.
    """

    def __init__(
        self,
        failed_request: RequestTemplate,
        execution_info: ExecutionInfo,
        final_exception: Exception,
    ):
        """
        Store context for post-mortem analysis.
        """
        self.failed_request = failed_request
        self.execution_info = execution_info
        self.final_exception = final_exception
        super().__init__(
            f"Execution failed for request {failed_request!r} with error {final_exception!r}. "
            f"See exception history: {self.exception_history}"
        )

    @property
    def exception_history(self):
        return getattr(self.execution_info, "exception_history", None)

class RCGlobalTimeOutException(RCException):
    """
    Raised on global timeout for whole execution.
    """
    def __init__(self, timeout: float):
        super().__init__(f"Execution timed out after {timeout} seconds")

class RCLLMException(RCException):
    """
    Raised when an error occurs during LLM invocation or completion.
    """
    pass
