from typing import Type, Optional, Literal

from mcp import StdioServerParameters
from requestcompletion.nodes.nodes import Node
import asyncio

from requestcompletion.utils.mcp_utils import MCPAsyncClient, from_mcp
from typing_extensions import Union

from requestcompletion.utils.mcp_utils import MCPHttpParams


def from_mcp_server(
    config: Union[StdioServerParameters, MCPHttpParams],
) -> [Type[Node]]:
    """
    Discover all tools from an MCP server and wrap them as Node classes.

    Args:
        config: Configuration for the MCP server, either as StdioServerParameters or MCPHttpParams.

    Returns:
        List of Nodes, one for each discovered tool.
    """
    return asyncio.run(
        async_from_mcp_server(config)
    )


async def async_from_mcp_server(
    config: Union[StdioServerParameters, MCPHttpParams],
) -> [Type[Node]]:
    """
    Asynchronously discover all tools from an MCP server and wrap them as Node classes.

    Args:
        config

    Returns:
        List of Nodes, one for each discovered tool.
    """
    async with MCPAsyncClient(config) as client:
        tools = await client.list_tools()
        return [
            from_mcp(
                tool,
                config
            )
            for tool in tools
        ]
