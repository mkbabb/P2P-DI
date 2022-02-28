import datetime
import json
import socket
import sys
import threading
from dataclasses import asdict, dataclass, field
from typing import *

from src.utils.http import HTTPRequest, HTTPResponse, http_response
from src.utils.utils import recv_message, send_message

PORT = 65243

TTL = 7200
TTL_INTERVAL = 1.0

SUCCESS_CODE = 200
FAIL_CODE = 403


@dataclass
class Peer:
    hostname: str
    cookie: int
    port: int

    last_active_time: datetime.datetime = field(default_factory=datetime.datetime.now)
    registration_count: int = 0
    active: bool = True
    ttl: int = TTL

    def __post_init__(self):
        if isinstance(self.last_active_time, str):
            self.last_active_time = datetime.datetime.fromisoformat(
                self.last_active_time
            )


PEER_ID = 0
PEERS: dict[int, Peer] = {}


def load_peer(response: HTTPResponse):
    data = json.loads(response.content.decode())
    return Peer(**data)


def load_peers(response: HTTPResponse):
    data = [json.loads(i) for i in json.loads(response.content)]
    return [Peer(**peer_data) for peer_data in data]


def dump_peer(peer: Peer):
    return json.dumps(asdict(peer), default=str)


def get_active_peers():
    return {peer_id: peer for peer_id, peer in PEERS.items() if peer.active}


def decrement_peer_ttls():
    for peer in get_active_peers().values():
        if peer.ttl == 0:
            peer.active = False
        else:
            peer.ttl -= 1


@http_response
def register(request: HTTPRequest):
    global PEER_ID

    hostname = request.path
    port = int(request.headers["Port"])

    peer = Peer(hostname=hostname, cookie=PEER_ID, port=port)

    PEERS[PEER_ID] = peer

    PEER_ID += 1

    return SUCCESS_CODE, {}, dump_peer(peer)


@http_response
def leave(request: HTTPRequest):
    peer_cookie = int(request.headers["Peer-Cookie"])
    peer = PEERS.get(peer_cookie)

    if peer is None:
        return FAIL_CODE

    peer.active = False
    peer.ttl = 0

    return SUCCESS_CODE


def refresh_peer(peer_cookie: int):
    peer = PEERS.get(peer_cookie)

    if peer is None:
        return False

    peer.active = True
    peer.ttl = TTL

    return True


@http_response
def p_query(request: HTTPRequest):
    peer_cookie = int(request.headers["Peer-Cookie"])

    if not refresh_peer(peer_cookie):
        return FAIL_CODE

    active_peers = [
        dump_peer(peer)
        for peer in get_active_peers().values()
        if peer.cookie != peer_cookie
    ]
    body = json.dumps(active_peers)

    return SUCCESS_CODE, {}, body


@http_response
def keep_alive(request: HTTPRequest):
    peer_cookie = int(request.headers["Peer-Cookie"])

    if not refresh_peer(peer_cookie):
        return FAIL_CODE
    else:
        return SUCCESS_CODE, {}, dump_peer(PEERS[peer_cookie])


@http_response
def fail():
    return FAIL_CODE


def server_receiver(peer_socket: socket.socket) -> None:
    def handle(request: HTTPRequest) -> bytes:
        match request.command.lower():
            case "register":
                return register(request)
            case "leave":
                return leave(request)
            case "pquery":
                return p_query(request)
            case "keepalive":
                return keep_alive(request)
            case _:
                return fail()

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


def server() -> None:
    address = (socket.gethostname(), PORT)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(address)
    server_socket.listen(10)

    decrementer = threading.Timer(TTL_INTERVAL, decrement_peer_ttls)
    decrementer.start()

    try:
        while True:
            conn, _ = server_socket.accept()
            t = threading.Thread(target=server_receiver, args=(conn,))
            t.start()
    except KeyboardInterrupt:
        pass

    decrementer.cancel()


if __name__ == "__main__":
    server()
