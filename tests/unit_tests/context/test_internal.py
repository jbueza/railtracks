import pytest
from unittest import mock
from requestcompletion.context.internal import InternalContext

class DummyPublisher:
    def __init__(self, running=True):
        self._running = running
    def is_running(self):
        return self._running

def test_internal_context_properties(dummy_executor_config):

    pub = DummyPublisher()
    ctx = InternalContext(
        runner_id="runner-1",
        publisher=pub,
        parent_id="parent-1",
        executor_config=dummy_executor_config,
    )
    assert ctx.runner_id == "runner-1"
    assert ctx.parent_id == "parent-1"
    assert ctx.publisher is pub
    assert ctx.executor_config is dummy_executor_config
    assert ctx.is_active is True

def test_internal_context_setters(dummy_executor_config):
    ctx = InternalContext(
        runner_id=None,
        publisher=None,
        parent_id=None,
        executor_config=dummy_executor_config,
    )
    ctx.runner_id = "r2"
    ctx.parent_id = "p2"
    pub = DummyPublisher()
    ctx.publisher = pub
    new_config = mock.Mock()
    ctx.executor_config = new_config
    assert ctx.runner_id == "r2"
    assert ctx.parent_id == "p2"
    assert ctx.publisher is pub
    assert ctx.executor_config is new_config

def test_is_active_false_when_no_publisher(dummy_executor_config):
    ctx = InternalContext(
        runner_id="r",
        publisher=None,
        parent_id="p",
        executor_config=dummy_executor_config,
    )
    assert ctx.is_active is False

def test_is_active_false_when_publisher_not_running(dummy_executor_config):
    pub = DummyPublisher(running=False)
    ctx = InternalContext(
        runner_id="r",
        publisher=pub,
        parent_id="p",
        executor_config=dummy_executor_config,
    )
    assert ctx.is_active is False

def test_prepare_new_creates_new_context(dummy_executor_config):
    pub = DummyPublisher()
    ctx = InternalContext(
        runner_id="r",
        publisher=pub,
        parent_id="old-parent",
        executor_config=dummy_executor_config,
    )
    new_ctx = ctx.prepare_new("new-parent")
    assert isinstance(new_ctx, InternalContext)
    assert new_ctx.parent_id == "new-parent"
    assert new_ctx.publisher is pub
    assert new_ctx.runner_id == ctx.runner_id
    assert new_ctx.executor_config is ctx.executor_config
