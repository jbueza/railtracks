import requestcompletion as rc
import asyncio

async def timeout_node():
    await asyncio.sleep(1)

rc.library.from_function()

async def top_level():
