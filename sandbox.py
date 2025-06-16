import asyncio
import concurrent.futures
import time

import requestcompletion as rc

#
#
# def timeout(seconds: int):
#     time.sleep(seconds)
#     return seconds
#
#
# TimeoutNode = rc.library.from_function(timeout)
#
#
# def top_level(num: int):
#     futs = [rc.call_sync(TimeoutNode, 1) for _ in range(num)]
#     return futs
#
#
# TopLevel = rc.library.from_function(top_level)
#
# with rc.Runner() as runner:
#     result = runner.run_sync(TopLevel, 5)
#     print(result.answer)


class ParentClass:
    def __init__(self):
        pass


class ExampleClass(ParentClass):
    def __init__(self):
        self.subscribers = {}

    def start_topic(self, topic: str):
        if topic not in self.subscribers:
            self.subscribers[topic] = []

    def subscribe(self, topic: str, callback: callable):
        if topic not in self.subscribers:
            raise ValueError(
                f"Topic '{topic}' does not exist. Please start the topic first."
            )
        self.subscribers[topic].append(callback)

    def publish(self, topic: str, message: any):
        if topic not in self.subscribers:
            raise ValueError(
                f"Topic '{topic}' does not exist. Please start the topic first."
            )

        for callback in self.subscribers[topic]:
            futs = []
            with concurrent.futures.ThreadPoolExecutor() as executor:
                f = executor.submit(callback(message))
                futs.append(f)

            concurrent.futures.wait(futs)

        return


# Example usage
if __name__ == "__main__":
    pubsub = ExampleClass()
    pubsub.start_topic("example_topic")

    def example_callback(message):
        print(f"Received message: {message}")

    pubsub.subscribe("example_topic", example_callback)

    pubsub.publish("example_topic", "Hello, World!")
