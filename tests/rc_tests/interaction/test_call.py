import pytest
import copy
import requestcompletion as rc
from ..fixtures.nodes import ActionType, CapitalizeText, FatalErrorNode, UnknownErrorNode, TimeoutNode, RNGNode

async def test_message_history_not_mutated():
    """
    Verify that message history is not modified when passed to a node.
    """
    # Create an original message history
    original_message_history = [
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Hello, how are you?"}
    ]
    
    # Create a deep copy to compare against
    message_history_copy = copy.deepcopy(original_message_history)
    
    # Run the call and store the result
    with rc.Runner() as run:
        result = run.run_sync(rc.call(CapitalizeText, message_history=original_message_history))
    
    # Assert that the original message history remains unchanged
    assert original_message_history == message_history_copy, "Message history should not be modified"


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
    dict_copy = copy.deepcopy(original_dict)
    list_copy = copy.deepcopy(original_list)
    str_copy = copy.deepcopy(original_str)
    int_copy = copy.deepcopy(original_int)
    
    # Create a custom test node that takes multiple parameter types
    class MultiParamNode(rc.Node):
        async def __call__(self, 
                           test_dict: dict, 
                           test_list: list, 
                           test_str: str, 
                           test_int: int):
            return {"answer": "processed"}
    
    # Run the call
    with rc.Runner() as run:
        result = run.run_sync(
            rc.call(
                MultiParamNode, 
                test_dict=original_dict, 
                test_list=original_list, 
                test_str=original_str, 
                test_int=original_int
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
            {"name": "Bob", "details": {"age": 25, "interests": ["coding"]}}
        ],
        "settings": {
            "theme": "dark",
            "notifications": True
        }
    }
    
    # Create a deep copy to compare against
    nested_structure_copy = copy.deepcopy(original_nested_structure)
    
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