import asyncio
import logging
import threading
import time
from contextlib import AsyncExitStack
from typing import Any, Dict, Optional, Literal

import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client
from mcp.client.sse import sse_client
from requestcompletion.llm import Tool
from requestcompletion.nodes.nodes import Node
from typing_extensions import Self, Type, List

try:
    from sseclient import SSEClient
except ImportError:
    SSEClient = None


class MCPStdioParams:
    command: str
    args: List[str]
    env: Optional[Dict[str, str]] = None


class MCPHttpParams:
    url: str
    headers: Optional[Dict[str, str]] = None
    endpoint: str = "/mcp"
    response_mode: str = "batch"
    base_url: Optional[str] = None
    transport_options: Optional[Dict] = None


class MCPAsyncClient:
    """
    Async client for communicating with an MCP server via stdio or HTTP Stream, with streaming support.
    """
    def __init__(
        self,
        command: str,
        args: list,
        env: Optional[Dict[str, str]] = None,
        transport_type: Literal["stdio", "http-stream"] = "stdio",
        transport_options: Optional[dict] = None,
    ):
        self.command = command
        self.args = args
        self.env = env
        self.transport_type = transport_type
        self.transport_options = transport_options or {}
        self.session = None
        self.exit_stack = AsyncExitStack()
        self._tools_cache = None
        self.session_id = None
        self.http_session = None
        self.sse_thread = None
        self.sse_stop_event = threading.Event()
        self.sse_messages = asyncio.Queue()
        self._main_loop = None

    async def __aenter__(self):
        self._main_loop = asyncio.get_running_loop()
        if self.transport_type == "stdio":
            server_params = StdioServerParameters(
                command=self.command,
                args=self.args,
                env=self.env
            )
            stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            self.session = await self.exit_stack.enter_async_context(ClientSession(*stdio_transport))
            await self.session.initialize()
        elif self.transport_type == "http-stream":
            self.http_headers = self.transport_options.get("headers", {})
            self.endpoint = self.transport_options.get("endpoint", "/mcp")
            self.base_url = self.transport_options.get("base_url", "http://localhost:8080") + self.endpoint
            self.response_mode = self.transport_options.get("responseMode", "batch")
            self.session_id = None

            try:
                (read_stream, write_stream, _) = await self.exit_stack.enter_async_context(
                    streamablehttp_client(
                        url=self.transport_options["url"],
                        # headers=self.http_headers,
                        # timeout=self.transport_options.get("batchTimeout"),
                        # terminate_on_close=True,
                    )
                )
                self.session = await self.exit_stack.enter_async_context(ClientSession(read_stream, write_stream))
                await self.session.initialize()
            except Exception as e:
                print("Mayday Mayday", e)
                (read_stream, write_stream) = await self.exit_stack.enter_async_context(
                    sse_client(
                        url=self.transport_options["url"],
                        # headers=self.http_headers,
                        # timeout=self.transport_options.get("batchTimeout"),
                        # terminate_on_close=True,
                    )
                )
                self.session = await self.exit_stack.enter_async_context(ClientSession(read_stream, write_stream))
                await self.session.initialize()

        else:
            raise ValueError(f"Unsupported transport_type: {self.transport_type}")
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.exit_stack.aclose()

    async def list_tools(self):
        if self._tools_cache is not None:
            return self._tools_cache
        else:
            resp = await self.session.list_tools()
            self._tools_cache = resp.tools
        return self._tools_cache

    async def call_tool(self, tool_name: str, tool_args: dict):
        return await self.session.call_tool(tool_name, tool_args)


def from_mcp(
    tool,
    command: str,
    args: list,
    transport_type: Literal["stdio", "http-stream"] = "stdio",
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
            if transport_type not in ["stdio", "http-stream"]:
                raise NotImplementedError("Transport type is not supported for MCP tools, contact Levi.")
            if self.kwargs.get("stream"):
                raise NotImplementedError("Streaming is not supported yet, contact Levi.")

        async def invoke(self):
            async with MCPAsyncClient(
                command,
                args,
                transport_type=transport_type,
                transport_options=transport_options
            ) as client:
                if self.kwargs.get("stream", False):
                    result = []
                    async for chunk in client.stream_tool_call(tool.name, self.kwargs):
                        result.append(chunk)
                    return result
                else:
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
