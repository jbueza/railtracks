import asyncio
import os

import requestcompletion as rc
from requestcompletion.nodes.library.mcp_tool import from_mcp_server

# %%
# Install mcp_server_time for time tools:
TIME_MCP_COMMAND = os.environ.get("TIME_MCP_COMMAND", "python.exe")
TIME_MCP_ARGS = ["-m", "mcp_server_time", "--local-timezone=America/Vancouver"]

AIRBNB_MCP_COMMAND = r"npx"
AIRBNB_MCP_ARGS = ["-y", "@openbnb/mcp-server-airbnb", "--ignore-robots-txt"]
# Airbnb MCP server requires Node.js and the `npx` command to run.


# Discover all tools
time_tools = from_mcp_server(TIME_MCP_COMMAND, TIME_MCP_ARGS)
airbnb_tools = from_mcp_server(AIRBNB_MCP_COMMAND, AIRBNB_MCP_ARGS)

parent_tool = rc.library.tool_call_llm(
    connected_nodes={*time_tools, *airbnb_tools},
    pretty_name="Parent Tool",
    system_message=rc.llm.SystemMessage(
        "Provide a response using the tool when asked."
    ),
    model=rc.llm.OpenAILLM("gpt-4o"),
)

# %%
user_message = (
    "What is the current time in Vancouver, BC, Canada? "
    "Also, show me a listing for an Airbnb in Vancouver, BC, Canada."
)

# %%
with rc.Runner(
    executor_config=rc.ExecutorConfig(logging_setting="QUIET", timeout=1000)
) as runner:
    message_history = rc.llm.MessageHistory([rc.llm.UserMessage(user_message)])
    response = asyncio.run(runner.run(parent_tool, message_history=message_history))

    print("Response:", response.answer)
