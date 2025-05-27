from ..execution.messages import (
    RequestCompletionMessage,
    RequestFinishedBase,
    RequestSuccess,
    RequestFailure,
)

def output_mapping(result: RequestCompletionMessage) -> RequestFinishedBase:
    assert isinstance(result, RequestFinishedBase), "Expected a RequestFinishedBase message type"
    result: RequestFinishedBase
    if isinstance(result, RequestSuccess):
        result: RequestSuccess
        return result.result
    elif isinstance(result, RequestFailure):
        result: RequestFailure
        raise result.error