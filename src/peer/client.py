import socket
import threading

from typing import *

from src.server.server import PORT, TTL_INTERVAL, Peer, load_peer, load_peers
from src.utils.http import BottleApp, HTTPResponse

me: Peer = None

app = BottleApp()
peer_app = BottleApp()


@app.request()
def register(port: int):
    return "Register", {"port": port}


@app.request()
def leave(peer: Peer):
    return "Leave", {"Peer-Cookie": peer.cookie}


@app.request()
def p_query(peer: Peer):
    return "PQuery", {"Peer-Cookie": peer.cookie}


@app.request()
def keep_alive(peer: Peer):
    return "KeepAlive", {"Peer-Cookie": peer.cookie}


@peer_app.request()
def rfc_query(peer: Peer):
    return "RFCQuery"


@peer_app.request()
def get_rfc(peer: Peer):
    pass


def client_handler(port: int, commands: list[tuple[str, list]]) -> None:
    def peer_to_server(command: str, args: dict):
        global me

        response = None
        match command:
            case "register":
                response = register(port=port)
            case "leave":
                response = leave(peer=me)
            case "pquery":
                response = p_query(peer=me)
            case "keepalive":
                response = keep_alive(peer=me)
            case _:
                return None

        if response.status != 200:
            return None

        match command:
            case "register" | "keepalive":
                me = load_peer(response)
            case "pquery":
                active_peers = load_peers(response)
                print(active_peers)

        return response

    def peer_to_peer(command: str, args: dict):
        response = None
        match command:
            case "rfcquery" | "getrfc":
                peer_app.connect(args["hostname"], args["port"])
            case _:
                return

        match command:
            case "rfcquery":
                response = rfc_query()
            case "getrfc":
                response = get_rfc()

        peer_app.disconnect()

        return response

    lock = threading.Lock()

    def make_request(command: str, args: dict = None):
        lock.acquire()

        response = peer_to_server(command, args) or peer_to_peer(command, args)

        lock.release()

        return response

    make_request("register")
    keep_alive_thread = threading.Timer(TTL_INTERVAL, make_request, ("keepalive",))
    keep_alive_thread.start()

    if commands is not None:
        for (command, args) in commands:
            make_request(command, args)

    keep_alive_thread.cancel()


def client(hostname: str, port: int, commands: list[tuple[str, dict]] = None):
    server_address = (hostname, PORT)

    app.connect(hostname, PORT)

    print(f"Connected to server: {server_address}")

    client_handler(
        port=port,
        commands=commands,
    )

    app.disconnect()


if __name__ == "__main__":
    hostname = socket.gethostname()
    port = 1235
    commands = [("pquery", {}), ("rfcquery", {"hostname": hostname, "port": port})]

    client(hostname, port, commands)
