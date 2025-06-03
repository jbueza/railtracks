import asyncio
import logging
import threading
import time
from contextlib import AsyncExitStack
from typing import Any, Dict, Optional, Literal

import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import create_mcp_http_client
from src.requestcompletion.llm import Tool
from src.requestcompletion.nodes.nodes import Node
from typing_extensions import Self, Type

try:
    from sseclient import SSEClient
except ImportError:
    SSEClient = None


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

            self.http_session = await self.exit_stack.enter_async_context(
                create_mcp_http_client(headers=self.http_headers, timeout=self.transport_options.get("batchTimeout"))
            )
            # Initialize session
            init_req = {
                "jsonrpc": "2.0",
                "id": "init-" + str(int(time.time() * 1000)),
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
            await resp.aread()
            # Start SSE stream for server-to-client messages
            await self._start_sse_stream()
        else:
            raise ValueError(f"Unsupported transport_type: {self.transport_type}")
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.terminate()
        await self.exit_stack.aclose()

    async def _start_sse_stream(self):
        if not SSEClient or not self.session_id:
            return
        url = self.base_url
        if "?" in url:
            url += f"&session={self.session_id}"
        else:
            url += f"?session={self.session_id}"

        def sse_worker():
            try:
                with httpx.Client() as client:
                    with client.stream("GET", url, headers=self.http_headers) as response:
                        sse = SSEClient(response)
                        for event in sse:
                            if self.sse_stop_event.is_set():
                                break
                            try:
                                data = event.data
                                asyncio.run_coroutine_threadsafe(
                                    self.sse_messages.put(data), self._main_loop
                                )
                            except Exception as e:
                                logging.exception("Error putting SSE message: %s", e)
            except Exception as e:
                logging.exception("SSE worker error: %s", e)

        self.sse_stop_event.clear()
        self.sse_thread = threading.Thread(target=sse_worker, daemon=True)
        self.sse_thread.start()

    async def terminate(self):
        # Stop SSE thread
        if self.sse_thread and self.sse_thread.is_alive():
            self.sse_stop_event.set()
            self.sse_thread.join(timeout=2)
            self.sse_thread = None
        # Terminate session if HTTP
        if self.transport_type == "http-stream" and self.session_id:
            try:
                await self.http_session.request(
                    "DELETE",
                    self.base_url,
                    headers={"Mcp-Session-Id": self.session_id, **self.http_headers}
                )
            except Exception as e:
                logging.exception("Error terminating HTTP session: %s", e)
            self.session_id = None

    async def get_sse_message(self, timeout: float = 0.1):
        try:
            return await asyncio.wait_for(self.sse_messages.get(), timeout)
        except asyncio.TimeoutError:
            return None

    async def list_tools(self):
        if self._tools_cache is not None:
            return self._tools_cache
        if self.transport_type == "stdio":
            resp = await self.session.list_tools()
            self._tools_cache = resp.tools
        elif self.transport_type == "http-stream":
            req = {
                "jsonrpc": "2.0",
                "id": "list_tools-" + str(int(time.time() * 1000)),
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
            data = resp.json()
            if asyncio.iscoroutine(data):
                data = await data
            self._tools_cache = data.get("result", {}).get("tools", [])
            await resp.aread()
        return self._tools_cache

    async def call_tool(self, tool_name: str, tool_args: dict):
        if self.transport_type == "stdio":
            return await self.session.call_tool(tool_name, tool_args)
        elif self.transport_type == "http-stream":
            req = {
                "jsonrpc": "2.0",
                "id": tool_name + "-" + str(int(time.time() * 1000)),
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
            content_type = resp.headers.get("Content-Type", "")
            if content_type.startswith("application/json"):
                data = resp.json()
                if asyncio.iscoroutine(data):
                    data = await data
                await resp.aread()
                return data.get("result")
            elif "text/event-stream" in content_type:
                await resp.aread()
                raise NotImplementedError("Use stream_tool_call for streaming responses.")
            else:
                await resp.aread()
                raise NotImplementedError("Unknown response type.")
        else:
            raise ValueError(f"Unsupported transport_type: {self.transport_type}")

    async def stream_tool_call(self, tool_name: str, tool_args: dict):
        if self.transport_type != "http-stream":
            raise NotImplementedError("Streaming only supported for http-stream transport.")
        req = {
            "jsonrpc": "2.0",
            "id": tool_name + "-" + str(int(time.time() * 1000)),
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
        content_type = resp.headers.get("Content-Type", "")
        if "text/event-stream" in content_type:
            async for chunk in resp.aiter_text():
                yield chunk
        else:
            await resp.aread()
            raise NotImplementedError("Non-streaming response received in stream_tool_call.")


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
            if transport_type not in ["stdio"]:
                raise NotImplementedError("Only 'stdio' transport type is currently supported for MCP tools, contact Levi.")
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


async def from_mcp_server_async(
    command: str,
    args: list,
    transport_type: Literal["stdio", "http-stream"] = "stdio",
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
