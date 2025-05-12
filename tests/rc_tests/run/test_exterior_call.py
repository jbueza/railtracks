import requestcompletion as rc
import random
import pytest

RNGNode = rc.library.from_function(random.random)


@pytest.mark.asyncio
async def test_runner_call_basic():
    response = await rc.call(RNGNode)
    assert isinstance(response, float), "Expected a float result from RNGNode"


# TODO write tests for accessing state and setting state after and before the fact.
