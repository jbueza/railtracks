import asyncio
import pytest
from unittest.mock import patch
import requestcompletion as rc
from requestcompletion.nodes.library.mcp_tool import from_mcp_server
from requestcompletion.nodes.nodes import Node

import pytest
import subprocess
import sys


@pytest.fixture(scope="session", autouse=True)
def install_mcp_server_time():
    subprocess.check_call([sys.executable, "-m", "pip", "install", "mcp_server_time"])


def test_from_mcp_server_basic():
    time_tools = from_mcp_server("python.exe", ["-m", "mcp_server_time", "--local-timezone=America/Vancouver"])
    assert len(time_tools) == 2
    assert all(issubclass(tool, Node) for tool in time_tools)


def test_from_mcp_server_with_llm():
    time_tools = from_mcp_server("python.exe", ["-m", "mcp_server_time", "--local-timezone=America/Vancouver"])
    parent_tool = rc.library.tool_call_llm(
        connected_nodes={*time_tools},
        pretty_name="Parent Tool",
        system_message=rc.llm.SystemMessage("Provide a response using the tool when asked."),
        model=rc.llm.OpenAILLM("gpt-4o"),
    )

    # Run the parent tool
    with rc.Runner(executor_config=rc.ExecutorConfig(logging_setting="QUIET", timeout=1000)) as runner:
        message_history = rc.llm.MessageHistory(
            [
                rc.llm.UserMessage(
                    "Give me a response."
                )
            ]
        )
        response = asyncio.run(runner.run(parent_tool, message_history=message_history))

    assert response.answer is not None
    assert response.answer.content == "Hello!"