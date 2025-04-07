import pytest
import src.requestcompletion as rc
import random

def encoder(text: str) -> bytes:
    """Encodes a string into bytes.
    Args:
        text (str): The string to encode.
    Returns:
        bytes: The encoded string as bytes.
    """
    return text.encode("utf-8")

import random

def random_byte_operation(data: bytes) -> bytes:
    """
    Performs a random operation on the input bytes object.
    Args:
        data (bytes): The bytes object to operate on.

    Returns:
        bytes: The resulting bytes object after the random operation.
    """
    num = random.randint(0, 4)
    print(num)
    match num:
        case 0:
            # Reverse the byte order
            return data[::-1]
        case 1:
            # Add 2 to each byte (ensure values stay in 0-255)
            return bytes((x + 2) % 256 for x in data)
        case 2:
            # repeat each byte twice
            return bytes(x for x in data for _ in range(2))
        case 3:
            # Rotate left by 1
            return data[1:] + data[:1] if data else b""
        case 4:
            # XOR each byte with 0xAA
            return bytes(x ^ 0xAA for x in data)


def decoder(bytes: bytes) -> str:
    """Decodes a bytes object into a string.
    Args:
        bytes (bytes): The bytes object to decode.
    Returns:
        str: The decoded string.
    """
    return bytes.decode("utf-8", errors='replace')


if __name__ == "__main__":
    x = encoder("hello world")
    y = random_byte_operation(x)
    z = decoder(y)
    print(z)