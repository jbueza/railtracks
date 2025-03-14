import asyncio
import contextvars
import time

import asyncio
import functools

def cancellation_aware(coro_func):
    @functools.wraps(coro_func)
    async def wrapper(*args, **kwargs):
        try:
            return await coro_func(*args, **kwargs)
        except asyncio.CancelledError:
            # Perform backend-specific cleanup or state management here
            print(f"{coro_func.__name__} was canceled. Performing cleanup.")
            # Example: await backend_cleanup()
            raise  # Re-raise the exception to propagate the cancellation
    return wrapper

@cancellation_aware
async def slow_print():

        await asyncio.sleep(10)
        print("hello world")





async def awaiter():
    task = asyncio.create_task(slow_print())
    await asyncio.sleep(0.5)
    task.cancel()
    try:
        return await task
    except asyncio.CancelledError:
        print("dead killed")




if __name__ == "__main__":
    asyncio.run(awaiter())
