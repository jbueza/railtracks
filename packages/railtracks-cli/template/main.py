import asyncio
import railtracks as rt
from src.{AGENT_MODULE_NAME} import agent


async def main():
    """Main entry point for the {AGENT_NAME} agent."""
    # Example: Run the agent with a test query
    response = await rt.call(agent, "Hello, how can you help me?")
    print(response.text)


if __name__ == "__main__":
    asyncio.run(main())

