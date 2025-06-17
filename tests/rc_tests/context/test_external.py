import pytest
from requestcompletion.context.external import (
    ImmutableExternalContext,
    ImmutableContextError,
)


def test_simple_empty():
    context = ImmutableExternalContext()

    with pytest.raises(KeyError):
        context.get("test_key")

    with pytest.raises(ImmutableContextError):
        context.put("test_key", "test_value")


def test_simple_load_in():
    context = ImmutableExternalContext()
    context.define({"test_key": "test_value"})

    assert context.get("test_key") == "test_value"
    assert context.get("non_existent_key", default="default_value") == "default_value"

    with pytest.raises(KeyError):
        context.get("non_existent_key")

    with pytest.raises(ImmutableContextError):
        context.put("test_key", "new_value")


def test_double_load_in():
    context = ImmutableExternalContext()
    context.define({"test_key": "test_value"})

    with pytest.raises(RuntimeError):
        context.define({"another_key": "another_value"})
