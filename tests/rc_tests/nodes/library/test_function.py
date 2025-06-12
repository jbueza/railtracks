"""
Tests for the FunctionNode and from_function functionality.

This module tests the ability to create nodes from functions with various parameter types:
- Simple primitive types (int, str)
- Pydantic models
- Complex types (Tuple, List, Dict)
"""

import pytest
from typing import Tuple, List, Dict
from pydantic import BaseModel, Field
import time

from requestcompletion.state.request import Failure
import requestcompletion as rc
from requestcompletion.nodes.library import from_function

simple_test_inputs = [
    ("5", type("5")),
    (5, type(5)),
    (5.0, type(5.0)),
    (True, type(True)),
    ((1,2,3), type((1,2,3))),
    (None, type(None)),
    ([5,4,3,2,1], type([5,4,3,2,1])),
    ({"key": "value"}, type({"key": "value"})),
]

arg_test_inputs =   [
    (("5", 5, 5.0), [type("5"), type(5), type(5.0)]),
    ((["5", "5"], {"key": "value"}, (1, 2, 3)), [type(["5", "5"]), type({"key": "value"}), type((1, 2, 3))]),
]

kwarg_test_inputs = [
    ({"first": "5", "second": 5, "third": 5.0}, [type("5"), type(5), type(5.0)]),
    ({"first": ["5", "5"], "second": {"key": "value"}, "third": (1, 2, 3)}, [type(["5", "5"]), type({"key": "value"}), type((1, 2, 3))]),
]

def func_type(arg):
    return type(arg)

def func_multiple_types(*args):
    return [type(arg) for arg in args]

def func_multiple_ktypes(**kwargs):
    return [type(kwargs[kwarg]) for kwarg in kwargs]

# ===== Test Models =====

# Define model providers to test with
MODEL_PROVIDERS = ["openai"]

# ===== Test Classes =====
class TestPrimitiveInputTypes:
    def test_empty_function(self):
        """Test that a function with no parameters works correctly."""
        def empty_function() -> str:
            """
            Returns:
                str: A simple string indicating the function was called.
            """
            return "This is an empty function."
        testNode = from_function(empty_function)
        with rc.Runner() as run:
            result = run.run_sync(testNode).answer
        assert "This is an empty function." == result
        

    @pytest.mark.parametrize("input, expected_output", simple_test_inputs)
    def test_single_int_input(self, input, expected_output):
        """Test that a function with a single int parameter works correctly."""
        testNode = from_function(func_type)
        with rc.Runner() as run:
            assert run.run_sync(testNode, input).answer == expected_output

    @pytest.mark.parametrize("model_provider", MODEL_PROVIDERS)
    def test_builtin_function_raises_error(self, model_provider, create_top_level_node):
        """Test that a builtin function raises error before attempting to interface with LLM."""

        with pytest.raises(ValueError):
            agent = create_top_level_node(time.sleep, model_provider=model_provider)
            with rc.Runner(rc.ExecutorConfig(logging_setting="NONE")) as run:
                response = run.run_sync(
                    agent,
                    rc.llm.MessageHistory(
                        [rc.llm.UserMessage("Try to run this function")]
                    ),
                )


class TestSequenceInputTypes:
    @pytest.mark.parametrize("input, expected_output", arg_test_inputs)
    def test_multi_arg_input(self, input, expected_output):
        """Test that a function with multiple arg parameters works correctly."""
        testNode = from_function(func_multiple_types)
        with rc.Runner() as run:
            assert run.run_sync(testNode, *input).answer == expected_output

    @pytest.mark.parametrize("input, expected_output", kwarg_test_inputs)
    def test_multi_kwarg_input(self, input, expected_output):
        """Test that a function with multiple kwarg parameters works correctly."""
        testNode = from_function(func_multiple_ktypes)
        with rc.Runner() as run:
            assert run.run_sync(testNode, **input).answer == expected_output
