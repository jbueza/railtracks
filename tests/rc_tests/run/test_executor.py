from __future__ import annotations

import asyncio
import random
import time

import requestcompletion as rc


RNGNode = rc.library.from_function(random.random)


async def many_calls(num_calls: int, parallel_calls: int):
    data = []
    for _ in range(num_calls):
        contracts = [rc.call(RNGNode) for _ in range(parallel_calls)]
        results = await asyncio.gather(*contracts)
        data.extend(results)
    return data


ManyCalls = rc.library.from_function(many_calls)


def many_calls_tester(num_calls: int, parallel_calls: int):
    with rc.Runner() as run:
        finished_result = run.run_sync(ManyCalls, num_calls, parallel_calls)

    ans = finished_result.answer

    assert isinstance(ans, list)
    assert len(ans) == num_calls * parallel_calls
    assert all([0 < x < 1 for x in ans])


def test_no_deadlock():
    num_calls = 4
    parallel_calls = 55

    many_calls_tester(num_calls, parallel_calls)


def test_small_no_deadlock():
    num_calls = 10
    parallel_calls = 15

    many_calls_tester(num_calls, parallel_calls)


def test_large_no_deadlock():
    num_calls = 45
    parallel_calls = 23

    many_calls_tester(num_calls, parallel_calls)


def test_simple_rng():
    with rc.Runner() as run:
        result = run.run_sync(RNGNode)

    assert 0 < result.answer < 1
