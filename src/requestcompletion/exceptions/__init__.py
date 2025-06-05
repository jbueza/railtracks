from .fatal import RCFatalException, RCNodeCreationException
from .execution import RCNodeInvocationException, RCGlobalTimeOutException, RCLLMException


class RCException(Exception):
    """
    A simple base class for all RCExceptions to inherit from.
    """

    pass



__all__ = [
    "RCFatalException",
    "RCNodeInvocationException",
    "RCGlobalTimeOutException",
    "RCLLMException",
    "RCNodeCreationException",
]
