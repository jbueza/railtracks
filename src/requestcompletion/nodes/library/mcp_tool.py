from typing import Type, Optional, Literal
from requestcompletion.nodes.nodes import Node
import asyncio

from requestcompletion.utils.mcp_utils import MCPAsyncClient, from_mcp


def from_mcp_server(
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
    return asyncio.run(
        async_from_mcp_server(
            command,
            args,
            transport_type=transport_type,
            transport_options=transport_options
        )
    )


async def async_from_mcp_server(
    command: str,
    args: list,
    transport_type: Literal["stdio", "http-stream"] = "stdio",
    transport_options: Optional[dict] = None
) -> [Type[Node]]:
    """
    Asynchronously discover all tools from an MCP server and wrap them as Node classes.

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
