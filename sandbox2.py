import concurrent.futures
import time
from src.requestcompletion.state.execute import Result


class Node:
    def invoke(self):
        # print("Node invoked")
        time.sleep(1)
        return "result"


node = Node()
request_id = "12345"


def handler(response):
    # print("Handler called with response:", response)
    return response.result if response.result else response.error


def wrapped_func():
    # setting the context variables for the thread of interest.

    print(f"Running {node} in {request_id}")
    try:
        result = node.invoke()
        response = Result(request_id, node=node, result=result)
    except Exception as e:
        response = Result(request_id, node=node, error=e)
    finally:
        returned_result = handler(response)
        if isinstance(returned_result, Exception):

            raise returned_result

    return returned_result


with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    future = executor.submit(wrapped_func)
    future2 = executor.submit(wrapped_func)

    print(future.result(), future2.result())
