import concurrent.futures
import time
import asyncio

from src.requestcompletion.execution.publisher import RCPublisher


def main():
    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            pub = RCPublisher()
            pub.subscribe(lambda msg: print(f"Received message: {msg}"))
            result = pub.listener(lambda msg: msg == "hello world")
            f = executor.submit(pub.publish, "Hello from the process pool!")
            f2 = executor.submit(pub.publish, "hello world")
            f3 = executor.submit(pub.publish, "Another message")
            f4 = executor.submit(pub.publish, "hello world")

            print(result.result())

    finally:
        pub.shutdown(True)


if __name__ == "__main__":
    main()
