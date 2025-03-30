import pytest
from copy import deepcopy
import src.requestcompletion as rc
from tests.rc_tests.fixtures.nodes import ActionType, CapitalizeText, FatalErrorNode, UnknownErrorNode, TimeoutNode

@pytest.fixture
def model():
    return rc.llm.OpenAILLM("gpt-4o")

@pytest.fixture
def terminal_llms_system_messages():
    system_rng = rc.llm.SystemMessage("You are a random integer generator that will return a random list of integers between 0 and 100. Do not return more than 10 integers.")
    system_rng_operation = rc.llm.SystemMessage("You are a random mathematical operation calculator that will apply a random operation to the list of integers that will be provided by the user and return the result. The answer should be only a single integer.")
    system_math_genius = rc.llm.SystemMessage("You are a math genius that will get a list of integers(loi) and another interger(x), your task is to predict what operation must be appled to the list of integers to get the result of x.")
    
    return system_rng, system_rng_operation, system_math_genius


@pytest.mark.asyncio
async def test_message_history_not_mutated_terminal_llm_easy_wrapper(model, terminal_llms_system_messages):
    """
    Verify that message history is not modified after rc.call when passed to a terminal_llm node (easy wrapper version).
    """
    system_rng, system_rng_operation, system_math_genius = terminal_llms_system_messages

    RNGNode = rc.library.terminal_llm("RNG Node", system_message=system_rng, model=model)     
    RNGOperationNode = rc.library.terminal_llm("RNG Operation Node", system_message=system_rng_operation, model=model)
    MathDetectiveNode = rc.library.terminal_llm("Math Detective Node", system_message=system_math_genius, model=model)

    async def MathGame(message_history: rc.llm.MessageHistory):
        original_message_history = deepcopy(message_history)

        random_num_list_response = await rc.call(RNGNode, message_history=message_history)
        assert all(orig.content == new.content for orig, new in zip(original_message_history, message_history)), "Message history modified after rc.call 1"

        message_history.append(rc.llm.AssistantMessage("The list of random integer: " + str(random_num_list_response)))
        original_message_history.append(
            rc.llm.AssistantMessage("The list of random integer: " + str(random_num_list_response))
        )  # since we appened to message_history

        operation_response = await rc.call(RNGOperationNode, message_history=message_history)
        assert all(orig.content == new.content for orig, new in zip(original_message_history, message_history)), "Message history modified after rc.call 2"

        message_history.append(rc.llm.AssistantMessage("The result int (x) = " + str(operation_response)))
        original_message_history.append(rc.llm.AssistantMessage("The result int (x) = " + str(operation_response)))

        response = await rc.call(MathDetectiveNode, message_history=message_history, llm_model=model)
        assert all(orig.content == new.content for orig, new in zip(original_message_history, message_history)), "Message history modified after rc.call 3"

        return response

    MathGameNode = rc.library.from_function(MathGame)

    with rc.Runner() as runner:
        _ = await runner.run(MathGameNode, message_history=rc.llm.MessageHistory([rc.llm.UserMessage("You can start the game")]))


@pytest.mark.asyncio
async def test_message_history_not_mutated_terminal_llm_class(model, terminal_llms_system_messages):
    """
    Verify that message history is not modified after rc.call when passed to a structured_llm node (class version).
    """
    system_rng, system_rng_operation, system_math_genius = terminal_llms_system_messages

    def make_terminal_llm_class_version(pretty_name: str, system_message: rc.llm.SystemMessage):
        class TerminalLLMNode(rc.library.TerminalLLM):
            def __init__(
                self,
                message_history: rc.llm.MessageHistory,
                llm_model: rc.llm.ModelBase,
            ):
                message_history = [x for x in message_history if x.role != "system"]
                message_history.insert(0, system_message)
                super().__init__(message_history=message_history, model=llm_model)

            def pretty_name(self) -> str:
                return pretty_name
        
        return TerminalLLMNode

    RNGNode = make_terminal_llm_class_version("RNG Node", system_message=system_rng)   
    RNGOperationNode = make_terminal_llm_class_version("RNG Operation Node", system_message=system_rng_operation)
    MathDetectiveNode = make_terminal_llm_class_version("Math Detective Node", system_message=system_math_genius)

    async def MathGame(message_history: rc.llm.MessageHistory):
        original_message_history = deepcopy(message_history)

        random_num_list_response = await rc.call(RNGNode, message_history=message_history, llm_model=model)
        assert all(orig.content == new.content for orig, new in zip(original_message_history, message_history)), "Message history modified after rc.call 1"

        message_history.append(rc.llm.AssistantMessage("The list of random integer: " + str(random_num_list_response)))
        original_message_history.append(rc.llm.AssistantMessage("The list of random integer: " + str(random_num_list_response))) # since we appened to message_history

        operation_response = await rc.call(RNGOperationNode, message_history=message_history, llm_model=model)
        assert all(orig.content == new.content for orig, new in zip(original_message_history, message_history)), "Message history modified after rc.call 2"

        message_history.append(rc.llm.AssistantMessage("The result int (x) = " + str(operation_response)))
        original_message_history.append(rc.llm.AssistantMessage("The result int (x) = " + str(operation_response)))

        response = await rc.call(MathDetectiveNode, message_history=message_history, llm_model=model)
        assert all(orig.content == new.content for orig, new in zip(original_message_history, message_history)), "Message history modified after rc.call 3"

        return response

    MathGameNode = rc.library.from_function(MathGame)

    with rc.Runner() as runner:
        _ = await runner.run(MathGameNode, message_history=rc.llm.MessageHistory([rc.llm.UserMessage("You can start the game")]))
