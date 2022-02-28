import json
import os
import pathlib
import socket
from sre_constants import SUCCESS
import sys
import threading
import time
from dataclasses import asdict, dataclass
from typing import *

from src.server.server import Peer
from src.utils.http import (
    FAIL_CODE,
    FAIL_RESPONSE,
    SUCCESS_CODE,
    SUCCESS_RESPONSE,
    TIME_FMT,
    HTTPRequest,
    HTTPResponse,
    http_response,
    make_request,
    make_response,
    send_recv_http_request,
)
from src.utils.utils import CHUNK_SIZE, recv_message, send_message


@dataclass
class RFC:
    number: int
    title: str
    hostname: Peer
    path: pathlib.Path


RFC_INDEX: set[RFC] = {}


def load_rfc(response: HTTPResponse | HTTPRequest):
    data = json.loads(response.content.decode())
    return RFC(**data)


def dump_rfc(rfc: RFC):
    return json.dumps(asdict(rfc))


def load_rfc_index(response: HTTPResponse | HTTPRequest):
    data = json.loads(response.content.decode())
    return [RFC(**i) for i in data]


def dump_rfc_index(rfc_index: list[RFC]):
    return json.dumps([asdict(i) for i in rfc_index], default=str)


@http_response
def rfc_query(request: HTTPRequest):
    return SUCCESS_CODE, {}, dump_rfc_index(RFC_INDEX)


def get_rfc(request: HTTPRequest, peer_socket: socket.socket) -> None:
    rfc_number = int(request.headers["RFC-Number"])
    rfcs = [i for i in RFC_INDEX if i.number == rfc_number]

    if len(rfcs) == 0:
        return FAIL_RESPONSE()

    rfc = rfcs[0]
    filepath = rfc.path

    if not filepath.is_file():
        return FAIL_RESPONSE()

    response = make_response(SUCCESS_CODE, body=dump_rfc(rfc))
    send_message(response, peer_socket)

    with filepath.open("r") as file:
        while d := file.read(CHUNK_SIZE):
            send_message(d.encode(), peer_socket)

    return SUCCESS_RESPONSE()


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
