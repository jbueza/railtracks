import time

import pytest
import requestcompletion as rc


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "timeout_config, expected, buffer",
    [
        ([1, 2, 3, 2, 1], 3.25, 0.5),
        ([1, 5, 1], 5.25, 0.5),
        ([1] * 35, 1.25, 0.5),
        ([2] * 100 + [3] * 50, 3.25, 0.5),
        ([10], 10.25, 0.5),
    ],
)
async def test_parallel_calls(parallel_node, timeout_config, expected, buffer):

    with rc.Runner(
        executor_config=rc.ExecutorConfig(
            logging_setting="NONE",
        )
    ) as runner:
        start_time = time.time()
        results = await runner.run(parallel_node, expected=expected, buffer=buffer)
        assert abs(time.time() - start_time - expected) < buffer
        assert results.answer == timeout_config


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "timeout_config, expected, buffer",
    [
        ([1, 2, 3, 2, 1], 3.25, 0.5),
        ([1, 5, 1], 5.25, 0.5),
        ([1] * 35, 1.25, 0.5),
        ([2] * 100 + [3] * 50, 3.25, 0.5),
        ([10], 10.25, 0.5),
    ],
)
def test_parallel_calls_sync(parallel_node, timeout_config, expected, buffer):
    with rc.Runner(
        executor_config=rc.ExecutorConfig(
            logging_setting="NONE",
        )
    ) as runner:
        start_time = time.time()
        results = runner.run_sync(parallel_node, expected=expected, buffer=buffer)
        assert abs(time.time() - start_time - expected) < buffer
        assert results.answer == timeout_config
