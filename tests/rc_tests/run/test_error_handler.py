from __future__ import annotations

import pytest
import random

import requestcompletion as rc

from requestcompletion.state.request import Failure

RNGNode = rc.library.from_function(random.random)


def test_simple_request():
    with rc.Runner() as run:
        result = run.run_sync(RNGNode)

    assert isinstance(result.answer, float)
    assert 0 < result.answer < 1


class TestError(Exception):
    pass


async def error_thrower():
    raise TestError("This is a test error")


ErrorThrower = rc.library.from_function(error_thrower)


def test_error():
    with rc.Runner() as run:
        with pytest.raises(TestError):
            run.run_sync(ErrorThrower)


async def error_handler():
    try:
        answer = await rc.call(ErrorThrower)
    except TestError as e:
        return "Caught the error"


ErrorHandler = rc.library.from_function(error_handler)


def test_error_handler():
    with rc.Runner() as run:
        result = run.run_sync(ErrorHandler)
    assert result.answer == "Caught the error"


async def error_handler_with_retry(retries: int):
    for _ in range(retries):
        try:
            return await rc.call(ErrorThrower)
        except TestError as e:
            continue

    return "Caught the error"


ErrorHandlerWithRetry = rc.library.from_function(error_handler_with_retry)


def test_error_handler_with_retry():
    for num_retries in range(5, 15):
        with rc.Runner() as run:
            result = run.run_sync(ErrorHandlerWithRetry, num_retries)

        assert result.answer == "Caught the error"
        i_r = result.request_heap.insertion_request

        children = result.request_heap.children(i_r.sink_id)
        assert len(children) == num_retries

        for r in children:
            assert isinstance(r.output, Failure)
            assert isinstance(r.output.exception, TestError)

        assert all([isinstance(e, TestError) for e in result.exception_history])
        assert len(result.exception_history) == num_retries


async def error_handler(num_calls: int, parallel_calls: int):
    data = []
    for _ in range(num_calls):
        contracts = [rc.call(ErrorThrower) for _ in range(parallel_calls)]
        results = await asyncio.gather(*contracts)
        data.extend(results)
    return data


def test_crazy_errors():
    num_calls = 10
    parallel_calls = 5
    i_node = CallNode(
        num_calls,
        parallel_calls,
        lambda: CompletionProtocolNode("hello world"),
    )

    finished_result = run(i_node, executor_config=ExecutorConfig(global_num_retries=350, timeout=250))

    assert isinstance(finished_result.answer, list)
    assert len(finished_result.answer) == num_calls * parallel_calls
    assert all([x == "hello world" for x in finished_result.answer])


def test_even_crazier_errors():
    i_node = CallNode(10, 50, lambda: RNGNode())

    finished_result = run(
        i_node,
        executor_config=ExecutorConfig(global_num_retries=10000, timeout=250, workers=290),
    )

    assert isinstance(finished_result.answer, list)
    assert len(finished_result.answer) == 10 * 50
    assert all([0 <= x <= 1 for x in finished_result.answer])


def test_time_out():
    i_node = TimeoutNode(5)

    with pytest.raises(ExecutionException) as err:
        run(i_node, executor_config=ExecutorConfig(timeout=1))

    assert isinstance(err.value.final_exception, GlobalTimeOut)
    assert len(err.value.exception_history) == 0


def test_passed_time_out():
    i_node = TimeoutNode(1)

    finished_result = run(i_node, executor_config=ExecutorConfig(global_num_retries=10, timeout=10))

    assert finished_result.answer is None


def test_complicated_graph_structure():
    i_node = CallNode(3, 5, lambda: TimeoutNode(1))

    try:
        run(i_node, executor_config=ExecutorConfig(timeout=5, global_num_retries=10000))
    except ExecutionException as err:
        assert isinstance(err.final_exception, GlobalTimeOut)


def test_complicated_graph_structure_2():
    i_node = CallNode(
        3,
        3,
        lambda: CompletionProtocolNode("Hello World"),
    )

    try:
        run(i_node, executor_config=ExecutorConfig(timeout=10, global_num_retries=10))
    except ExecutionException as err:
        assert isinstance(err.final_exception, GlobalRetriesExceeded)
