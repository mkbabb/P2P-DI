import pathlib
import socket
import sys
import threading
from enum import Enum, auto
from typing import *

from p2p_di.peer.rfc import RFC, dump_rfc, dump_rfc_index
from p2p_di.registration_server.server import TIMEOUT
from p2p_di.utils.http import (
    FAIL_RESPONSE,
    SUCCESS_CODE,
    HTTPRequest,
    http_response,
    make_response,
)
from p2p_di.utils.utils import receive_message, send_message, timethat


class P2PCommands(Enum):
    rfcquery = auto()
    getrfc = auto()
    leave = auto()


@http_response
def rfc_query(request: HTTPRequest, rfc_index: set[RFC]):
    return SUCCESS_CODE, {}, dump_rfc_index(rfc_index)


@timethat
def get_rfc(
    request: HTTPRequest, rfc_index: set[RFC], peer_socket: socket.socket
) -> Optional[bytes]:
    rfc_number = int(request.headers["RFC-Number"])
    rfcs = [i for i in rfc_index if i.number == rfc_number]

    if len(rfcs) == 0:
        return FAIL_RESPONSE()

    rfc = rfcs[0]
    filepath = pathlib.Path(rfc.path)

    if not filepath.is_file():
        return FAIL_RESPONSE()

    response = make_response(SUCCESS_CODE, body=dump_rfc(rfc))
    send_message(response, peer_socket)

    with filepath.open("rb") as file:
        return make_response(SUCCESS_CODE, body=file.read())


def server_receiver(rfc_index: set[RFC], peer_socket: socket.socket) -> None:
    def handle(request: HTTPRequest) -> bytes:
        match (command := P2PCommands[request.command.lower()]):
            case P2PCommands.rfcquery:
                return rfc_query(request, rfc_index)
            case P2PCommands.getrfc:
                return get_rfc(
                    request,
                    rfc_index,
                    peer_socket,
                )
            case P2PCommands.leave:
                raise Exception("Peer leaving")
            case _:
                return FAIL_RESPONSE()

    try:
        while message := receive_message(peer_socket):
            request = HTTPRequest(message)
            if (response := handle(request)) is not None:
                send_message(response, peer_socket)

    except Exception as e:
        print("Peer: ", e, file=sys.stderr)
    finally:
        peer_socket.close()
        sys.exit(0)


def server(
    hostname: str,
    port: str,
    rfc_index: set[RFC] = None,
) -> None:
    address = (hostname, port)
    print(f"Started peer server on {address}")

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(address)
    server_socket.listen(32)

    if rfc_index is None:
        rfc_index: set[RFC] = set()

    try:
        while True:
            conn, _ = server_socket.accept()
            t = threading.Thread(
                target=server_receiver,
                args=(rfc_index, conn),
            )
            t.start()
    except KeyboardInterrupt:
        pass
