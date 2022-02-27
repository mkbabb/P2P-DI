import pathlib
import socket
import threading
from typing import *

from src.server.server import PORT, TTL_INTERVAL, Peer, load_peer
from src.utils.http import HTTPResponse, http_request, send_recv_http_request

me: Peer = None

server_socket: socket.socket = None
peer_socket: socket.socket = None


@http_request
def register(hostname: str, port: int):
    return "Register", hostname, {"port": port}


@http_request
def leave(hostname: str, peer: Peer):
    return "Leave", hostname, {"Peer-Cookie": peer.cookie}


@http_request
def p_query(hostname: str, peer: Peer):
    return "Leave", hostname, {"Peer-Cookie": peer.cookie}


@http_request
def keep_alive(hostname: str, peer: Peer):
    return "KeepAlive", hostname, {"Peer-Cookie": peer.cookie}


@http_request
def rfc_query(peer: Peer):
    pass


@http_request
def get_rfc(peer: Peer):
    pass


def client_handler(hostname: str, port: int, commands: list[str]) -> None:
    def parse_response(command: str, response: HTTPResponse):
        global me

        match command.lower():
            case "register" | "keepalive":
                me = load_peer(response)
            case "pquery":
                pass

    def peer_to_server(command: str):
        request = None
        match command.lower():
            case "register":
                request = register(hostname=hostname, port=port)
            case "leave":
                request = leave(hostname=hostname, peer=me)
            case "pquery":
                request = p_query(hostname=hostname, peer=me)
            case "keepalive":
                request = keep_alive(hostname=hostname, peer=me)

        return send_recv_http_request(request=request, server_socket=server_socket)

    def peer_to_peer(command: str):
        match command:
            case "rfcquery":
                response = rfc_query(hostname=hostname)
            case "getrfc":
                pass

    def make_request(command: str):
        response = None

        match command.lower():
            case "register":
                response = register(hostname=hostname, port=port)
            case "leave":
                response = leave(hostname=hostname, peer=me)
            case "pquery":
                response = p_query(hostname=hostname, peer=me)
            case "keepalive":
                response = keep_alive(hostname=hostname, peer=me)

            case "rfcquery":
                response = rfc_query(hostname=hostname)
            case "getrfc":
                pass

        match response.status:
            case 200:
                parse_response(command=command, response=response)

    make_request("register")
    keep = threading.Timer(TTL_INTERVAL, make_request, ("keepalive",))
    keep.start()

    for command in commands:
        make_request(command)

    keep.cancel()


def client(hostname: str, port: int, commands: list[str]):
    global server_socket

    server_address = (hostname, PORT)

    with socket.create_connection(server_address) as sock:
        server_socket = sock
        print(f"Connected to server: {server_address}")

        client_handler(
            hostname=hostname,
            port=port,
            commands=commands,
        )


if __name__ == "__main__":
    hostname = socket.gethostname()
    port = 1234
    commands = ["pquery"]

    client(hostname, port, commands)
