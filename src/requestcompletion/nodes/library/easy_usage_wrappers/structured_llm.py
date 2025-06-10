import warnings
from typing import Type, Dict, Any
from copy import deepcopy
from ....exceptions import RCNodeCreationException
from ....llm import (
    UserMessage,
    MessageHistory,
    ModelBase,
    SystemMessage,
    Tool,
)
from typing_extensions import Self

from ....nodes.library.structured_llm import StructuredLLM
from pydantic import BaseModel


def structured_llm(  # noqa: C901
    output_model: Type[BaseModel],
    system_message: SystemMessage | None = None,
    model: ModelBase | None = None,
    pretty_name: str | None = None,
    tool_details: str | None = None,
    tool_params: dict | None = None,
) -> Type[StructuredLLM]:
    class StructuredLLMNode(StructuredLLM):
        def __init__(
            self,
            message_history: MessageHistory,
            llm_model: ModelBase | None = None,
        ):
            message_history_copy = deepcopy(message_history)
            if system_message is not None:
                if len([x for x in message_history_copy if x.role == "system"]) > 0:
                    warnings.warn(
                        "System message already exists in message history. We will replace it."
                    )
                    message_history_copy = [
                        x for x in message_history_copy if x.role != "system"
                    ]
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
                    raise RuntimeError(
                        "You Must provide a model to the StructuredLLM class"
                    )
                llm_model = model

            super().__init__(message_history=message_history_copy, model=llm_model)

        @classmethod
        def output_model(cls) -> Type[BaseModel]:
            return output_model

        @classmethod
        def pretty_name(cls) -> str:
            if pretty_name is None:
                return output_model.__name__
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
        raise RCNodeCreationException(
            "Tool parameters provided but no tool details provided.",
            notes=["If you want to use TerminalLLM as a tool, you must provide tool details."],
        )
    elif (
        tool_details
        and tool_params
        and len([x.name for x in tool_params]) != len({x.name for x in tool_params})
    ):
        raise RCNodeCreationException(
            message="Duplicate parameter names are not allowed.",
            notes=["Parameter names in tool_params must be unique."],
        )
    elif not output_model or len(output_model.model_fields) == 0:
        raise RCNodeCreationException("Output model cannot be empty")
    elif not issubclass(output_model, BaseModel):
        raise RCNodeCreationException(f"Output model must be a pydantic model, not {type(output_model)}")
    elif system_message is not None and not isinstance(system_message, SystemMessage):
        raise RCNodeCreationException(
            "system_message must be a SystemMessage object, not a string or any other type.",
            notes=["Message history must be a list of Message objects"],
        )
    return StructuredLLMNode
