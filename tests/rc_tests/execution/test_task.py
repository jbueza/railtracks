import requestcompletion as rc


def hello_world():
    print("Hello, World!")


HelloWorldNode = rc.library.from_function(hello_world)


def test_task_invoke():
    hwn = HelloWorldNode()
    task = rc.execution.task.Task(node=hwn, request_id="test_request_id")

    assert task.node == hwn
    assert task.request_id == "test_request_id"
