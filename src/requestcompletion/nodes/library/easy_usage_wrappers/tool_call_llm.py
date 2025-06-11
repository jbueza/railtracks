import warnings
from copy import deepcopy
from typing import Set, Type, Union, Literal, Dict, Any

from pydantic import BaseModel
from ....llm import (
    MessageHistory,
    ModelBase,
    SystemMessage,
    AssistantMessage,
    UserMessage,
    Tool,
)
from ....nodes.library import structured_llm
from ....nodes.library._tool_call_llm_base import (
    OutputLessToolCallLLM,
)
from ....nodes.nodes import Node
from ....llm.message import Role

from typing_extensions import Self
from inspect import isclass, isfunction
from ....nodes.library.function import from_function


def tool_call_llm(  # noqa: C901
    connected_nodes: Set[Type[Node]],
    pretty_name: str | None = None,
    model: ModelBase | None = None,
    system_message: SystemMessage | None = None,
    output_type: Literal["MessageHistory", "LastMessage"] = "LastMessage",
    output_model: BaseModel | None = None,
    tool_details: str | None = None,
    tool_params: dict | None = None,
) -> Type[OutputLessToolCallLLM[Union[MessageHistory, AssistantMessage, BaseModel]]]:
    if output_model:
        OutputType = output_model  # noqa: N806
    else:
        OutputType = (  # noqa: N806
            MessageHistory if output_type == "MessageHistory" else AssistantMessage
        )

    if (
        output_model and output_type == "MessageHistory"
    ):  # TODO: add support for MessageHistory output type with output_model. Maybe resp.answer = message_hist and resp.structured = model response
        raise NotImplementedError(
            "MessageHistory output type is not supported with output_model at the moment."
        )

    # If a function is passed in, we will convert it to a node
    for elem in connected_nodes:
        if isclass(elem):
            if not issubclass(elem, Node):
                raise TypeError(
                    f"Tools must be of type Node or FunctionType but got {type(elem)}"
                )
        elif isfunction(elem):
            connected_nodes.remove(elem)
            connected_nodes.add(from_function(elem))
        else:
            raise TypeError(
                f"Tools must be of type Node or FunctionType but got {type(elem)}"
            )

    class ToolCallLLM(OutputLessToolCallLLM[OutputType]):
        def return_output(self):
            if output_model:
                if isinstance(self.structured_output, Exception):
                    raise self.structured_output
                return self.structured_output
            elif output_type == "MessageHistory":
                return self.message_hist
            else:
                return self.message_hist[-1]

        def __init__(
            self,
            message_history: MessageHistory,
            llm_model: ModelBase | None = None,
            max_tool_calls: int | None = 30,
        ):
            message_history_copy = deepcopy(message_history)
            if system_message is not None:
                if len([x for x in message_history_copy if x.role == Role.system]) > 0:
                    warnings.warn(
                        "System message already exists in message history. We will replace it."
                    )
                    message_history_copy = [
                        x for x in message_history_copy if x.role != Role.system
                    ]
                    message_history_copy.insert(0, system_message)
                else:
                    message_history_copy.insert(0, system_message)

            if llm_model is not None:
                if model is not None:
                    warnings.warn(
                        "You have provided a model as a parameter and as a class variable. We will use the parameter."
                    )
            else:
                if model is None:
                    raise RuntimeError(
                        "You must provide a model to the ToolCallLLM class"
                    )
                llm_model = model

            super().__init__(message_history_copy, llm_model, max_tool_calls=max_tool_calls)

            if output_model:
                system_structured = SystemMessage(
                    "You are a structured LLM that can convert the response into a structured output."
                )
                self.structured_resp_node = structured_llm(
                    output_model, system_message=system_structured, model=llm_model
                )

        def connected_nodes(self) -> Set[Type[Node]]:
            return connected_nodes


        @classmethod
        def pretty_name(cls) -> str:
            if pretty_name is None:
                return (
                    "ToolCallLLM("
                    + ", ".join([x.pretty_name() for x in connected_nodes])
                    + ")"
                )
            else:
                return pretty_name

        @classmethod
        def tool_info(cls):
            if not tool_details:
                raise ValueError("Tool details are not provided.")
            return Tool(
                name=cls.pretty_name().replace(" ", "_"),
                detail=tool_details,
                parameters=tool_params,
            )

        @classmethod
        def prepare_tool(cls, tool_parameters: Dict[str, Any]) -> Self:
            message_hist = MessageHistory(
                [
                    UserMessage(f"{param.name}: '{tool_parameters[param.name]}'")
                    for param in (tool_params if tool_params else [])
                ]
            )
            return cls(message_hist)

    if tool_params and not tool_details:
        raise RuntimeError(
            "Tool parameters are provided, but tool details are missing."
        )
    elif tool_details and (tool_params is not None and not tool_params):
        raise RuntimeError(
            "If no parameters are required for the tool, `tool_params` must be set to None."
        )
    elif (
        tool_details
        and tool_params
        and len({param.name for param in tool_params}) != len(tool_params)
    ):
        raise ValueError("Duplicate parameter names are not allowed.")

    return ToolCallLLM
