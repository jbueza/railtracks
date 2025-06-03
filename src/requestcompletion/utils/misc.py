from ..execution.messages import (
    RequestCompletionMessage,
    RequestFinishedBase,
    RequestSuccess,
    RequestFailure,
    FatalFailure,
    RequestCreationFailure,
)


def output_mapping(result: RequestCompletionMessage):
    assert isinstance(result, (RequestFinishedBase, FatalFailure)), (
        "Expected a RequestFinishedBase message type"
    )
    result: RequestFinishedBase
    if isinstance(result, RequestSuccess):
        result: RequestSuccess
        return result.result
    elif isinstance(result, RequestFailure):
        result: RequestFailure
        raise result.error
    elif isinstance(result, FatalFailure):
        result: FatalFailure
        raise result.error
    elif isinstance(result, RequestCreationFailure):
        raise result.error
