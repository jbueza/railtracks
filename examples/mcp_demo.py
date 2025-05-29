import streamlit as st
import asyncio
import os
import requestcompletion as rc
from requestcompletion.nodes.library.mcp_tool import async_from_mcp_server

# MCP server URL
urls = [
    "https://mcp.deepwiki.com/sse",
    "https://remote.mcpservers.org/fetch/mcp",
    "https://remote.mcpservers.org/sequentialthinking/mcp"
    ]

# Initialize chat history in session state
if "history" not in st.session_state:
    st.session_state.history = [
        {"role": "system", "content": "Provide a response using the tool when asked."}
    ]

st.title("MCP Chat Demo")

# Chat message display
for msg in st.session_state.history:
    if msg["role"] == "user":
        st.chat_message("user").write(msg["content"], unsafe_allow_html=True)
    elif msg["role"] == "assistant":
        st.chat_message("assistant").write(msg["content"], unsafe_allow_html=True)

# User input
if prompt := st.chat_input("Type your message..."):
    st.session_state.history.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    async def get_response(history):
        all_tools = set()
        for url in urls:
            tools = await async_from_mcp_server("", [], transport_type="http-stream", transport_options={"url": url})
            all_tools.update(tools)
        parent_tool = rc.library.tool_call_llm(
            connected_nodes=all_tools,
            pretty_name="Parent Tool",
            system_message=rc.llm.SystemMessage("Provide a response using the tool when asked."),
            model=rc.llm.OpenAILLM("gpt-4o"),
        )
        message_history = rc.llm.MessageHistory(
            [rc.llm.UserMessage(m["content"]) if m["role"] == "user" else rc.llm.SystemMessage(m["content"]) for m in history if m["role"] != "assistant"]
        )
        with rc.Runner(executor_config=rc.ExecutorConfig(logging_setting="QUIET", timeout=1000)) as runner:
            response = await runner.run(parent_tool, message_history=message_history)
            return response.answer

    # Run async function in Streamlit
    response = asyncio.run(get_response(st.session_state.history))
    st.session_state.history.append({"role": "assistant", "content": response.content})
    st.chat_message("assistant").write(response.content)
    # st.experimental_rerun()