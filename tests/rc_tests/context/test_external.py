import pytest
from requestcompletion.context.external import (
    MutableExternalContext,
)


def test_simple_empty():
    context = MutableExternalContext()

    with pytest.raises(KeyError):
        context.get("test_key")

    context.put("test_key", "test_value")


def test_simple_load_in():
    context = MutableExternalContext()
    context.update({"test_key": "test_value"})

    assert context.get("test_key") == "test_value"
    assert context.get("non_existent_key", default="default_value") == "default_value"

    with pytest.raises(KeyError):
        context.get("non_existent_key")

    context.put("test_key", "new_value")


def test_double_load_in():
    context = MutableExternalContext()
    context.update({"test_key": "test_value"})

    context.update({"another_key": "another_value"})

    assert context.get("test_key") == "test_value"
    assert context.get("another_key") == "another_value"
