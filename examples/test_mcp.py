import streamlit as st
import asyncio
import requestcompletion as rc
from requestcompletion.nodes.library.mcp_tool import from_mcp_server


TIME_MCP_COMMAND = r"C://Users//Levi//anaconda3//python.exe"
TIME_MCP_ARGS = ["-m", "mcp_server_time", "--local-timezone=America/Vancouver"]

AIRBNB_MCP_COMMAND = r"npx"
AIRBNB_MCP_ARGS = ["-y", "@openbnb/mcp-server-airbnb", "--ignore-robots-txt"]

@st.cache_resource(show_spinner=True)
def load_tools():
    time_tools = asyncio.run(from_mcp_server(TIME_MCP_COMMAND, TIME_MCP_ARGS))
    airbnb_tools = asyncio.run(from_mcp_server(AIRBNB_MCP_COMMAND, AIRBNB_MCP_ARGS))
    return {*time_tools, *airbnb_tools}

tools = load_tools()

@st.cache_resource(show_spinner=True)
def get_parent_tool():
    return rc.library.tool_call_llm(
        connected_nodes=tools,
        pretty_name="Parent Tool",
        system_message=rc.llm.SystemMessage("Provide a response, using relevant tools as required."),
        model=rc.llm.OpenAILLM("gpt-4o"),
    )

parent_tool = get_parent_tool()

st.title("MCP Chatbot Demo")

if "history" not in st.session_state:
    st.session_state.history = rc.llm.MessageHistory([])

if "runner" not in st.session_state:
    st.session_state.runner = rc.Runner(executor_config=rc.ExecutorConfig(logging_setting="QUIET", timeout=1000))

for msg in st.session_state.history:
    if isinstance(msg, rc.llm.UserMessage):
        st.chat_message("user").write(msg.content)
    elif isinstance(msg, rc.llm.AssistantMessage):
        st.chat_message("assistant").write(msg.content)

if prompt := st.chat_input("Ask something..."):
    st.session_state.history.append(rc.llm.UserMessage(prompt))
    with st.spinner("Thinking..."):
        response = asyncio.run(
            st.session_state.runner.run(parent_tool, message_history=st.session_state.history)
        )
    st.session_state.history.append(rc.llm.AssistantMessage(response.answer))
    st.chat_message("user").write(prompt)
    st.chat_message("assistant").write(response.answer)
