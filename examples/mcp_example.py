import asyncio
import os

import requestcompletion as rc
from mcp import StdioServerParameters
from requestcompletion.nodes.library.mcp_tool import async_from_mcp_server

from requestcompletion.nodes.library.mcp_tool import async_from_server_auth
from requestcompletion.utils.mcp_utils import MCPHttpParams

#%%
# Install mcp_server_time for time tools:
MCP_COMMAND = "npx"
MCP_ARGS = ["mcp-remote", "https://mcp.paypal.com/sse"]
# Airbnb MCP server requires Node.js and the `npx` command to run.


#%%
# Discover all tools
tools = asyncio.run(async_from_server_auth(MCPHttpParams(url="https://remote.mcpservers.org/fetch/mcp")))

#%%
parent_tool = rc.library.tool_call_llm(
    connected_nodes={*tools},
    pretty_name="Parent Tool",
    system_message=rc.llm.SystemMessage("Provide a response using the tool when asked."),
    model=rc.llm.OpenAILLM("gpt-4o"),
)

#%%
user_message = ("What tools can you use?")

#%%
with rc.Runner(executor_config=rc.ExecutorConfig(logging_setting="QUIET", timeout=1000)) as runner:
    message_history = rc.llm.MessageHistory(
        [
            rc.llm.UserMessage(
                user_message
            )
        ]
    )
    response = asyncio.run(runner.run(parent_tool, message_history=message_history))

    print("Response:", response.answer)
