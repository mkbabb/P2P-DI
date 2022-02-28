import json
import socket
import sys
import threading
from enum import Enum, auto
from typing import *

from src.peer.peer import TTL_INTERVAL, PeerIndex, dump_peer
from src.utils.http import (
    FAIL_CODE,
    FAIL_RESPONSE,
    SUCCESS_CODE,
    HTTPRequest,
    http_response,
)
from src.utils.utils import recv_message, send_message

TIMEOUT = 2


class P2ServerCommands(Enum):
    register = auto()
    leave = auto()
    pquery = auto()
    keepalive = auto()


PORT = 65243


@http_response
def register(request: HTTPRequest, peer_index: PeerIndex):
    hostname = request.path
    port = int(request.headers["Port"])

    peer = peer_index.register(hostname, port)

    return SUCCESS_CODE, {}, dump_peer(peer)


@http_response
def leave(request: HTTPRequest, peer_index: PeerIndex):
    peer_cookie = int(request.headers["Peer-Cookie"])
    peer = peer_index.get(peer_cookie)

    if peer is None:
        return (FAIL_CODE,)

    peer.leave()

    return (SUCCESS_CODE,)


@http_response
def p_query(request: HTTPRequest, peer_index: PeerIndex):
    peer_cookie = int(request.headers["Peer-Cookie"])
    peer = peer_index.get(peer_cookie)
    if peer is None:
        return (FAIL_CODE,)

    peer.refresh()

    active_peers = [
        dump_peer(peer)
        for peer in peer_index.get_active_peers().values()
        if peer.cookie != peer_cookie
    ]
    body = json.dumps(active_peers)

    return SUCCESS_CODE, {}, body


@http_response
def keep_alive(request: HTTPRequest, peer_index: PeerIndex):
    peer_cookie = int(request.headers["Peer-Cookie"])
    peer = peer_index.get(peer_cookie)
    if peer is None:
        return (FAIL_CODE,)

    peer.refresh()

    return SUCCESS_CODE, {}, dump_peer(peer)


def server_receiver(peer_index: PeerIndex, peer_socket: socket.socket) -> None:
    def handle(request: HTTPRequest) -> bytes:
        match (command := P2ServerCommands[request.command.lower()]):
            case P2ServerCommands.register:
                return register(request, peer_index)
            case P2ServerCommands.leave:
                leave(request, peer_index)
                raise Exception("Peer leaving server.")
            case P2ServerCommands.pquery:
                return p_query(request, peer_index)
            case P2ServerCommands.keepalive:
                return keep_alive(request, peer_index)
            case _:
                return FAIL_RESPONSE()

    try:
        while message := recv_message(peer_socket):
            request = HTTPRequest(message)
            response = handle(request)
            send_message(response, peer_socket)
    except Exception as e:
        print("Server: ", e)
    finally:
        peer_socket.close()
        sys.exit(0)


def server() -> None:
    address = (socket.gethostname(), PORT)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(address)
    server_socket.listen(32)

    peer_index = PeerIndex()

    # decrement_peer_thread = threading.Timer(
    #     TTL_INTERVAL, peer_index.decrement_peer_ttls
    # )
    # decrement_peer_thread.start()

    

    try:
        while True:
            print("start")
            conn, _ = server_socket.accept()
            t = threading.Thread(
                target=server_receiver,
                args=(peer_index, conn),
            )
            t.start()
            print("stop")

    except KeyboardInterrupt:
        pass

    

    # decrement_peer_thread.cancel()


if __name__ == "__main__":
    server()
