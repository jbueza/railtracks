import asyncio
from typing import TypeVar, ParamSpec, Generic, Set, Type, Dict, Any, Union, Callable
from copy import deepcopy
from ..nodes import Node
from ...llm import (
    MessageHistory,
    ModelBase,
    ToolCall,
    ToolResponse,
    ToolMessage,
    UserMessage,
)
from ...interaction.call import call
from abc import ABC, abstractmethod
from ...exceptions import NodeCreationError, LLMError
from ...exceptions.node_invocation.validation import check_message_history

_T = TypeVar("_T")
_P = ParamSpec("_P")


class OutputLessToolCallLLM(Node[_T], ABC, Generic[_T]):
    """A base class that is a node which contains
     an LLm that can make tool calls. The tool calls will be returned
    as calls or if there is a response, the response will be returned as an output"""

    def __init__(
        self,
        message_history: MessageHistory,
        model: ModelBase,
        max_tool_calls: int | None = 30,
    ):
        super().__init__()
        self.model = model
        check_message_history(
            message_history
        )  # raises NodeInvocationError if any of the checks fail
        self.message_hist = deepcopy(message_history)
        self.structured_resp_node = None  # The structured LLM node

        self.max_tool_calls = max_tool_calls

    @abstractmethod
    def connected_nodes(self) -> Set[Union[Type[Node], Callable]]: ...

    def create_node(self, tool_name: str, arguments: Dict[str, Any]) -> Node:
        """
        A function which creates a new instance of a node Class from a tool name and arguments.

        This function may be overwritten to fit the needs of the given node as needed.
        """
        node = [x for x in self.connected_nodes() if x.tool_info().name == tool_name]
        if node == []:
            raise LLMError(
                reason=f" Error creating a node from tool {tool_name}. The tool_name given by the LLM doesn't match any of the tool names in the connected nodes.",
                message_history=self.message_hist,
            )
        if len(node) > 1:
            raise NodeCreationError(
                message=f"Tool {tool_name} has multiple nodes, this is not allowed. Current Node include {[x.tool_info().name for x in self.connected_nodes()]}",
                notes=["Please check the tool names in the connected nodes."],
            )
        return node[0].prepare_tool(arguments)

    def tools(self):
        return [x.tool_info() for x in self.connected_nodes()]

    @abstractmethod
    def return_output(self) -> _T: ...

    async def invoke(
        self,
    ) -> _T:
        while True:
            # special check for maximum tool calls
            if self.max_tool_calls is not None and (
                len([m for m in self.message_hist if isinstance(m, ToolMessage)])
                >= self.max_tool_calls
            ):
                raise LLMError(
                    reason=f"Maximum number of tool calls ({self.max_tool_calls}) exceeded.",
                    message_history=self.message_hist,
                )

            # collect the response from the model
            returned_mess = self.model.chat_with_tools(
                self.message_hist, tools=self.tools()
            )

            self.message_hist.append(returned_mess.message)

            if returned_mess.message.role == "assistant":
                # if the returned item is a list then it is a list of tool calls
                if isinstance(returned_mess.message.content, list):
                    assert all(
                        isinstance(x, ToolCall) for x in returned_mess.message.content
                    )

                    contracts = []
                    for t_c in returned_mess.message.content:
                        contract = call(
                            self.create_node,
                            t_c.name,
                            t_c.arguments,
                        )
                        contracts.append(contract)

                    tool_responses = await asyncio.gather(
                        *contracts, return_exceptions=True
                    )
                    tool_responses = [
                        (
                            x
                            if not isinstance(x, Exception)
                            else f"There was an error running the tool: \n Exception message: {x} "
                        )
                        for x in tool_responses
                    ]
                    tool_ids = [x.identifier for x in returned_mess.message.content]
                    tool_names = [x.name for x in returned_mess.message.content]

                    for r_id, r_name, resp in zip(
                        tool_ids,
                        tool_names,
                        tool_responses,
                    ):
                        self.message_hist.append(
                            ToolMessage(
                                ToolResponse(
                                    identifier=r_id, result=str(resp), name=r_name
                                )
                            )
                        )
                else:
                    # this means the tool call is finished
                    break
            else:
                # the message is malformed from the model
                raise LLMError(
                    reason="ModelLLM returned an unexpected message type.",
                    message_history=self.message_hist,
                )

        if self.structured_resp_node:
            try:
                self.structured_output = await call(
                    self.structured_resp_node,
                    message_history=MessageHistory(
                        [UserMessage(str(self.message_hist))]
                    ),
                )
            except Exception as e:
                # will be raised in the return_output method in StructuredToolCallLLM
                self.structured_output = LLMError(
                    reason="Failed to parse assistant response into structured output.",
                    message_history=self.message_hist,
                    exception_message=str(e),
                )

        return self.return_output()
