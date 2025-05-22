import asyncio
import requestcompletion as rc

from src.requestcompletion.nodes.library.mcp_tool import from_mcp_server

#%%
# Command Arg pairs for the MCP servers - Time and Airbnb
TIME_MCP_COMMAND = r"C://Users//Levi//anaconda3//python.exe"
TIME_MCP_ARGS = ["-m", "mcp_server_time", "--local-timezone=America/Vancouver"]

AIRBNB_MCP_COMMAND = r"npx"  # C://Users//Levi//anaconda3//python.exe"
AIRBNB_MCP_ARGS = ["-y", "@openbnb/mcp-server-airbnb", "--ignore-robots-txt"]

#%%
user_message = "Show me a listing for an Airbnb in Vancouver, BC, Canada. Also, what time is it?"

#%%
# Discover all tools
time_tools = asyncio.run(from_mcp_server(TIME_MCP_COMMAND, TIME_MCP_ARGS))
airbnb_tools = asyncio.run(from_mcp_server(AIRBNB_MCP_COMMAND, AIRBNB_MCP_ARGS))

#%%
parent_tool = rc.library.tool_call_llm(
    connected_nodes={*time_tools, *airbnb_tools},
    pretty_name="Parent Tool",
    system_message=rc.llm.SystemMessage("Provide a response, using relevant tools as required."),
    model=rc.llm.OpenAILLM("gpt-4o"),
)

with rc.Runner(executor_config=rc.ExecutorConfig(logging_setting="QUIET", timeout=1000)) as runner:
    message_history = rc.llm.MessageHistory(
        [
            rc.llm.UserMessage(user_message)
        ]
    )
    response = asyncio.run(runner.run(parent_tool, message_history=message_history))

print("Response:", response.answer)
