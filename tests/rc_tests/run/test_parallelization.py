import requestcompletion as rc
import asyncio

async def timeout_node():
    await asyncio.sleep(1)

rc.library.from_function(timeout_node)

async def top_level():
