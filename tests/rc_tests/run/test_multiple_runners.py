import concurrent.futures
import requestcompletion as rc
import pytest

from tests.rc_tests.fixtures.nodes import RNGNode


def test_multiple_runners():
    with concurrent.futures.ThreadPoolExecutor() as executor:

        def run_rng():
            with rc.Runner() as run:
                result = run.run_sync(RNGNode)

        mapped_results = executor.map(run_rng, [] * 5)

        for m in mapped_results:
            assert isinstance(m, float), "Expected a float result from RNGNode"


@pytest.mark.asyncio
async def test_multiple_runners_2():
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for _ in range(5):
            with rc.Runner() as run:
                result = await run.run(RNGNode)


@pytest.mark.asyncio
async def test_multiple_runners_2():
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for _ in range(5):
            with rc.Runner() as run:
                result = run.run_sync(RNGNode)
