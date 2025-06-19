import asyncio
import pytest
import time
import threading

import requestcompletion as rc
from requestcompletion.mcp.to_node import create_mcp_server
from requestcompletion.mcp import MCPHttpParams
from requestcompletion.nodes.library import from_mcp_server

# ---- Node and MCP server setup as normal ----

def add_nums(num1: int, num2: int, print_s: str):
    return num1 + num2 + 10

node = rc.library.from_function(add_nums)

def run_server():
    """Runs MCP server in current thread (blocking)."""
    mcp = create_mcp_server([node])
    # streamable-http uses asyncio.run() inside, so just call .run()
    mcp.run(transport="streamable-http")

@pytest.fixture(scope="module")
def mcp_server():
    # Run the server in a background thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    # Wait for server to be ready
    time.sleep(3)
    yield

def test_add_nums_tool(mcp_server):
    tools = from_mcp_server(MCPHttpParams(url="http://127.0.0.1:8000/mcp"))
    assert len(tools) == 1

    with rc.Runner(
        executor_config=rc.ExecutorConfig(logging_setting="QUIET", timeout=1000)
    ) as runner:
        response = asyncio.run(runner.run(tools[0], num1=1, num2=3, print_s="Hello"))

    assert (
        response.answer[0].text == "14"
    ), f"Expected 14, got {response.answer[0].text}"