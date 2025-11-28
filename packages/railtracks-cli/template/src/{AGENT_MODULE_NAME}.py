import railtracks as rt


# Define a tool (just a function!)
@rt.function_node
def get_weather(location: str) -> str:
    """Get the weather for a given location."""
    return f"It's sunny in {location}!"


# Define your agent here
agent = rt.agent_node(
    name="{AGENT_NAME}",
    tool_nodes={get_weather},
    llm=rt.llm.OpenAILLM("gpt-4o"),
    system_message="You are a helpful AI assistant. You can use the get_weather tool to get the weather for a given location.",
)
