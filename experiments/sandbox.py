import warnings

import requestcompletion as rc
from requestcompletion import ExecutorConfig
from requestcompletion.llm import MessageHistory, UserMessage

warnings.simplefilter("ignore", UserWarning)


def adder(x: int, y: int) -> int:
    """
    A simple function that adds two integers.

    Args:
        x (int): The first integer.
        y (int): The second integer.
    """
    return x + y

def multiplier(x: int, y: int) -> int:
    """
    A simple function that multiplies two integers.

    Args:
        x (int): The first integer.
        y (int): The second integer.
    """
    raise Exception("Mutiplier is broken, use other functions to calculate the result")

    return x * y



Add = rc.library.from_function(adder)
Multiply = rc.library.from_function(multiplier)

Calc = rc.library.tool_call_llm(
    connected_nodes={Multiply, Add},
    model=rc.llm.OpenAILLM("gpt-4o"),
    system_message="You are a master calculator capable of complicated reasoning. You are given too elementary operations which you can use to solve more complicated operations. You should rely on the tools and not your own math skills")

if __name__ == "__main__":
    with rc.Runner(executor_config=ExecutorConfig(log_file="../.logs/example.log", logging_setting="QUIET"), ) as run:
        result = rc.call_sync(Calc, MessageHistory([UserMessage("What is 5 * 5")]))

