import asyncio
import sys
import subprocess
import time

import requestcompletion as rc
import tempfile
import os
import textwrap

import pytest
from requestcompletion.mcp import MCPHttpParams
from requestcompletion.nodes.library import from_mcp_server


def make_server_script():
    # Write a minimal server script to a temp file
    script = textwrap.dedent("""
        import sys
        import requestcompletion as rc
        from requestcompletion.mcp.to_node import create_mcp_server

        def add_nums(num1: int, num2: int, print_s: str):
            return num1 + num2

        node = rc.library.from_function(add_nums)

        if __name__ == "__main__":
            mcp = create_mcp_server([node])
            mcp.run(transport='streamable-http')
    """)
    fd, path = tempfile.mkstemp(suffix=".py")
    with os.fdopen(fd, "w") as f:
        f.write(script)
    return path


@pytest.fixture(scope="module")
def mcp_server():
    script_path = make_server_script()
    proc = subprocess.Popen([sys.executable, script_path])
    # Wait for server to start
    time.sleep(3)
    yield
    proc.terminate()
    proc.wait()
    os.remove(script_path)


def test_list_tools(mcp_server):
    tools = from_mcp_server(MCPHttpParams(url="http://127.0.0.1:8000/mcp"))
    assert len(tools) == 1


def test_add_nums_tool(mcp_server):
    tools = from_mcp_server(MCPHttpParams(url="http://127.0.0.1:8000/mcp"))

    with rc.Runner(executor_config=rc.ExecutorConfig(logging_setting="QUIET", timeout=1000)) as runner:
        response = asyncio.run(runner.run(tools, Num1=1, Num2=3))
    assert response.answer.content == 4, f"Expected 4, got {response.answer.content}"


