import requestcompletion as rc

import time


def timeout_node(_t: float):
    print(f"Sleeping for {_t}")
    time.sleep(_t)
    return _t


TimeoutNode = rc.library.from_function(timeout_node)


def future_parallel():

    uno = rc.submit(TimeoutNode, 1)
    dos = rc.submit(TimeoutNode, 2)
    tres = rc.submit(TimeoutNode, 3)
    quatro = rc.submit(TimeoutNode, 2)
    cinco = rc.submit(TimeoutNode, 1)

    finished_results = [f.result() for f in [uno, dos, tres, quatro, cinco]]

    return finished_results


FutureParallel = rc.library.from_function(future_parallel)


with rc.Runner() as run:
    result = run.run_sync(FutureParallel)
    assert result.answer == [1, 2, 3, 2, 1]
