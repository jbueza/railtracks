from typing import Type, Optional, Literal
from ..nodes import Node
import asyncio

from ...utils.mcp_utils import from_mcp_server_async


def from_mcp_server(
    command: str,
    args: list,
    transport_type: Literal["stdio", "http-stream"] = "stdio",
    transport_options: Optional[dict] = None,
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
        from_mcp_server_async(
            command,
            args,
            transport_type=transport_type,
            transport_options=transport_options,
        )
    )
