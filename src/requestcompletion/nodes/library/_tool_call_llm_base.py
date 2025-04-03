import asyncio
import warnings
from functools import partial
from typing import TypeVar, Generic, Set, Type, Dict, Any, Union, Literal
from copy import deepcopy
from ..nodes import Node, ResetException, FatalException

from ...llm import MessageHistory, ModelBase, ToolCall, ToolResponse, ToolMessage, SystemMessage, AssistantMessage

from ...interaction.call import call

from abc import ABC, abstractmethod

from ...llm.message import Role

_T = TypeVar("_T")

class OutputLessToolCallLLM(Node[_T], ABC, Generic[_T]):
    """A base class that is a node which contains
     an LLm that can make tool calls. The tool calls will be returned
    as calls or if there is a response, the response will be returned as an output"""

    def __init__(
        self,
        message_history: MessageHistory,
        model: ModelBase,
    ):
        super().__init__()
        self.model = model
        self.message_hist = deepcopy(message_history)

    @abstractmethod
    def connected_nodes(self) -> Set[Type[Node]]: ...

    def create_node(self, tool_name: str, arguments: Dict[str, Any]) -> Node:
        """
        A function which creates a new instance of a node from a tool name and arguments.

        This function may be overwritten to fit the needs of the given node as needed.
        """
        node = [x for x in self.connected_nodes() if x.tool_info().name == tool_name]
        if node is []:
            raise ResetException(node=self, detail=f"Tool {tool_name} cannot be create a node")
        if len(node) > 1:
            raise FatalException(
                node=self,
                detail=f"Tool {tool_name} has multiple nodes, this is not allowed. Current Node include {[x.tool_info().name for x in self.connected_nodes()]}",
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
            # collect the response from the model
            returned_mess = self.model.chat_with_tools(self.message_hist, tools=self.tools())
            self.message_hist.append(returned_mess.message)

            if returned_mess.message.role == "assistant":
                # if the returned item is a list then it is a list of tool calls
                if isinstance(returned_mess.message.content, list):
                    assert all([isinstance(x, ToolCall) for x in returned_mess.message.content])
                    contracts = [
                        call(lambda arguments: self.create_node(tool_name=t_c.name, arguments=arguments), t_c.arguments)
                        for t_c in returned_mess.message.content
                    ]

                    tool_responses = await asyncio.gather(*contracts, return_exceptions=True)
                    tool_responses = [
                        x if not isinstance(x, Exception) else "There was an error running the tool"
                        for x in tool_responses
                    ]

                    for r_id, resp in zip(
                        [x.identifier for x in returned_mess.message.content],
                        tool_responses,
                    ):
                        self.message_hist.append(ToolMessage(ToolResponse(identifier=r_id, result=str(resp))))

                elif returned_mess.message.content is not None:
                    # this means the tool call is finished
                    break
            else:
                # the message is malformed from the model
                raise ResetException(
                    node=self,
                    detail="ModelLLM returned an unexpected message type.",
                )

        return self.return_output()


def tool_call_llm(
    connected_nodes: Set[Type[Node]],
    pretty_name: str | None = None,
    model: ModelBase | None = None,
    system_message: SystemMessage | None = None,
    output_type: Literal["MessageHistory", "LastMessage"] = "LastMessage",
) -> Type[OutputLessToolCallLLM[Union[MessageHistory, AssistantMessage]]]:

    OutputType = MessageHistory if output_type == "MessageHistory" else AssistantMessage

    class ToolCallLLM(OutputLessToolCallLLM[OutputType]):
        def return_output(self):
            if output_type == "MessageHistory":
                return self.message_hist
            else:
                return self.message_hist[-1]

        def __init__(
            self,
            message_history: MessageHistory,
            llm_model: ModelBase | None = None,
        ):
            message_history_copy = deepcopy(message_history)
            if system_message is not None:
                if len([x for x in message_history_copy if x.role == Role.system]) > 0:
                    warnings.warn("System message already exists in message history. We will replace it.")
                    message_history_copy = [x for x in message_history_copy if x.role != Role.system]
                    message_history_copy.insert(0, system_message)
                else:
                    message_history_copy.insert(0, system_message)

            if llm_model is not None:
                if model is not None:
                    warnings.warn(
                        "You have provided a model as a parameter and as a class varaible. We will use the parameter."
                    )
            else:
                if model is None:
                    raise RuntimeError("You Must provide a model to the ToolCallLLM class")
                llm_model = model

            super().__init__(message_history_copy, llm_model)

        def connected_nodes(self) -> Set[Type[Node]]:
            return connected_nodes

        @classmethod
        def pretty_name(cls) -> str:
            if pretty_name is None:
                return "ToolCallLLM(" + ", ".join([x.pretty_name() for x in connected_nodes]) + ")"
            else:
                return pretty_name

    return ToolCallLLM


