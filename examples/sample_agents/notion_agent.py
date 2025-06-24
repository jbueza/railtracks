from copy import deepcopy
from typing import Set, Type, Union, Literal, Dict, Any, Callable
from pydantic import BaseModel
from requestcompletion.llm import (
    MessageHistory,
    ModelBase,
    SystemMessage,
    AssistantMessage,
)
from requestcompletion.nodes.library import structured_llm
from requestcompletion.nodes.library._tool_call_llm_base import (
    OutputLessToolCallLLM,
)
from requestcompletion.nodes.nodes import Node
from requestcompletion.llm.message import Role

from typing_extensions import Self
from requestcompletion.exceptions import NodeCreationError
from requestcompletion.exceptions.node_creation.validation import validate_tool_metadata
from requestcompletion.exceptions.node_invocation.validation import (
    check_model,
    check_message_history,
    )
from requestcompletion.nodes.library._mcp_agent_base_class import MCPAgentBase,check_output
import requestcompletion as rc

MCP_COMMAND = "npx"
MCP_ARGS = ["-y", "@notionhq/notion-mcp-server"]
SYSTEM_MESSAGE = """You are a master notion page designer. You love creating beautiful and well-structured Notion pages and make sure that everything is correctly formatted."""


def notion_agent(  # noqa: C901
    notion_api_token: str | None = None,
    pretty_name: str | None = None,
    model: ModelBase | None = None,
    system_message: SystemMessage | str | None = SYSTEM_MESSAGE,
    output_type: Literal["MessageHistory", "LastMessage"] = "LastMessage",
    output_model: BaseModel | None = None,
    tool_details: str | None = None,
    tool_params: dict | None = None,
) -> Type[OutputLessToolCallLLM[Union[MessageHistory, AssistantMessage, BaseModel]]]:
    
    class NotionAgent(MCPAgentBase[check_output(output_type, output_model)],
            mcp_command=MCP_COMMAND, 
            mcp_args=MCP_ARGS,
            mcp_env={
            "OPENAPI_MCP_HEADERS": f'{{"Authorization": "Bearer {notion_api_token}", "Notion-Version": "2022-06-28" }}'
            },
            api_token=notion_api_token,
            pretty_name=pretty_name,
            model=model,
            system_message=system_message,
            output_type=output_type,
            output_model=output_model,
            tool_details=tool_details,
            tool_params=tool_params):
        def connected_nodes(self):
            return self.__class__._connected_nodes

    return NotionAgent