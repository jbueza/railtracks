from __future__ import annotations

from abc import abstractmethod, ABC
from typing import (
    Any,
    TypeVar,
    Callable,
)


from ..nodes import (
    Node,
)



TOutput = TypeVar("_TOutput")

# TODO migrate the following classes to the new system
# class TerminalLLM(Node[str], ABC):
#     """A simple LLM nodes that takes in a message and returns a response. It is the simplest of all llms."""
#
#     def __init__(self, message_history: MessageHistory):
#         """Creates a new instance of the TerminalLLM class
#
#         Args:
#
#         """
#         super().__init__()
#         self.model = self.create_model()
#         self.message_hist = MessageHistory.create_w_system(self.system_message())
#         self.message_hist += message_history
#
#     @classmethod
#     @abstractmethod
#     def system_message(cls) -> Content: ...
#
#     @classmethod
#     @abstractmethod
#     def create_model(cls) -> ModelLLM: ...
#
#     def invoke(self) -> str:
#         """Makes a call containing the inputted message and system prompt to the model and returns the response
#
#         Returns:
#             (TerminalLLM.Output): The response message from the model
#         """
#         try:
#             returned_mess = self.model.call_llm(self.message_hist)
#         except LLMException as e:
#             raise ResetException(node=self, detail=f"{e.original_error}")
#
#         self.message_hist.add_message(returned_mess)
#
#         if isinstance(returned_mess, AssistantMessage):
#             cont = returned_mess.content
#             if cont is None:
#                 raise ResetException(self, "ModelLLM returned no content")
#             return cont.text
#
#         raise ResetException(
#             node=self,
#             detail="ModelLLM returned an unexpected message type.",
#         )
#
#     def state_details(self) -> Dict[str, str]:
#         return {
#             "message_hist": format_multiline_for_markdown(repr(self.message_hist)),
#         }
#
#
# _TOutput = TypeVar("_TOutput")
#
#
# class OutputLessToolCallLLM(Node[_TOutput], ABC, Generic[_TOutput]):
#     """A base class that is a node which contains
#      an LLm that can make tool calls. The tool calls will be returned
#     as calls or if there is a response, the response will be returned as an output"""
#
#     def __init__(
#         self,
#         message_history: MessageHistory,
#     ):
#         super().__init__()
#         self.model = self.create_model()
#         self.message_hist = MessageHistory.create_w_system(self.system_message())
#         self.message_hist += message_history
#
#     @classmethod
#     @abstractmethod
#     def system_message(cls) -> Content: ...
#
#     @classmethod
#     @abstractmethod
#     def create_model(cls) -> ModelLLM: ...
#
#     @classmethod
#     @abstractmethod
#     def tool_details(cls) -> Set[ToolDefinedNode]: ...
#
#     @classmethod
#     def tool_name_mapping(cls):
#         return {tdn.tool_info().name: tdn.prepare_tool for tdn in cls.tool_details()}
#
#     @classmethod
#     def tools(cls):
#         return ToolListDefinition([x.tool_info() for x in cls.tool_details()])
#
#     @abstractmethod
#     def return_output(self): ...
#
#     def invoke(
#         self,
#     ) -> _TOutput:
#         while True:
#             # collect the response from the model
#             try:
#                 returned_mess = self.model.call_llm(
#                     self.message_hist, tools=self.tools()
#                 )
#                 self.message_hist.add_message(returned_mess)
#             except LLMException as e:
#                 raise FatalException(node=self, detail=f"{e.original_error}")
#
#             if isinstance(returned_mess, AssistantMessage):
#                 if returned_mess.tool_calls:
#                     new_nodes = [
#                         NodeFactory(self.tool_name_mapping()[t_c.name], t_c.kwargs)
#                         for t_c in returned_mess.tool_calls
#                     ]
#
#                     responses = self.call_nodes(new_nodes)
#                     for r_id, resp in zip(
#                         [x.identifier for x in returned_mess.tool_calls],
#                         [x.data for x in responses],
#                     ):
#                         self.message_hist.add_tool_response(
#                             tool_id=r_id, returned_data=resp
#                         )
#
#                 elif returned_mess.content is not None:
#                     # this means the tool call is finished
#                     break
#             else:
#                 # the message is malformed from the model
#                 raise FatalException(
#                     node=self,
#                     detail="ModelLLM returned an unexpected message type.",
#                 )
#
#         return self.return_output()
#
#     def state_details(self) -> Dict[str, str]:
#         return {
#             "message_hist": format_multiline_for_markdown(repr(self.message_hist)),
#         }
#
#
# class MessageHistoryToolCallLLM(OutputLessToolCallLLM[MessageHistory], ABC):
#
#     def return_output(self) -> MessageHistory:
#         return self.message_hist
#
#
# class ToolCallLLM(OutputLessToolCallLLM[Message], ABC):
#
#     def return_output(self):
#         """Returns the last message in the message history"""
#         return self.message_hist.messages[-1]
#
#
# class ToolDefinedNode(Node[_TOutput], ABC, Generic[_TOutput]):
#     @classmethod
#     @abstractmethod
#     def tool_info(cls) -> ToolDefinition:
#         pass
#
#     @classmethod
#     @abstractmethod
#     def prepare_tool(cls, tool_parameters: Dict[str, Any]) -> ToolDefinedNode:
#         pass


class FunctionNode(Node[TOutput]):
    """
    A class for ease of creating a function node for the user
    """

    def __init__(self, func: Callable[..., TOutput], **kwargs: dict[str, Any]):
        super().__init__()
        self.func = func
        self.kwargs = kwargs

    def invoke(self) -> TOutput:
        try:
            result = self.func(**self.kwargs)
            if result and isinstance(result, str):
                self.data_streamer(result)

            return result
        except Exception as e:
            raise RuntimeError(f"Error invoking function: {str(e)}")

    def pretty_name(self) -> str:
        return f"Function Node - {self.__class__.__name__}({self.func.__name__})"
