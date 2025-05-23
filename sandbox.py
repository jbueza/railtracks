import asyncio
import concurrent.futures
import threading
import time
import warnings
import requestcompletion as rc


async def async_function():
    await asyncio.sleep(0.1)
    return "Async result"


def wrapped_async_function():
    asyncio.run(async_function())


def sync_function():
    time.sleep(0.1)
    return "Sync result"


async def test_async():
    for i in iterations:
        start_time = time.time()
        futures = [async_function() for _ in range(i)]
        await asyncio.gather(*futures)
        end_time = time.time()
        print(f"Async execution took {end_time - start_time} seconds for {i} iterations.")


if __name__ == "__main__":
    iterations = [10, 100, 1000]
    # first lets see how long it takes to run wrapped async function
    for i in iterations:
        start = time.time()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(wrapped_async_function) for _ in range(i)]
            for item in concurrent.futures.as_completed(futures):
                pass

        end = time.time()
        print(f"Threaded async execution took {end - start} seconds for {i} iterations.")

    print("-" * 50)
    # now lets see how long it takes to run sync function
    for i in iterations:
        start = time.time()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(sync_function) for _ in range(i)]
            for item in concurrent.futures.as_completed(futures):
                pass

        end = time.time()
        print(f"Threaded sync execution took {end - start} seconds for {i} iterations.")

    print("-" * 50)
    # now lets see how long it takes to run async function
    asyncio.run(test_async())
    print("-" * 50)
    # now finally lets see how long it takes the run wrapped async function in process pool
    for i in iterations:
        start = time.time()
        with concurrent.futures.ProcessPoolExecutor() as executor:
            futures = [executor.submit(wrapped_async_function) for _ in range(i)]
            for item in concurrent.futures.as_completed(futures):
                pass

        end = time.time()
        print(f"Process async execution took {end - start} seconds for {i} iterations.")

    print("-" * 50)
    # now finally lets see how long it takes the run sync function in process pool
    for i in iterations:
        start = time.time()
        with concurrent.futures.ProcessPoolExecutor() as executor:
            futures = [executor.submit(sync_function) for _ in range(i)]
            for item in concurrent.futures.as_completed(futures):
                pass

        end = time.time()
        print(f"Process sync execution took {end - start} seconds for {i} iterations.")
