import pathlib
import socket
from typing import *

from src.peer.peer import Peer, load_peer, load_peers
from src.peer.rfc import RFC, load_rfc, load_rfc_index
from src.server.server import PORT
from src.utils.http import (
    FAIL_RESPONSE,
    SUCCESS_CODE,
    SUCCESS_RESPONSE,
    BottleApp,
    http_request,
    send_recv_http_request,
)
from src.utils.utils import recv_message

import pprint


@http_request
def register(port: int):
    return "Register", {"port": port}


@http_request
def leave(peer: Peer):
    return "Leave", {"Peer-Cookie": peer.cookie}


@http_request
def p_query(peer: Peer):
    return "PQuery", {"Peer-Cookie": peer.cookie}


@http_request
def keep_alive(peer: Peer):
    return "KeepAlive", {"Peer-Cookie": peer.cookie}


@http_request
def rfc_query():
    return "RFCQuery", {}


def get_rfc(rfc_number: int, peer_socket: socket.socket):
    @http_request
    def _get_rfc():
        return "GetRFC", {"RFC-Number": rfc_number}

    request = _get_rfc(rfc_number)
    response = send_recv_http_request(request, peer_socket)

    if response.status == SUCCESS_CODE:
        print("Downloading file...")

        rfc: RFC = load_rfc(response)
        filepath = rfc.path

        out_filepath = pathlib.Path(filepath.name)

        with out_filepath.open("w") as file:
            while d := recv_message(peer_socket):
                file.write(d.decode())

        return SUCCESS_RESPONSE()
    else:
        return FAIL_RESPONSE()


def client_handler(
    hostname: str,
    port: int,
    commands: list[tuple[str, list]],
    server_socket: socket.socket,
) -> None:
    rfc_index: set[RFC] = set()

    def peer_to_server(command: str, args: dict):
        global me

        request = None
        match command:
            case "register":
                request = register(port)
            case "leave":
                request = leave(me)
            case "pquery":
                request = p_query(me)
            case "keepalive":
                request = keep_alive(me)

        response = send_recv_http_request(request, server_socket)

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
        address = (args["hostname"], args["port"])

        with socket.create_connection(address) as peer_socket:
            request = None
            match command:
                case "rfcquery":
                    request = rfc_query()
                case "getrfc":
                    request = get_rfc(args["rfc_number"], peer_socket)

            response = send_recv_http_request(request, peer_socket)

            if response.status != 200:
                return None

            match command:
                case "rfcquery":
                    rfcs = load_rfc_index(response)
                    rfc_index.update(rfcs)
                    pprint.pprint(rfc_index)

            return response

    def make_request(command: str, args: dict = None):
        match (command := command.lower()):
            case "register" | "leave" | "pquery" | "keepalive":
                return peer_to_server(command, args)
            case "rfcquery" | "getrfc":
                return peer_to_peer(command, args)

    make_request("register")
    make_request("rfcquery", {"hostname": hostname, "port": port})

    if commands is not None:
        for (command, args) in commands:
            make_request(command, args)


def client(hostname: str, port: int, commands: list[tuple[str, dict]] = None):
    server_address = (hostname, PORT)

    with socket.create_connection(server_address) as server_socket:
        print(f"Connected to server: {server_address}")

        client_handler(
            hostname=hostname, port=port, commands=commands, server_socket=server_socket
        )
