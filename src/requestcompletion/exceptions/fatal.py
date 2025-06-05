from . import RCException


class RCFatalException(RCException):
    pass


class RCNodeCreationException(RCException):
    """
    Raised during node creation/validation before any execution begins.
    For example, bad config, missing required parameters, or structural errors.
    """
    pass
