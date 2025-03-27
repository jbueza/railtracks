import pytest
from copy import deepcopy
import src.requestcompletion as rc
from tests.rc_tests.fixtures.nodes import ActionType, CapitalizeText, FatalErrorNode, UnknownErrorNode, TimeoutNode

@pytest.fixture
def model():
    return rc.llm.OpenAILLM("gpt-4o")

@pytest.mark.asyncio
async def test_message_history_not_mutated_terminal_llm(model):
    """
    Verify that message history is not modified after rc.call when passed to a terminal_llm node (test both wrapper and class version).
    """
    system_rng = rc.llm.SystemMessage(
        "You are a random integer generator that will return a random list of integers between 0 and 100. Do not return more than 10 integers."
    )
    system_rng_operation = rc.llm.SystemMessage(
        "You are a random mathematical operation calculator that will apply a random operation to the list of integers that will be provided by the user and return the result. The answer should be only a single integer."
    )
    system_math_genius = rc.llm.SystemMessage(
        "You are a math genius that will get a list of integers(loi) and another interger(x), your task is to predict what operation must be appled to the list of integers to get the result of x."
    )

    RNGNode = rc.library.terminal_llm("RNG Node", system_message=system_rng, model=model)                   
    RNGOperationNode = rc.library.terminal_llm("RNG Operation Node", system_message=system_rng_operation, model=model)

    class MathDetectiveNode(rc.library.TerminalLLM):
        def __init__(
            self,
            message_history: rc.llm.MessageHistory,
            llm_model: rc.llm.ModelBase,
        ):
            super().__init__(message_history=message_history, model=llm_model)

        def pretty_name(self) -> str:
            return "Math Detective Node"

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
        _ = await runner.run(MathGameNode, 
                             message_history=rc.llm.MessageHistory([
                                system_math_genius,
                                rc.llm.UserMessage("You can start the game"),
                            ]))


async def test_multiple_parameter_types_not_mutated():
    """
    Verify that different types of parameters are not mutated when passed to a node.
    """
    # Create sample parameters of different types
    original_dict = {"key": "value"}
    original_list = [1, 2, 3]
    original_str = "test string"
    original_int = 42

    # Create deep copies to compare against
    dict_copy = deepcopy(original_dict)
    list_copy = deepcopy(original_list)
    str_copy = deepcopy(original_str)
    int_copy = deepcopy(original_int)

    # Create a custom test node that takes multiple parameter types
    class MultiParamNode(rc.Node):
        async def __call__(self, test_dict: dict, test_list: list, test_str: str, test_int: int):
            return {"answer": "processed"}

    # Run the call
    with rc.Runner() as run:
        result = run.run_sync(
            rc.call(
                MultiParamNode,
                test_dict=original_dict,
                test_list=original_list,
                test_str=original_str,
                test_int=original_int,
            )
        )

    # Assert that each original parameter remains unchanged
    assert original_dict == dict_copy, "Dictionary should not be modified"
    assert original_list == list_copy, "List should not be modified"
    assert original_str == str_copy, "String should not be modified"
    assert original_int == int_copy, "Integer should not be modified"


def test_immutable_parameter_preservation():
    """
    Verify that immutable parameters are preserved across node calls.
    """

    # Create a custom node that attempts to modify an immutable parameter
    class ImmutableParamNode(rc.Node):
        async def __call__(self, immutable_param: int):
            # Attempt to modify the parameter (this should not affect the original)
            immutable_param += 1
            return {"answer": immutable_param}

    original_value = 10

    # Run the call
    with rc.Runner() as run:
        result = run.run_sync(rc.call(ImmutableParamNode, immutable_param=original_value))

    # Assert that the original value remains unchanged
    assert original_value == 10, "Immutable parameter should not be modified"


async def test_nested_structure_not_mutated():
    """
    Verify that nested data structures are not mutated when passed to a node.
    """
    # Create a complex nested structure
    original_nested_structure = {
        "users": [
            {"name": "Alice", "details": {"age": 30, "interests": ["reading"]}},
            {"name": "Bob", "details": {"age": 25, "interests": ["coding"]}},
        ],
        "settings": {"theme": "dark", "notifications": True},
    }

    # Create a deep copy to compare against
    nested_structure_copy = deepcopy(original_nested_structure)

    # Create a custom node that takes a nested structure
    class NestedStructureNode(rc.Node):
        async def __call__(self, complex_param: dict):
            # Attempt to modify the nested structure
            if complex_param["users"]:
                complex_param["users"][0]["name"] = "Modified"
            return {"answer": "processed"}

    # Run the call
    with rc.Runner() as run:
        result = run.run_sync(rc.call(NestedStructureNode, complex_param=original_nested_structure))

    # Assert that the original nested structure remains unchanged
    assert original_nested_structure == nested_structure_copy, "Nested structure should not be modified"
