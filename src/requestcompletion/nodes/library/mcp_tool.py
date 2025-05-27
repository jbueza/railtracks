import asyncio
from typing import Any, Dict, Type, Optional, Generic, ParamSpec
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from typing_extensions import Self

from ..nodes import Node, _TOutput, _P
from ...llm import Tool


class MCPAsyncClient:
    """
    Async client for communicating with an MCP server via stdio or HTTP Stream.

    Args:
        command: The command to launch the MCP server (e.g., 'npx').
        args: Arguments to pass to the command.
        env: Optional environment variables.
        transport_type: 'stdio' (default) or 'http-stream'.
        transport_options: Optional dict for HTTP Stream configuration (endpoint, headers, responseMode, etc).
    """
    def __init__(
        self,
        command: str,
        args: list,
        env: Optional[Dict[str, str]] = None,
        transport_type: str = "stdio",
        transport_options: Optional[dict] = None,
    ):
        self.command = command
        self.args = args
        self.env = env  # TODO: Handle environment variables
        self.transport_type = transport_type
        self.transport_options = transport_options or {}
        self.session = None
        self.exit_stack = AsyncExitStack()
        self._tools_cache = None

    async def __aenter__(self):
        if self.transport_type == "stdio":
            server_params = StdioServerParameters(
                command=self.command,
                args=self.args,
                env=self.env
            )
            stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            self.stdio, self.write = stdio_transport
            self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
            await self.session.initialize()
        elif self.transport_type == "http-stream":
            import aiohttp
            self.http_session = await self.exit_stack.enter_async_context(aiohttp.ClientSession())
            self.endpoint = self.transport_options.get("endpoint", "/mcp")
            self.base_url = self.transport_options.get("base_url", "http://localhost:8080") + self.endpoint
            self.response_mode = self.transport_options.get("responseMode", "batch")
            self.http_headers = self.transport_options.get("headers", {})
            self.session_id = None
            # Initialize session
            init_req = {
                "jsonrpc": "2.0",
                "id": "init-" + str(asyncio.get_event_loop().time()),
                "method": "initialize",
                "params": {}
            }
            resp = await self.http_session.post(
                self.base_url,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                    **self.http_headers,
                },
                json=init_req
            )
            self.session_id = resp.headers.get("Mcp-Session-Id")
            # Optionally process response if needed
            await resp.release()
        else:
            raise ValueError(f"Unsupported transport_type: {self.transport_type}")
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.exit_stack.aclose()

    async def list_tools(self):
        """
        List available tools from the MCP server.
        Returns:
            List of tool objects as provided by the MCP server.
        """
        if self._tools_cache is not None:
            return self._tools_cache
        if self.transport_type == "stdio":
            resp = await self.session.list_tools()
            self._tools_cache = resp.tools
        elif self.transport_type == "http-stream":
            req = {
                "jsonrpc": "2.0",
                "id": "list_tools-" + str(asyncio.get_event_loop().time()),
                "method": "list_tools",
                "params": {}
            }
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                **self.http_headers,
            }
            if self.session_id:
                headers["Mcp-Session-Id"] = self.session_id
            resp = await self.http_session.post(
                self.base_url,
                headers=headers,
                json=req
            )
            data = await resp.json()
            self._tools_cache = data.get("result", {}).get("tools", [])
            await resp.release()
        return self._tools_cache

    async def call_tool(self, tool_name: str, tool_args: Dict[str, Any]):
        """
        Call a tool by name with the provided arguments.
        Args:
            tool_name: Name of the tool to invoke.
            tool_args: Arguments for the tool.
        Returns:
            The result from the tool invocation.
        """
        if self.transport_type == "stdio":
            return await self.session.call_tool(tool_name, tool_args)
        elif self.transport_type == "http-stream":
            req = {
                "jsonrpc": "2.0",
                "id": tool_name + "-" + str(asyncio.get_event_loop().time()),
                "method": tool_name,
                "params": tool_args
            }
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                **self.http_headers,
            }
            if self.session_id:
                headers["Mcp-Session-Id"] = self.session_id
            resp = await self.http_session.post(
                self.base_url,
                headers=headers,
                json=req
            )
            # For now, only support batch (JSON) response
            if resp.headers.get("Content-Type", "").startswith("application/json"):
                data = await resp.json()
                await resp.release()
                return data.get("result")
            else:
                # TODO: Support streaming (SSE) responses if needed
                await resp.release()
                raise NotImplementedError("Streaming (SSE) responses not yet supported in client.")
        else:
            raise ValueError(f"Unsupported transport_type: {self.transport_type}")


def from_mcp(
    tool,
    command: str,
    args: list,
    transport_type: str = "stdio",
    transport_options: Optional[dict] = None
):
    """
    Wrap an MCP tool as a Node class for use in the requestcompletion framework.

    Args:
        tool: The MCP tool object.
        command: Command to launch the MCP server.
        args: Arguments for the command.
        transport_type: 'stdio' or 'http-stream'.
        transport_options: Optional dict for HTTP Stream configuration.

    Returns:
        A Node subclass that invokes the MCP tool.
    """
    class MCPToolNode(Node):
        def __init__(self, **kwargs):
            super().__init__()
            self.kwargs = kwargs

        async def invoke(self):
            async with MCPAsyncClient(
                command,
                args,
                transport_type=transport_type,
                transport_options=transport_options
            ) as client:
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


async def from_mcp_server(
    command: str,
    args: list,
    transport_type: str = "stdio",
    transport_options: Optional[dict] = None
) -> [Type[Node]]:
    """
    Discover all tools from an MCP server and wrap them as Node classes.

    Args:
        command: Command to launch the MCP server.
        args: Arguments for the command.
        transport_type: 'stdio' or 'http-stream'.
        transport_options: Optional dict for HTTP Stream configuration.

    Returns:
        List of Nodes, one for each discovered tool.
    """
    async with MCPAsyncClient(
        command,
        args,
        transport_type=transport_type,
        transport_options=transport_options
    ) as client:
        tools = await client.list_tools()
        return [
            from_mcp(
                tool,
                command,
                args,
                transport_type=transport_type,
                transport_options=transport_options
            )
            for tool in tools
        ]
