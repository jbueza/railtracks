import concurrent.futures
import time
import pytest

from requestcompletion.execution.publisher import Subscriber, RCPublisher


def test_basic_sub():
    number = None

    def callback(n: int):
        nonlocal number
        number = n

    sub = Subscriber(callback)

    assert sub.callback == callback

    sub.trigger(42)

    assert number == 42


def test_sleep_sub():
    text = None

    def callback(t: str):
        nonlocal text
        time.sleep(0.2)
        text = t

    sub = Subscriber(callback)
    assert sub.callback == callback
    sub.trigger("Hello, World!")
    assert text == "Hello, World!"


@pytest.mark.timeout(0.5)
def test_basic_publisher():
    with RCPublisher() as publisher:
        _message = None

        def callback(message: str):
            nonlocal _message
            _message = message

        publisher.subscribe(callback)
        publisher.publish("hello world")

        while _message is None:
            time.sleep(0.000001)

        assert _message == "hello world"


@pytest.mark.timeout(0.5)
def test_many_publishers():
    with RCPublisher() as publisher:
        _message_1 = None
        _message_2 = None

        def callback1(message: str):
            nonlocal _message_1
            _message_1 = message

        def callback2(message: str):
            nonlocal _message_2
            _message_2 = message

        publisher.subscribe(callback1)
        publisher.subscribe(callback2)
        publisher.publish("hello world")

        while _message_1 is None and _message_2 is None:
            time.sleep(0.000001)

        assert _message_1 == "hello world"
        assert _message_2 == "hello world"


@pytest.mark.timeout(1)
def test_blocking_publisher():
    with RCPublisher() as publisher:
        _message = []

        def callback(message: str):
            nonlocal _message
            time.sleep(0.1)
            _message.append((time.time(), message))

        publisher.subscribe(callback)
        publisher.publish("hello world")
        publisher.publish("second")

        while len(_message) < 2:
            time.sleep(0.000001)

        assert _message[0][1] == "hello world"
        assert _message[1][1] == "second"
        assert _message[0][0] < _message[1][0], "Messages should be processed in order."
        assert (
            abs(_message[1][0] - _message[0][0] - 0.1) < 0.02
        ), "Messages should be processed with a delay of 0.1 seconds roughly"


def test_multiple_subs_with_blocking():
    with RCPublisher() as publisher:
        _message_1 = []
        _message_2 = []

        def callback1(message: str):
            nonlocal _message_1
            time.sleep(0.1)
            _message_1.append((time.time(), message))

        def callback2(message: str):
            nonlocal _message_2
            _message_2.append((time.time(), message))

        publisher.subscribe(callback1)
        publisher.subscribe(callback2)
        publisher.publish("hello world")
        publisher.publish("second")

        while len(_message_1) < 2 or len(_message_2) < 2:
            time.sleep(0.000001)

        assert (
            abs(_message_1[0][0] - _message_2[0][0] - 0.1) < 0.02
        ), "Messages should be processed with a delay of 0.1 seconds roughly"
        assert (
            abs(_message_2[1][0] - _message_2[0][0] - 0.1) < 0.02
        ), "Second message should be delayed because of the other blocking operation"


def test_unsubscribe():
    with RCPublisher() as publisher:
        _message = None

        def callback(message: str):
            nonlocal _message
            _message = message

        identifier = publisher.subscribe(callback)
        publisher.publish("hello world")

        while _message is None:
            time.sleep(0.000001)

        assert _message == "hello world"

        publisher.unsubscribe(identifier)
        _message = None
        publisher.publish("this should not be received")

        time.sleep(0.1)  # Give some time to process the message

        assert _message is None, "Unsubscribed subscriber should not receive messages."


def test_bad_unsubscribe():
    with RCPublisher() as publisher:
        with pytest.raises(KeyError):
            # Attempting to unsubscribe a non-existent subscriber should raise KeyError
            publisher.unsubscribe("nonexistent_id")


def test_bad_subscribe():
    with RCPublisher() as publisher:

        def sample_sub(message: str):
            pass

        publisher.subscribe(sample_sub)
        with pytest.raises(KeyError):
            publisher.unsubscribe("not_a_callable")


def test_exception_thrower():
    with RCPublisher() as publisher:

        def exception_thrower(message: str):
            raise ValueError("This is a test exception")

        _message = None

        def callback(message: str):
            nonlocal _message
            _message = message

        publisher.subscribe(callback)
        publisher.subscribe(exception_thrower)

        publisher.publish("hello world")

        publisher.publish("another message")

        time.sleep(0.1)
        assert (
            _message == "another message"
        ), "Callback should still receive messages even if one subscriber throws an exception"


def test_listener_simple():
    with RCPublisher() as publisher:
        _message = None

        def callback(message: str):
            nonlocal _message
            _message = message

        publisher.subscribe(callback)

        def message_filter(message: str) -> bool:
            return message == "hello world"

        future = publisher.listener(message_filter)

        publisher.publish("hello world")
        result = future.result()

        assert result == "hello world"
        assert _message == "hello world"


def test_listener_many_messages():
    with RCPublisher() as pub:
        hw_listener = pub.listener(lambda x: x == "hello world")

        am_listener = pub.listener(lambda x: x == "another message")

        pub.publish("lala")
        pub.publish("hello world")
        assert hw_listener.result() == "hello world"
        pub.publish("another message")
        assert am_listener.result() == "another message"
        pub.publish("hello world")


def test_precheck_listener():
    with RCPublisher() as pub:
        hw_listener = pub.listener(lambda x: x == "hello world")

        pub.publish("lala")
        with pytest.raises(concurrent.futures.TimeoutError):
            hw_listener.result(timeout=0.1)


def test_get_listener_after_shutdown():
    with RCPublisher() as pub:
        hw_listener = pub.listener(lambda x: x == "hello world")

        pub.publish("greenery")

    with pytest.raises(ValueError):
        hw_listener.result()  # Should raise an error since the publisher is shutdown
