import json
import pathlib
import socket
import sys
import threading
from dataclasses import asdict, dataclass
from typing import *

from src.server.server import Peer
from src.utils.http import (
    FAIL_CODE,
    FAIL_RESPONSE,
    SUCCESS_CODE,
    HTTPRequest,
    HTTPResponse,
    http_response,
)
from src.utils.utils import recv_message, send_message


@dataclass
class RFC:
    number: int
    title: str
    hostname: Peer
    path: pathlib.Path


RFC_INDEX: list[RFC] = []


def load_rfc_index(response: HTTPResponse):
    data = json.loads(response.content.decode())
    return [RFC(**i) for i in data]


def dump_rfc_index(rfc_index: list[RFC]):
    return json.dumps([asdict(i) for i in rfc_index], default=str)


@http_response
def rfc_query(request: HTTPRequest):
    return SUCCESS_CODE, {}, dump_rfc_index(RFC_INDEX)


@http_response
def get_rfc(request: HTTPRequest):
    rfc_number = int(request.headers.get("RFC"))

    rfcs = [i for i in RFC_INDEX if i.number == rfc_number]

    if len(rfcs) == 0:
        return FAIL_CODE

    return SUCCESS_CODE, {}, json.dumps(asdict(rfcs[0]))


def server_receiver(peer_socket: socket.socket) -> None:
    def handle(request: HTTPRequest) -> bytes:
        match request.command.lower():
            case "rfcquery":
                return rfc_query(request)
            case "getrfc":
                return get_rfc(request)
            case _:
                return FAIL_RESPONSE()

    try:
        while request := HTTPRequest(recv_message(peer_socket)):
            response = handle(request)
            send_message(response, peer_socket)
    except Exception as e:
        print(e)
        pass
    finally:
        peer_socket.close()
        sys.exit(0)


def server(hostname: str, port: str) -> None:
    address = (hostname, port)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(address)
    server_socket.listen(10)

    try:
        while True:
            conn, _ = server_socket.accept()
            t = threading.Thread(target=server_receiver, args=(conn,))
            t.start()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    server()
