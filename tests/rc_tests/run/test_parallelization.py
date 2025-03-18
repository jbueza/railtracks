import requestcompletion as rc
import asyncio


async def timeout_node(time: float):
    await asyncio.sleep(time)
    return time


TimeoutNode = rc.library.from_function(timeout_node)


async def top_level():

    uno = rc.call(TimeoutNode, 1)
    dos = rc.call(TimeoutNode, 2)
    tres = rc.call(TimeoutNode, 3)
    quatro = rc.call(TimeoutNode, 2)
    cinco = rc.call(TimeoutNode, 1)

    return await asyncio.gather(uno, dos, tres, quatro, cinco)


TopLevel = rc.library.from_function(top_level)


def test_parallelization():
    with rc.Runner() as run:
        result = run.run_sync(TopLevel)
        assert result == [1, 2, 3, 2, 1]
