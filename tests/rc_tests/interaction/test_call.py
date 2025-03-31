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

@pytest.fixture
def initial_message_history():
    return rc.llm.MessageHistory([rc.llm.UserMessage("You can start the game")])

@pytest.fixture
def math_game_factory():
    """
    Creates a math game node factory that generates a MathGame function and node
    based on the provided node implementations.
    """
    def _create_math_game(rng_node, rng_operation_node, math_detective_node, model=None):
        async def MathGame(message_history: rc.llm.MessageHistory):
            original_message_history = deepcopy(message_history)

            # Common parameters for node calls
            call_params = {"message_history": message_history}
            if model:
                call_params["llm_model"] = model

            # First node call
            random_num_list_response = await rc.call(rng_node, **call_params)
            assert all(orig.content == new.content for orig, new in zip(original_message_history, message_history)), "Message history modified after rc.call 1"

            message_history.append(rc.llm.AssistantMessage("The list of random integer: " + str(random_num_list_response)))
            original_message_history.append(rc.llm.AssistantMessage("The list of random integer: " + str(random_num_list_response)))

            # Second node call
            operation_response = await rc.call(rng_operation_node, **call_params)
            assert all(orig.content == new.content for orig, new in zip(original_message_history, message_history)), "Message history modified after rc.call 2"

            message_history.append(rc.llm.AssistantMessage("The result int (x) = " + str(operation_response)))
            original_message_history.append(rc.llm.AssistantMessage("The result int (x) = " + str(operation_response)))

            # Third node call
            response = await rc.call(math_detective_node, **call_params)
            assert all(orig.content == new.content for orig, new in zip(original_message_history, message_history)), "Message history modified after rc.call 3"

            return response

        return rc.library.from_function(MathGame)
    
    return _create_math_game

@pytest.fixture
def easy_wrapper_nodes(model, terminal_llms_system_messages):
    """
    Creates nodes using the easy wrapper method (terminal_llm function).
    """
    system_rng, system_rng_operation, system_math_genius = terminal_llms_system_messages
    
    rng_node = rc.library.terminal_llm("RNG Node", system_message=system_rng, model=model)     
    rng_operation_node = rc.library.terminal_llm("RNG Operation Node", system_message=system_rng_operation, model=model)
    math_detective_node = rc.library.terminal_llm("Math Detective Node", system_message=system_math_genius, model=model)
    
    return rng_node, rng_operation_node, math_detective_node

@pytest.fixture
def class_based_nodes(terminal_llms_system_messages):
    """
    Creates nodes using the class-based method.
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

    rng_node = make_terminal_llm_class_version("RNG Node", system_message=system_rng)   
    rng_operation_node = make_terminal_llm_class_version("RNG Operation Node", system_message=system_rng_operation)
    math_detective_node = make_terminal_llm_class_version("Math Detective Node", system_message=system_math_genius)
    
    return rng_node, rng_operation_node, math_detective_node

@pytest.mark.asyncio
@pytest.mark.parametrize("node_fixture_name", ["class_based_nodes", "easy_wrapper_nodes"])
async def test_message_history_not_mutated_terminal_llm(model, request, node_fixture_name, math_game_factory, initial_message_history):
    """
    Verify that message history is not modified after rc.call when passed to nodes constructed using different methods.
    """
    # Get the fixture by name using the request object
    nodes = request.getfixturevalue(node_fixture_name)
    rng_node, rng_operation_node, math_detective_node = nodes
    
    # For class_based_nodes, we need to pass the model
    needs_model = node_fixture_name == "class_based_nodes"
    math_game_node = math_game_factory(rng_node, rng_operation_node, math_detective_node, model if needs_model else None)

    with rc.Runner() as runner:
        _ = await runner.run(math_game_node, message_history=initial_message_history)