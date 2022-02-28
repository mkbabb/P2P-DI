import socket
from typing import *

HEADER_SIZE = 10
CHUNK_SIZE = 1024


def parse_message(message: bytes, header_size: int = HEADER_SIZE) -> tuple[int, bytes]:
    if len(message) == 0:
        return 0, message
    else:
        message_length = int(message[:header_size].decode())
        data = message[header_size:]
        return message_length, data


def recv_message(
    peer_socket: socket.socket,
    header_size: int = HEADER_SIZE,
    chunk_size: int = CHUNK_SIZE,
) -> bytes:
    message = b""
    t_message = peer_socket.recv(header_size)
    message_len, _ = parse_message(t_message, header_size)

    while message_len > 0:
        chunk_size = min(chunk_size, message_len)
        message_len -= chunk_size

        response = peer_socket.recv(chunk_size, )
        message += response

    return message


def send_message(
    data: bytes, peer_socket: socket.socket, header_size: int = HEADER_SIZE
) -> int:
    header = f"{len(data):<{header_size}}"
    message = header.encode() + data
    return peer_socket.send(message)
