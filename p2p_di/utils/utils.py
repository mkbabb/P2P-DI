from datetime import datetime
from functools import wraps
import socket
from typing import *

HEADER_SIZE = 8
CHUNK_SIZE = 2**10


def parse_header(message: bytes, header_size: int = HEADER_SIZE) -> tuple[int, bytes]:
    if len(message) == 0:
        return len(message), message
    return int(message[:header_size].decode()), message[header_size:]


def receive_message(
    sock: socket.socket,
    header_size: int = HEADER_SIZE,
    chunk_size: int = CHUNK_SIZE,
) -> bytes:
    message = b""
    t_message = sock.recv(header_size)
    message_len, header = parse_header(t_message, header_size)

    while message_len > 0:
        chunk_size = min(chunk_size, message_len)

        response = sock.recv(chunk_size)
        message += response

        message_len -= chunk_size

    return message


def send_message(
    data: bytes, sock: socket.socket, header_size: int = HEADER_SIZE
) -> int:
    message_len = len(data)
    message = f"{message_len:<{header_size}}".encode() + data
    return sock.send(message)


def timethat(func: Callable[..., Any]):
    total_time = 0

    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        nonlocal total_time
        start = datetime.now()
        result = func(*args, **kwargs)
        end = datetime.now()

        delta = (end - start).total_seconds() / 1000
        total_time += delta

        print(f"Timing for {func.__name__}")
        print(f"Took {delta}ms!")
        print(f"Total time: {total_time}")
        print()

        return result

    return wrapper
