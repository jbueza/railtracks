import asyncio
import inspect
import threading
import time
import webbrowser
from contextlib import AsyncExitStack
from datetime import timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from inspect import _empty
from typing import Any, Dict
from urllib.parse import urlparse, parse_qs

import httpx
from mcp.server import FastMCP
from typing_extensions import Self, List

from mcp import ClientSession, StdioServerParameters
from mcp.client.auth import OAuthClientProvider, TokenStorage
from mcp.shared.auth import OAuthClientInformationFull, OAuthClientMetadata, OAuthToken
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client
from mcp.client.sse import sse_client
from mcp.server.fastmcp.tools.base import Tool as MCPTool
from mcp.server.fastmcp.utilities.func_metadata import FuncMetadata, func_metadata

from pydantic import BaseModel
from ..llm import Tool
from ..nodes.nodes import Node
import requestcompletion as rc


try:
    from sseclient import SSEClient
except ImportError:
    SSEClient = None


class MCPHttpParams(BaseModel):
    url: str
    headers: dict[str, Any] | None = None
    timeout: timedelta = timedelta(seconds=30)
    sse_read_timeout: timedelta = timedelta(seconds=60 * 5)
    terminate_on_close: bool = True


class MCPAsyncClient:
    """
    Async client for communicating with an MCP server via stdio or HTTP Stream, with streaming support.

    If a client session is provided, it will be used; otherwise, a new session will be created.
    """
    def __init__(
        self,
        config: StdioServerParameters | MCPHttpParams,
        client_session: ClientSession | None = None,
    ):
        self.config = config
        self.session = client_session
        self.exit_stack = AsyncExitStack()
        self._tools_cache = None

    async def __aenter__(self):
        if isinstance(self.config, StdioServerParameters):
            stdio_transport = await self.exit_stack.enter_async_context(stdio_client(self.config))
            self.session = await self.exit_stack.enter_async_context(ClientSession(*stdio_transport))
            await self.session.initialize()
        elif isinstance(self.config, MCPHttpParams):
            await self._init_http()

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

    async def _init_http(self):
        # Set transport type based on URL ending
        if self.config.url.rstrip("/").endswith("/sse"):
            self.transport_type = "sse"
        else:
            self.transport_type = "streamable_http"

        async def get_oauth_metadata(server_url: str):
            from urllib.parse import urlparse, urlunparse, urljoin
            parsed = urlparse(server_url)
            base_url = urlunparse((parsed.scheme, parsed.netloc, "", "", "", ""))
            metadata_url = urljoin(base_url, "/.well-known/oauth-authorization-server")
            async with httpx.AsyncClient() as client:
                resp = await client.get(metadata_url)
                if resp.status_code == 200:
                    return resp.json()
                return None

        oauth_metadata = await get_oauth_metadata(self.config.url)

        if oauth_metadata:
            callback_server = CallbackServer(port=3000)
            callback_server.start()

            async def callback_handler() -> tuple[str, str | None]:
                print("⏳ Waiting for authorization callback...")
                try:
                    auth_code = callback_server.wait_for_callback(timeout=300)
                    return auth_code, callback_server.get_state()
                finally:
                    callback_server.stop()

            client_metadata_dict = {
                "client_name": "Simple Auth Client",
                "redirect_uris": ["http://localhost:3000/callback"],
                "grant_types": ["authorization_code", "refresh_token"],
                "response_types": ["code"],
                "token_endpoint_auth_method": "client_secret_post",
            }

            async def _default_redirect_handler(authorization_url: str) -> None:
                print(f"Opening browser for authorization: {authorization_url}")
                webbrowser.open(authorization_url)

            oauth_auth = OAuthClientProvider(
                server_url=self.config.url,
                client_metadata=OAuthClientMetadata.model_validate(client_metadata_dict),
                storage=InMemoryTokenStorage(),
                redirect_handler=_default_redirect_handler,
                callback_handler=callback_handler,
            )

            if self.transport_type == "sse":
                client = sse_client(
                    url=self.config.url,
                    headers=self.config.headers,
                    timeout=self.config.timeout.total_seconds(),
                    sse_read_timeout=self.config.sse_read_timeout.total_seconds(),
                    auth=oauth_auth,
                )
            else:
                client = streamablehttp_client(
                    url=self.config.url,
                    headers=self.config.headers,
                    timeout=self.config.timeout.total_seconds(),
                    sse_read_timeout=self.config.sse_read_timeout.total_seconds(),
                    terminate_on_close=self.config.terminate_on_close,
                    auth=oauth_auth,
                )
        else:
            if self.transport_type == "sse":
                client = sse_client(
                    url=self.config.url,
                    headers=self.config.headers,
                    timeout=self.config.timeout.total_seconds(),
                    sse_read_timeout=self.config.sse_read_timeout.total_seconds(),
                    auth=self.config.auth if hasattr(self.config, 'auth') else None,
                )
            else:
                client = streamablehttp_client(
                    url=self.config.url,
                    headers=self.config.headers,
                    timeout=self.config.timeout,
                    sse_read_timeout=self.config.sse_read_timeout,
                    terminate_on_close=self.config.terminate_on_close,
                    auth=self.config.auth if hasattr(self.config, 'auth') else None,
                )

        read_stream, write_stream, *_ = await self.exit_stack.enter_async_context(client)
        self.session = await self.exit_stack.enter_async_context(ClientSession(read_stream, write_stream))
        await self.session.initialize()


