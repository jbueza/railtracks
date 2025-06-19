import os
from dotenv import load_dotenv
import requestcompletion as rc
from mcp import StdioServerParameters
from requestcompletion.llm import MessageHistory, UserMessage
from notion_agent import notion_agent
import asyncio

load_dotenv()

notion_api_token = os.getenv("NOTION_TOKEN")

#Make sure you have Node.js installed



USER_PROMPT = """Would you be able to create a new page for me in Notion labeled "Test Page"? I would like to have a small joke at the top of the page."""

notion_agent = notion_agent(
    notion_api_token = notion_api_token,
)

with rc.Runner() as run:
    result = asyncio.run(run.run(
        notion_agent,message_history=MessageHistory([UserMessage(USER_PROMPT)]), llm_model = rc.llm.OpenAILLM("gpt-4o")))