import asyncio
from typing import Any, Dict, Type, Optional, Generic, ParamSpec
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from ..nodes import Node, _TOutput, _P


class MCPAsyncClient:
    def __init__(self, server_script_path: str):
        self.server_script_path = server_script_path
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self._tools_cache = None

    async def __aenter__(self):
        is_python = self.server_script_path.endswith('.py')
        is_js = self.server_script_path.endswith('.js')
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")
        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command,
            args=[self.server_script_path],
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


def from_mcp(
    tool_name: str,
    server_script_path: str,
    pretty_name: Optional[str] = None,
) -> Type[Node]:
    """
    Returns a Node class for a single MCP tool.
    Usage:
        MyToolNode = from_mcp("toolname", "path/to/server.py")
        node = MyToolNode(arg1=..., arg2=...)
        result = await node.invoke()
    """
    class MCPToolNode(Node[_TOutput], Generic[_P, _TOutput]):
        _tool_name = tool_name
        _server_script_path = server_script_path

        def __init__(self, **kwargs):
            super().__init__()
            self.kwargs = kwargs

        async def invoke(self):
            async with MCPAsyncClient(self._server_script_path) as client:
                result = await client.call_tool(self._tool_name, self.kwargs)
            # Result is typically a ToolResult object with a .content field
            if hasattr(result, "content"):
                return result.content
            return result

        @classmethod
        def pretty_name(cls):
            return pretty_name or f"MCPToolNode({tool_name})"

    return MCPToolNode


async def from_mcp_server(
    server_script_path: str,
) -> Dict[str, Type[Node]]:
    """
    Returns a dict of {tool_name: Node class} for all tools on the MCP server.
    Usage:
        nodes = await from_mcp_server("path/to/server.py")
        MyToolNode = nodes["toolname"]
        node = MyToolNode(...)
        result = await node.invoke()
    """
    async with MCPAsyncClient(server_script_path) as client:
        tools = await client.list_tools()
        return {
            tool.name: from_mcp(tool.name, server_script_path, pretty_name=tool.name)
            for tool in tools
        }