def from_mcp(
    tool,
    config: StdioServerParameters | MCPHttpParams,
):
    """
    Wrap an MCP tool as a Node class for use in the requestcompletion framework.

    Args:
        tool: The MCP tool object.
        config: Configuration parameters for the MCP client, either Stdio or HTTP.

    Returns:
        A Node subclass that invokes the MCP tool.
    """
    class MCPToolNode(Node):
        def __init__(self, **kwargs):
            super().__init__()
            self.kwargs = kwargs
            self.client = MCPAsyncClient(config)

        async def invoke(self):
            async with self.client:
                result = await self.client.call_tool(tool.name, self.kwargs)
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

#############


class InMemoryTokenStorage(TokenStorage):
    """Simple in-memory token storage implementation."""

    def __init__(self):
        self._tokens: OAuthToken | None = None
        self._client_info: OAuthClientInformationFull | None = None

    async def get_tokens(self) -> OAuthToken | None:
        return self._tokens

    async def set_tokens(self, tokens: OAuthToken) -> None:
        self._tokens = tokens

    async def get_client_info(self) -> OAuthClientInformationFull | None:
        return self._client_info

    async def set_client_info(self, client_info: OAuthClientInformationFull) -> None:
        self._client_info = client_info


class CallbackHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler to capture OAuth callback."""

    def __init__(self, request, client_address, server, callback_data):
        """Initialize with callback data storage."""
        self.callback_data = callback_data
        super().__init__(request, client_address, server)

    def do_GET(self):  # noqa: N802 Need to use do_GET for GET requests
        """Handle GET request from OAuth redirect."""
        parsed = urlparse(self.path)
        query_params = parse_qs(parsed.query)

        if "code" in query_params:
            self.callback_data["authorization_code"] = query_params["code"][0]
            self.callback_data["state"] = query_params.get("state", [None])[0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"""
            <html>
            <body>
                <h1>Authorization Successful!</h1>
                <p>You can close this window and return to the terminal.</p>
                <script>setTimeout(() => window.close(), 2000);</script>
            </body>
            </html>
            """)
        elif "error" in query_params:
            self.callback_data["error"] = query_params["error"][0]
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                f"""
            <html>
            <body>
                <h1>Authorization Failed</h1>
                <p>Error: {query_params['error'][0]}</p>
                <p>You can close this window and return to the terminal.</p>
            </body>
            </html>
            """.encode()
            )
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


class CallbackServer:
    """Simple server to handle OAuth callbacks."""

    def __init__(self, port=3000):
        self.port = port
        self.server = None
        self.thread = None
        self.callback_data = {"authorization_code": None, "state": None, "error": None}

    def _create_handler_with_data(self):
        """Create a handler class with access to callback data."""
        callback_data = self.callback_data

        class DataCallbackHandler(CallbackHandler):
            def __init__(self, request, client_address, server):
                super().__init__(request, client_address, server, callback_data)

        return DataCallbackHandler

    def start(self):
        """Start the callback server in a background thread."""
        handler_class = self._create_handler_with_data()
        self.server = HTTPServer(("localhost", self.port), handler_class)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        print(f"🖥️  Started callback server on http://localhost:{self.port}")

    def stop(self):
        """Stop the callback server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        if self.thread:
            self.thread.join(timeout=1)

    def wait_for_callback(self, timeout=300):
        """Wait for OAuth callback with timeout."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.callback_data["authorization_code"]:
                return self.callback_data["authorization_code"]
            elif self.callback_data["error"]:
                raise Exception(f"OAuth error: {self.callback_data['error']}")
            time.sleep(0.1)
        raise Exception("Timeout waiting for OAuth callback")

    def get_state(self):
        """Get the received state parameter."""
        return self.callback_data["state"]


def create_mcp_server(nodes: List[Node], server_name: str = "MCP Server", fastmcp: FastMCP = None):
    """
    Create a FastMCP server that can be used to run nodes as MCP tools.

    Args:
        nodes: List of Node classes to be registered as tools with the MCP server.
        server_name: Name of the MCP server instance.
        fastmcp: Optional FastMCP instance to use instead of creating a new one.

    Returns:
        A FastMCP server instance.
    """
    if fastmcp is not None:
        if not isinstance(fastmcp, FastMCP):
            raise ValueError("Provided fastmcp must be an instance of FastMCP.")
        mcp = FastMCP(server_name)

    type_map = {
        "integer": int,
        "number": float,
        "string": str,
        "boolean": bool,
        "array": list,
        "object": dict,
    }

    def create_tool_function(node_cls: Node, node_info):
        params = []
        args_doc = []
        params_schema = node_info.parameters.model_json_schema() if node_info.parameters is not None else {}
        for param_name, param_info in params_schema.get("properties", {}).items():
            required = param_name in params_schema.get("required", [])
            param_type = param_info.get("type", "any")
            annotation = type_map.get(param_type, str)
            if required:
                params.append(inspect.Parameter(
                    param_name,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    annotation=annotation
                ))
            else:
                params.append(inspect.Parameter(
                    param_name,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    default=None,
                    annotation=annotation
                ))

            param_desc = param_info.get("description", "")
            args_doc.append(f"    {param_name}: {param_desc}")

        async def tool_function(**kwargs):
            with rc.Runner(
                    executor_config=rc.ExecutorConfig(logging_setting="QUIET", timeout=1000)
            ) as runner:
                response = await runner.run(node_cls.prepare_tool, kwargs)
                return response.answer

        tool_function.__signature__ = inspect.Signature(params)
        return tool_function

    for node in nodes:
        node_info = node.tool_info()
        func = create_tool_function(node, node_info)

        mcp._tool_manager._tools[node_info.name] = MCPTool(
            fn=func,
            name=node_info.name,
            description=node_info.detail,
            parameters=node_info.parameters.model_json_schema() if node_info.parameters is not None else {},
            fn_metadata=func_metadata(func, []),
            is_async=True,
            context_kwarg=None,
            annotations=None,
        )  # Register the node as a tool

    return mcp
