# my_node.py
import requestcompletion as rc
from requestcompletion.mcp.to_node import create_mcp_server


def add_nums(num1: int, num2: int, print_s: str):
    return num1 + num2 + 10


node = rc.library.from_function(add_nums)

if __name__ == "__main__":
    mcp = create_mcp_server([node])
    mcp.run(transport="streamable-http")
