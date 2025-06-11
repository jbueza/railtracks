import requestcompletion as rc


with rc.Runner() as run:
    result = run.run_sync(rc.library.from_function(lambda x: x + 1), 5)
