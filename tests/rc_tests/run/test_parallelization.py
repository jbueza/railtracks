import concurrent.futures
import threading

import pytest
import requestcompletion as rc
import asyncio
import time


def timeout_node(_t: float):
    time.sleep(_t)
    return _t


async def timeout_node_async(_t: float):
    await asyncio.sleep(_t)
    return _t


TimeoutNode = rc.library.from_function(timeout_node)
TimeoutNodeAsync = rc.library.from_function(timeout_node_async)


async def top_level_async():

    uno = rc.call(TimeoutNodeAsync, 1)
    dos = rc.call(TimeoutNodeAsync, 2)
    tres = rc.call(TimeoutNodeAsync, 3)
    quatro = rc.call(TimeoutNodeAsync, 2)
    cinco = rc.call(TimeoutNodeAsync, 1)

    result = await asyncio.gather(uno, dos, tres, quatro, cinco)

    return result


async def top_level():

    uno = rc.call(TimeoutNode, 1)
    dos = rc.call(TimeoutNode, 2)
    tres = rc.call(TimeoutNode, 3)
    quatro = rc.call(TimeoutNode, 2)
    cinco = rc.call(TimeoutNode, 1)

    result = await asyncio.gather(uno, dos, tres, quatro, cinco)

    return result


TopLevelAsync = rc.library.from_function(top_level_async)
TopLevel = rc.library.from_function(top_level)


# by leveraging timeout we can ensure that the test is properly using parallelization
@pytest.mark.timeout(4)
def test_regular_style_parallel():
    with rc.Runner() as run:
        result = run.run_sync(TopLevel)
        assert result.answer == [1, 2, 3, 2, 1]


@pytest.mark.timeout(4)
def test_async_style_parallel():
    with rc.Runner() as run:
        result = run.run_sync(TopLevelAsync)
        assert result.answer == [1, 2, 3, 2, 1]


@pytest.mark.timeout(4)
@pytest.mark.asyncio
async def test_async_style_parallel_2():
    with rc.Runner() as run:
        result = await run.run(TopLevelAsync)
        assert result.answer == [1, 2, 3, 2, 1]


def future_parallel():
    print(f"Future running in {threading.get_ident()}")

    uno = rc.submit(TimeoutNode, 1)
    dos = rc.submit(TimeoutNode, 2)
    tres = rc.submit(TimeoutNode, 3)
    quatro = rc.submit(TimeoutNode, 2)
    cinco = rc.submit(TimeoutNode, 1)

    finished_results = [f.result() for f in [uno, dos, tres, quatro, cinco]]

    return finished_results


FutureParallel = rc.library.from_function(future_parallel)


@pytest.mark.timeout(4)
def test_futures_parallel():
    with rc.Runner() as run:
        result = run.run_sync(FutureParallel)
        assert result.answer == [1, 2, 3, 2, 1]
