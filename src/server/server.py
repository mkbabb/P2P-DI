import datetime
import json
import socket
import sys
import threading
from dataclasses import dataclass, field
from typing import *

from src.utils.http import HTTPRequest, HTTPResponse, make_response
from src.utils.utils import recv_message, send_message

PORT = 65243

TTL = 7200


@dataclass
class Peer:
    hostname: str
    cookie: int
    port: int

    last_active_time: datetime.datetime = field(default_factory=datetime.datetime.now)
    registration_count: int = 0
    active: bool = True
    ttl: int = TTL


PEER_ID = 0
PEERS: dict[int, Peer] = {}

SUCCESS_RESPONSE = make_response(status_code=200)
FAIL_RESPONSE = make_response(status_code=403)


def register(http_request: HTTPRequest):
    global PEER_ID

    hostname = http_request.path
    port = int(http_request.headers["Port"])

    peer = Peer(hostname=hostname, cookie=PEER_ID, port=port)

    PEERS[PEER_ID] = peer

    PEER_ID += 1

    return SUCCESS_RESPONSE


def leave(http_request: HTTPRequest):
    peer_cookie = int(http_request.headers["Peer-Cookie"])
    peer = PEERS.get(peer_cookie)

    if peer is None:
        return FAIL_RESPONSE

    peer.active = False
    peer.ttl = 0

    return SUCCESS_RESPONSE


def p_query(http_request: HTTPRequest):
    active_peers = {k: v for k, v in PEERS.items() if v.active}

    return make_response(status_code=200, body=json.dumps(active_peers))


def keep_alive(http_request: HTTPRequest):
    peer_cookie = int(http_request.headers["Peer-Cookie"])
    peer = PEERS.get(peer_cookie)

    if peer is None:
        return FAIL_RESPONSE

    peer.active = True
    peer.ttl = TTL

    return SUCCESS_RESPONSE


def server_receiver(peer_socket: socket.socket) -> None:
    def handle(http_request: HTTPRequest) -> str:
        match http_request.command:
            case "Register":
                return register(http_request)
            case "Leave":
                return leave(http_request)
            case "KeepAlive":
                return keep_alive
            case _:
                return FAIL_RESPONSE

    try:
        while request := recv_message(peer_socket):
            http_request = HTTPRequest(request)

            response = handle(http_request)
            send_message(response, peer_socket)

    except KeyboardInterrupt:
        pass

    peer_socket.close()
    sys.exit(0)


def server() -> None:
    address = (socket.gethostname(), PORT)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(address)
    server_socket.listen(32)

    try:
        while True:
            conn, _ = server_socket.accept()
            t = threading.Thread(target=server_receiver, args=(conn,))
            t.start()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    server()
