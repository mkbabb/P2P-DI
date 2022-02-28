import pathlib
import pprint
import socket
from typing import *

from src.peer.peer import Peer, load_peer, load_peers
from src.peer.rfc import RFC, load_rfc, load_rfc_index
from src.peer.server import P2PCommands
from src.server.server import PORT, P2ServerCommands
from src.utils.http import (
    FAIL_RESPONSE,
    SUCCESS_CODE,
    SUCCESS_RESPONSE,
    http_request,
    send_recv_http_request,
)
from src.utils.utils import recv_message


@http_request
def register(hostname: str, port: int):
    return P2ServerCommands.register, hostname, {"port": port}


@http_request
def leave(hostname: str, peer: Peer):
    return P2ServerCommands.leave, hostname, {"Peer-Cookie": peer.cookie}


@http_request
def p_query(hostname: str, peer: Peer):
    return P2ServerCommands.pquery, hostname, {"Peer-Cookie": peer.cookie}


@http_request
def keep_alive(hostname: str, peer: Peer):
    return P2ServerCommands.keepalive, hostname, {"Peer-Cookie": peer.cookie}


@http_request
def rfc_query(hostname: str):
    return P2PCommands.rfcquery, hostname


def get_rfc(hostname: str, rfc_number: int, peer_socket: socket.socket):
    @http_request
    def _get_rfc():
        return P2PCommands.getrfc, hostname, {"RFC-Number": rfc_number}

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


Command = P2PCommands | P2ServerCommands


def client_handler(
    hostname: str,
    port: int,
    commands: list[tuple[Command, dict]],
    server_socket: socket.socket,
) -> None:
    rfc_index: set[RFC] = set()
    me: Peer = None

    def peer_to_server(command: P2ServerCommands, args: dict):
        nonlocal me

        request = None
        match command:
            case P2ServerCommands.register:
                request = register(hostname, port)
            case P2ServerCommands.leave:
                request = leave(hostname, me)
            case P2ServerCommands.pquery:
                request = p_query(hostname, me)
            case P2ServerCommands.keepalive:
                request = keep_alive(hostname, me)

        response = send_recv_http_request(request, server_socket)

        if response.status != 200:
            return None

        match command:
            case P2ServerCommands.register | P2ServerCommands.keepalive:
                me = load_peer(response)
                pprint.pprint(me)
            case P2ServerCommands.pquery:
                active_peers = load_peers(response)
                pprint.pprint(active_peers)

        return response

    def peer_to_peer(command: P2PCommands, args: dict):
        peer_hostname, peer_port = args["hostname"], args["port"]

        with socket.create_connection((peer_hostname, peer_port)) as peer_socket:
            request = None
            match command:
                case P2PCommands.rfcquery:
                    request = rfc_query(peer_hostname)
                case P2PCommands.getrfc:
                    request = get_rfc(peer_hostname, args["rfc_number"], peer_socket)

            response = send_recv_http_request(request, peer_socket)

            if response.status != 200:
                return None

            match command:
                case P2PCommands.rfcquery:
                    rfcs = load_rfc_index(response)
                    rfc_index.update(rfcs)
                    pprint.pprint(rfc_index)

            return response

    def make_request(command: P2ServerCommands | P2PCommands, args: dict = None):
        match command:
            case (
                P2ServerCommands.register
                | P2ServerCommands.leave
                | P2ServerCommands.pquery
                | P2ServerCommands.keepalive
            ):
                return peer_to_server(command, args)
            case P2PCommands.rfcquery | P2PCommands.getrfc:
                return peer_to_peer(command, args)

    make_request(P2ServerCommands.register)
    make_request(P2PCommands.rfcquery, {"hostname": hostname, "port": port})

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
