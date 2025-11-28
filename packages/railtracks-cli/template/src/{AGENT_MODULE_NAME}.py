import railtracks as rt


# Define a tool (just a function!)
def get_weather(location: str) -> str:
    """Get the weather for a given location."""
    return f"It's sunny in {location}!"


# Define your agent here
agent = rt.agent_node(
    name="{AGENT_NAME}",
    tool_nodes=(rt.function_node(get_weather)),
    llm=rt.llm.OpenAILLM("gpt-4o"),
    system_message="You are a helpful AI assistant.",
)
