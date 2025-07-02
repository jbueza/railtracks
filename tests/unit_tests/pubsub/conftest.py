import pytest
import asyncio
from unittest.mock import patch
from requestcompletion.pubsub.publisher import Publisher, RCPublisher

@pytest.fixture
def sync_callback_container():
    """Container for a simple mutable value, with a registered callback function."""
    state = {'value': None}
    def callback(x):
        state['value'] = x
    return state, callback

@pytest.fixture
def async_callback_container():
    state = {'value': None}
    async def callback(x):
        await asyncio.sleep(0.01)
        state['value'] = x
    return state, callback

@pytest.fixture
def msg_list_container():
    """For collecting callback messages in order."""
    state = []
    def callback(x):
        state.append(x)
    return state, callback

@pytest.fixture
async def started_publisher():
    """Auto-started instance of Publisher (shuts down after)."""
    pub = Publisher()
    await pub.start()
    yield pub
    await pub.shutdown()

@pytest.fixture
async def async_publisher():
    async with Publisher() as pub:
        yield pub

@pytest.fixture
def streamed_object():
    class DummyStream: pass
    return DummyStream()

@pytest.fixture
def streaming_message(streamed_object):
    from requestcompletion.pubsub.messages import Streaming
    return Streaming(streamed_object)

@pytest.fixture
def dummy_publisher():
    pub = RCPublisher()
    return pub

@pytest.fixture
def logger_patch():
    with patch("requestcompletion.pubsub.publisher.logger") as mock_logger:
        yield mock_logger