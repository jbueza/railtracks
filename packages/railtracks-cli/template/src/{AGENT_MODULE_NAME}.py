import railtracks as rt


# Define your agent here
agent = rt.agent_node(
    name="{AGENT_NAME}",
    llm=rt.llm.OpenAILLM("gpt-4o"),
    system_message="You are a helpful AI assistant.",
)

