
from typing import Dict, Any, Set, Type
import asyncio
import requestcompletion as rc

# ======================== Terminal LLMS as Tools ===============================================
class HarshCritic(rc.library.TerminalLLM):
    @classmethod
    def system_message(cls):
        return "You are a harsh critic of the world and you should analyze the given statement and provide a harsh critique of it."
    
    @classmethod
    def create_model(cls) -> rc.llm.ModelBase:
        return rc.llm.OpenAILLM("gpt-4o")

    def __init__(
            self,
            message_history: rc.llm.MessageHistory
    ):
        message_history.insert(0, rc.llm.SystemMessage(self.system_message()))
        super().__init__(
            message_history=message_history,
            model=self.create_model(),
        )
    
    @classmethod
    def pretty_name(cls) -> str:
        return "Harsh Critic"
    
    # for types which you want to connect to an LLM using our tooling you should implement this method
    @classmethod
    def tool_info(cls) -> rc.llm.Tool:
        return rc.llm.Tool(
            name="Harsh_Critic",
            detail="A tool used to critique a statement harshly.",
            parameters={rc.llm.Parameter("analysis_detail", "string", "The thing you would like to analyze")}
            
        )
    
    @classmethod
    def prepare_tool(cls, tool_parameters: Dict[str, Any]) -> rc.library.TerminalLLM:
        message_hist = rc.llm.MessageHistory([rc.llm.UserMessage(tool_parameters["analysis_detail"])])
        return cls(message_hist)
        
class PositiveCritic(rc.library.TerminalLLM):
    @classmethod
    def system_message(cls):
        return "You are a positive critic of the world and you should analyze the given statement and provide a positive critique of it."
    
    @classmethod
    def create_model(cls) -> rc.llm.ModelBase:
        return rc.llm.OpenAILLM("gpt-4o")

    def __init__(
            self,
            message_history: rc.llm.MessageHistory
    ):
        message_history.insert(0, rc.llm.SystemMessage(self.system_message()))
        super().__init__(
            message_history=message_history,
            model=self.create_model(),
        )
    
    @classmethod
    def pretty_name(cls) -> str:
        return "Positive Critic"
    
    # for types which you want to connect to an LLM using our tooling you should implement this method
    @classmethod
    def tool_info(cls) -> rc.llm.Tool:
        return rc.llm.Tool(
            name="Positive_Critic",
            detail="A tool used to critique a statement positively.",
            parameters={rc.llm.Parameter("analysis_detail", "string", "The thing you would like to analyze")}
            
        )
    
    @classmethod
    def prepare_tool(cls, tool_parameters: Dict[str, Any]) -> rc.library.TerminalLLM:
        message_hist = rc.llm.MessageHistory([rc.llm.UserMessage(tool_parameters["analysis_detail"])])
        return cls(message_hist)
    
class DeeperMeaningCritic(rc.library.TerminalLLM):
    @classmethod
    def system_message(cls):
        return "You are a critic of the world and you should analyze the given statement and provide a critique of it."
    
    @classmethod
    def create_model(cls) -> rc.llm.ModelBase:
        return rc.llm.OpenAILLM("gpt-4o")

    def __init__(
            self,
            message_history: rc.llm.MessageHistory
    ):
        message_history.insert(0, rc.llm.SystemMessage(self.system_message()))
        super().__init__(
            message_history=message_history,
            model=self.create_model(),
        )
    
    @classmethod
    def pretty_name(cls) -> str:
        return "Deeper Meaning Critic"
    
    # for types which you want to connect to an LLM using our tooling you should implement this method
    @classmethod
    def tool_info(cls) -> rc.llm.Tool:
        return rc.llm.Tool(
            name="Deeper_Meaning_Critic",
            detail="A tool used to critique a statement.",
            parameters={rc.llm.Parameter("analysis_detail", "string", "The thing you would like to analyze",)}
            
        )
    
    @classmethod
    def prepare_tool(cls, tool_parameters: Dict[str, Any]) -> rc.library.TerminalLLM:
        message_hist = rc.llm.MessageHistory([rc.llm.UserMessage(tool_parameters["analysis_detail"])])
        return cls(message_hist)
    
# ==================================== End Terminal LLMs as Tools ======================================

system_message_critic = rc.llm.SystemMessage("You are a critic of the world and you provide comprehensive critiques of the world around you. You should utilize the provided tools to collect specific critiques before completing your answer.")

Critic = rc.library.tool_call_llm(connected_nodes={HarshCritic, PositiveCritic, DeeperMeaningCritic}, pretty_name="Critic", system_message=system_message_critic, model=rc.llm.OpenAILLM("gpt-4o"))

template = ("I am writing a short story and I would like to analyze my introduction.\n"
            "\n"
            "Once upon a time there was a little boy who lived in a small village. He was a very kind and generous, but lacked an understanding"
            " of the world around him. He was always looking for ways to help others and make the world a better place. One day, he stumbled upon a"
            " magical book that would change his life forever. The book was filled with stories of adventure and mystery, and the promise of a better"
            " tomorrow.")

async def main():
    with rc.Runner(executor_config=rc.run.ExecutorConfig(timeout=50)) as runner:
        response = await runner.run(Critic, message_history=rc.llm.MessageHistory([rc.llm.UserMessage(template)]))
        print(response.answer)

asyncio.run(main())