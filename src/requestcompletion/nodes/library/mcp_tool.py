import asyncio
from typing import Any, Dict, Type, Optional, Generic, ParamSpec
from contextlib import AsyncExitStack
import shutil  # <-- add this import

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from typing_extensions import Self, Set

from ..nodes import Node, _TOutput, _P
from ...llm import Tool


class MCPAsyncClient:
    def __init__(self, command: str, args: list, env: Optional[Dict[str, str]] = None, transport_type: str = "stdio", http_url: str = None):
        self.command = command
        self.args = args
        self.env = env  # TODO: Handle environment variables
        self.transport_type = transport_type
        self.http_url = http_url
        self.session = None
        self.exit_stack = AsyncExitStack()
        self._tools_cache = None

    async def __aenter__(self):
        if self.transport_type == "stdio":
            # Check if command exists
            if shutil.which(self.command) is None:
                raise FileNotFoundError(
                    f"Command not found: {self.command}. "
                    "If you are on Windows, try using the full path to npx.cmd or ensure your PATH includes the directory containing npx."
                )
            server_params = StdioServerParameters(
                command=self.command,
                args=self.args,
                env=self.env
            )
            stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            self.stdio, self.write = stdio_transport
            self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
            await self.session.initialize()
        elif self.transport_type == "http":
            # Placeholder: Replace with actual HTTP client session logic as needed
            import aiohttp
            self.http_session = await self.exit_stack.enter_async_context(aiohttp.ClientSession())
            self.session = self  # For compatibility; implement list_tools/call_tool for HTTP below
        else:
            raise ValueError(f"Unsupported transport_type: {self.transport_type}")
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.exit_stack.aclose()

    async def list_tools(self):
        if self._tools_cache is not None:
            return self._tools_cache
        if self.transport_type == "stdio":
            resp = await self.session.list_tools()
            self._tools_cache = resp.tools
        elif self.transport_type == "http":
            # Placeholder: Replace with actual HTTP API call
            async with self.http_session.get(f"{self.http_url}/tools") as resp:
                data = await resp.json()
                self._tools_cache = data["tools"]
        return self._tools_cache

    async def call_tool(self, tool_name: str, tool_args: Dict[str, Any]):
        if self.transport_type == "stdio":
            return await self.session.call_tool(tool_name, tool_args)
        elif self.transport_type == "http":
            # Placeholder: Replace with actual HTTP API call
            async with self.http_session.post(f"{self.http_url}/tools/{tool_name}", json=tool_args) as resp:
                return await resp.json()
        else:
            raise ValueError(f"Unsupported transport_type: {self.transport_type}")


def from_mcp_tool(tool, command: str, args: list, transport_type: str = "stdio", http_url: str = None):
    class MCPToolNode(Node):
        def __init__(self, **kwargs):
            super().__init__()
            self.kwargs = kwargs

        async def invoke(self):
            async with MCPAsyncClient(command, args, transport_type=transport_type, http_url=http_url) as client:
                result = await client.call_tool(tool.name, self.kwargs)
            if hasattr(result, "content"):
                return result.content
            return result

        @classmethod
        def pretty_name(cls):
            return f"MCPToolNode({tool.name})"

        @classmethod
        def tool_info(cls) -> Tool:
            return Tool.from_mcp(tool)

        @classmethod
        def prepare_tool(cls, tool_parameters: Dict[str, Any]) -> Self:
            return cls(**tool_parameters)

    return MCPToolNode


async def from_mcp_server(command: str, args: list, transport_type: str = "stdio", http_url: str = None) -> Set[Node]:
    async with MCPAsyncClient(command, args, transport_type=transport_type, http_url=http_url) as client:
        tools = await client.list_tools()
        return {
            from_mcp_tool(tool, command, args, transport_type=transport_type, http_url=http_url)
            for tool in tools
        }
