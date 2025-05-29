import asyncio

import requestcompletion as rc


async def main():
    publisher = rc.execution.publisher.RCPublisher()
    await publisher.start()
    _message = None

    def callback(message: str):
        nonlocal _message
        _message = message

    publisher.subscribe(callback)
    await publisher.publish("hello world")

    while _message is None:
        await asyncio.sleep(0.001)

    assert _message == "hello world"

    await publisher.shutdown()


if __name__ == "__main__":

    asyncio.run(main())
