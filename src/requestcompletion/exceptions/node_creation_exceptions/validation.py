from .exception_messages import get_message, get_notes
from typing import Any, Iterable
from ..fatal import RCNodeCreationError
from pydantic import BaseModel

def check_classmethod(method: Any, method_name: str) -> None:
    """
    Ensure the given method is a classmethod.

    Args:
        method: The method to check.
        method_name: The name of the method (for error messages).

    Raises:
        RCNodeCreationException: If the method is not a classmethod.
    """
    if not isinstance(method, classmethod):
        raise RCNodeCreationError(
            message=get_message("CLASSMETHOD_REQUIRED_MSG").format(method_name=method_name),
            notes=[note.format(method_name=method_name) for note in get_notes("CLASSMETHOD_REQUIRED_NOTES")],
        )

def check_connected_nodes(node_set, node: type) -> None:
    """
    Validate that node_set is non-empty and contains only subclasses of Node.

    Args:
        node_set: The set of nodes to check.
        Node: The base Node class.

    Raises:
        RCNodeCreationException: If node_set is empty or contains invalid types.
    """
    if not node_set:
        raise RCNodeCreationError(
            message=get_message("CONNECTED_NODES_EMPTY_MSG"),
            notes=get_notes("CONNECTED_NODES_EMPTY_NOTES"),
        )
    elif not all(issubclass(x, node) for x in node_set):    # ideally we should be importing node from requestcompletion, but we don't want to deal woth circular imports here :'
        raise RCNodeCreationError(
            message=get_message("CONNECTED_NODES_TYPE_MSG"),
            notes=get_notes("CONNECTED_NODES_TYPE_NOTES"),
        )

def check_duplicate_param_names(tool_params: Iterable[Any]) -> None:
    """
    Ensure all parameter names in tool_params are unique.

    Args:
        tool_params: Iterable of parameter objects with a 'name' attribute.

    Raises:
        RCNodeCreationException: If duplicate parameter names are found.
    """
    if tool_params:
        names = [x.name for x in tool_params]
        if len(names) != len(set(names)):
            raise RCNodeCreationError(
                message=get_message("DUPLICATE_PARAMETER_NAMES_MSG"),
                notes=get_notes("DUPLICATE_PARAMETER_NAMES_NOTES"),
            )

def check_output_model(method: classmethod, cls: type) -> None:
    """
    Validate the output model returned by a classmethod.

    Args:
        method: The classmethod to call.
        cls: The class to pass to the method.

    Raises:
        RCNodeCreationException: If the output model is missing, invalid, or empty.
    """
    output_model = method.__func__(cls)
    if not output_model:
        raise RCNodeCreationError(
            message=get_message("OUTPUT_MODEL_REQUIRED_MSG"),
            notes=get_notes("OUTPUT_MODEL_REQUIRED_NOTES"),
        )
    elif not issubclass(output_model, BaseModel):
        raise RCNodeCreationError(
            message=get_message("OUTPUT_MODEL_TYPE_MSG").format(actual_type=type(output_model)),
            notes=get_notes("OUTPUT_MODEL_TYPE_NOTES"),
        )
    elif len(output_model.model_fields) == 0:
        raise RCNodeCreationError(
            message=get_message("OUTPUT_MODEL_EMPTY_MSG"),
            notes=get_notes("OUTPUT_MODEL_EMPTY_NOTES"),
        )

def check_pretty_name(pretty_name: str | None, tool_details: Any) -> None:
    """
    Ensure a pretty_name is provided if tool_details exist.

    Args:
        pretty_name: The pretty name to check.
        tool_details: The tool details object.

    Raises:
        RCNodeCreationException: If pretty_name is missing when tool_details are present.
    """
    if pretty_name is None and tool_details:
        raise RCNodeCreationError(get_message("MISSING_PRETTY_NAME_MSG"))

def check_system_message(system_message: Any, system_message_type: type) -> None:
    """
    Validate that system_message is an instance of SystemMessageType if provided.

    Args:
        system_message: The system message to check.
        SystemMessageType: The expected type for system_message.

    Raises:
        RCNodeCreationException: If system_message is not of the correct type.
    """
    if system_message is not None and not isinstance(system_message, system_message_type):
        raise RCNodeCreationError(
            get_message("INVALID_SYSTEM_MESSAGE_MSG"),
            notes=get_notes("INVALID_SYSTEM_MESSAGE_NOTES"),
        )

def check_tool_params_and_details(tool_params: Any, tool_details: Any) -> None:
    """
    Ensure tool_details are provided if tool_params exist.

    Args:
        tool_params: The tool parameters to check.
        tool_details: The tool details object.

    Raises:
        RCNodeCreationException: If tool_params exist but tool_details are missing.
    """
    if tool_params and not tool_details:
        raise RCNodeCreationError(
            get_message("MISSING_TOOL_DETAILS_MSG"),
            notes=get_notes("MISSING_TOOL_DETAILS_NOTES"),
        )
