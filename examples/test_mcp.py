import asyncio
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from typing import Dict, Type, Any

import requestcompletion as rc
from src.requestcompletion.llm.tools import Tool
from requestcompletion.nodes.nodes import Node
from typing_extensions import Self, Optional

from src.requestcompletion.nodes.library.mcp_tool import from_mcp_server

# You can configure these directly or load from your config
MCP_COMMAND = r"npx"  # C://Users//Levi//anaconda3//python.exe"
MCP_ARGS = ["-y",
            "@openbnb/mcp-server-airbnb"]  # "-m", "mcp_server_time", "--local-timezone=America/Vancouver"]


def main():
    # Discover all tools
    tools = asyncio.run(from_mcp_server(MCP_COMMAND, MCP_ARGS))

    async def test_tool(_nodes):
        parent_tool = rc.library.tool_call_llm(
            connected_nodes=tools,
            pretty_name="Parent Tool",
            system_message=rc.llm.SystemMessage("Provide a response using the tool when asked."),
            model=rc.llm.OpenAILLM("gpt-4o"),
        )

        with rc.Runner(executor_config=rc.ExecutorConfig(logging_setting="QUIET", timeout=1000)) as runner:
            message_history = rc.llm.MessageHistory(
                [
                    rc.llm.UserMessage(
                        "Show me a listing for an Airbnb in Vancouver, BC, Canada. "
                    )
                ]
            )
            response = await runner.run(parent_tool, message_history=message_history)

            print("Response:", response.answer)

    asyncio.run(test_tool(tools))


if __name__ == "__main__":
    main()
