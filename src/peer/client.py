import pathlib
from typing import *

from src.peer.peer import Peer, load_peer, load_peers
from src.peer.rfc import RFC, load_rfc, load_rfc_index
from src.server.server import PORT
from src.utils.http import FAIL_RESPONSE, SUCCESS_CODE, SUCCESS_RESPONSE, BottleApp
from src.utils.utils import recv_message

import pprint

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
def rfc_query():
    return "RFCQuery", {}


def get_rfc(rfc_number: int):
    @peer_app.request()
    def _get_rfc():
        return "GetRFC", {"RFC-Number": rfc_number}

    response = _get_rfc(rfc_number)

    if response.status == SUCCESS_CODE:
        print("Downloading file...")

        rfc: RFC = load_rfc(response)
        filepath = rfc.path

        out_filepath = pathlib.Path(filepath.name)

        with out_filepath.open("w") as file:
            while d := recv_message(peer_app.socket):
                file.write(d.decode())

        return SUCCESS_RESPONSE()
    else:
        return FAIL_RESPONSE()


def client_handler(hostname: str, port: int, commands: list[tuple[str, list]]) -> None:
    rfc_index: set[RFC] = set()

    def peer_to_server(command: str, args: dict):
        global me

        response = None
        match command:
            case "register":
                response = register(port)
            case "leave":
                response = leave(me)
            case "pquery":
                response = p_query(me)
            case "keepalive":
                response = keep_alive(me)
            case _:
                return None

        if response.status != 200:
            return None

        match command:
            case "register" | "keepalive":
                me = load_peer(response)
                pprint.pprint(me)
            case "pquery":
                active_peers = load_peers(response)
                pprint.pprint(active_peers)

        return response

    def peer_to_peer(command: str, args: dict):
        response = None
        match command:
            case "rfcquery" | "getrfc":
                peer_app.connect(args["hostname"], args["port"])
            case _:
                return None

        match command:
            case "rfcquery":
                response = rfc_query()
            case "getrfc":
                response = get_rfc(args["rfc_number"])

        if response.status != 200:
            return None

        match command:
            case "rfcquery":
                rfcs = load_rfc_index(response)
                rfc_index.update(rfcs)

                pprint.pprint(rfc_index)
                print()

        peer_app.disconnect()

        return response

    def make_request(command: str, args: dict = None):
        command = command.lower()
        response = peer_to_server(command, args) or peer_to_peer(command, args)
        return response

    make_request("register")
    # make_request("rfcquery", {"hostname": hostname, "port": port})

    if commands is not None:
        for (command, args) in commands:
            make_request(command, args)


def client(hostname: str, port: int, commands: list[tuple[str, dict]] = None):
    server_address = (hostname, PORT)

    app.connect(hostname, PORT)

    print(f"Connected to server: {server_address}")

    client_handler(
        hostname=hostname,
        port=port,
        commands=commands,
    )

    app.disconnect()
