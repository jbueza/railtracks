import asyncio
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from typing import Dict, Type, Any

import requestcompletion as rc
from requestcompletion.llm.tools import Tool
from requestcompletion.nodes.nodes import Node
from typing_extensions import Self

# You can configure these directly or load from your config
MCP_COMMAND = r"C://Users//Levi//anaconda3//python.exe"
MCP_ARGS = ["-m", "mcp_server_time", "--local-timezone=America/Vancouver"]


class MCPAsyncClient:
    def __init__(self, command: str, args: list):
        self.command = command
        self.args = args
        self.session = None
        self.exit_stack = AsyncExitStack()
        self._tools_cache = None

    async def __aenter__(self):
        server_params = StdioServerParameters(
            command=self.command,
            args=self.args,
            env=None
        )
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        await self.session.initialize()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.exit_stack.aclose()

    async def list_tools(self):
        if self._tools_cache is not None:
            return self._tools_cache
        resp = await self.session.list_tools()
        self._tools_cache = resp.tools
        return self._tools_cache

    async def call_tool(self, tool_name: str, tool_args: Dict[str, Any]):
        return await self.session.call_tool(tool_name, tool_args)


def from_mcp(tool, command: str, args: list):
    class MCPToolNode(Node):

        def __init__(self, **kwargs):
            super().__init__()
            self.kwargs = kwargs

        async def invoke(self):
            async with MCPAsyncClient(command, args) as client:
                result = await client.call_tool(tool.name, self.kwargs)
            if hasattr(result, "content"):
                return result.content
            return result

        @classmethod
        def pretty_name(cls):
            return f"MCPToolNode({tool.name})"

        @classmethod
        def tool_info(cls) -> Tool:
            return Tool.from_function(tool)

        @classmethod
        def prepare_tool(cls, tool_parameters: Dict[str, Any]) -> Self:
            return cls(**tool_parameters)

    return MCPToolNode


async def from_mcp_server(command: str, args: list) -> [Type[Node]]:
    async with MCPAsyncClient(command, args) as client:
        tools = await client.list_tools()
        return [
            from_mcp(tool, command, args)
            for tool in tools
        ]


def main():
    # Discover all tools and display them
    async def show_tools():
        tools = await from_mcp_server(MCP_COMMAND, MCP_ARGS)
        return tools

    tools = asyncio.run(show_tools())

    # Test a tool (replace 'local_time' with your actual tool name)
    # tool_name = list(nodes.keys())[0]  # use first discovered tool
    # MyNode = nodes[tool_name]
    # node = MyNode()  # supply arguments if needed

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
                        "What time is it?"
                    )
                ]
            )
            response = await runner.run(parent_tool, message_history=message_history)

            print("Response:", response)

    asyncio.run(test_tool(tools))


if __name__ == "__main__":
    main()
