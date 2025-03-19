import contextvars
import asyncio

p_id = contextvars.ContextVar("parent_id")


async def call(function, _id):
    p_id.set("parent")
    token = p_id.set(_id)
    await function
    p_id.reset(token)
    print(p_id.get())


async def function():
    print(p_id.get())


async def main():
    # for i in range(10):
    contract = [call(function(), i) for i in range(10)]
    await asyncio.gather(*contract)


asyncio.run(main())
