from typing import Dict, Any
import src.requestcompletion as rc      # TODO Change this

# ========== Using TerminalLLMs as tools ==========
class Encoder(rc.library.TerminalLLM):
    @classmethod
    def system_message(cls):
        return "You are a text encoder. Encode the input string into bytes and do a random operation on them. You can use the following operations: reverse the byte order, add 2 to each byte (ensure values stay in 0-255), or repeat each byte twice, rotate left by 1"
    
    def __init__(
            self,
            message_history: rc.llm.MessageHistory,
    ):
        message_history.insert(0, rc.llm.SystemMessage(self.system_message()))
        super().__init__(
            message_history=message_history,
            model=self.create_model(),
        )

    def create_model(self) -> rc.llm.ModelBase:
        return rc.llm.OpenAILLM("gpt-4o")
    
    @classmethod
    def pretty_name(cls) -> str:
        return "Encoder"
    
    # for types which you want to connect to an LLM using our tooling you should implement this method
    @classmethod
    def tool_info(cls) -> rc.llm.Tool:
        return rc.llm.Tool(
            name="Encoder",
            detail="A tool used to encode text into bytes.",
            parameters={rc.llm.Parameter("text_input", "string", "The string to encode.")},
        )
    
    @classmethod
    def prepare_tool(cls, tool_parameters: Dict[str, Any]) -> rc.library.TerminalLLM:
        message_hist = rc.llm.MessageHistory([rc.llm.UserMessage(tool_parameters["text_input"])])
        return cls(message_hist)
    
class Decoder(rc.library.TerminalLLM):
    @classmethod
    def system_message(cls):
        return "You are a text decoder. Decode the bytes into a string."
    
    def __init__(
            self,
            message_history: rc.llm.MessageHistory,
    ):
        message_history.insert(0, rc.llm.SystemMessage(self.system_message()))
        super().__init__(
            message_history=message_history,
            model=self.create_model(),
        )

    def create_model(self) -> rc.llm.ModelBase:
        return rc.llm.OpenAILLM("gpt-4o")
    
    @classmethod
    def pretty_name(cls) -> str:
        return "Decoder"
    
    # for types which you want to connect to an LLM using our tooling you should implement this method
    @classmethod
    def tool_info(cls) -> rc.llm.Tool:
        return rc.llm.Tool(
            name="Encoder",
            detail="A tool used to decode bytes into text.",
            parameters={rc.llm.Parameter("bytes_input", "string", "The bytes you would like to decode")}
            
        )
    
    @classmethod
    def prepare_tool(cls, tool_parameters: Dict[str, Any]) -> rc.library.TerminalLLM:
        message_hist = rc.llm.MessageHistory([rc.llm.UserMessage(tool_parameters["text_input"])])
        return cls(message_hist)
    
# ========== End of Using TerminalLLMs as tools ==========