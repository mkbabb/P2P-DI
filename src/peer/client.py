import pathlib
import pprint
import socket
import sys
import threading
from typing import *
import time

from src.peer.peer import Peer, load_peer, load_peers
from src.peer.rfc import RFC, load_rfc, load_rfc_index
from src.peer.server import P2PCommands
from src.server.server import PORT, TIMEOUT, P2ServerCommands
from src.utils.http import (
    FAIL_RESPONSE,
    SUCCESS_CODE,
    SUCCESS_RESPONSE,
    HTTPResponse,
    http_request,
    make_request,
    send_recv_http_request,
)
from src.utils.utils import recv_message, send_message, timethat


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

@timethat
def get_rfc(hostname: str, rfc_number: int, peer_socket: socket.socket):
    @http_request
    def _get_rfc():
        return P2PCommands.getrfc, hostname, {"RFC-Number": rfc_number}

    request = _get_rfc()
    response = send_recv_http_request(request, peer_socket)

    if response.status == SUCCESS_CODE:

        rfc: RFC = load_rfc(response)
        filepath = pathlib.Path(rfc.path)
        out_filepath = pathlib.Path("out/").joinpath(pathlib.Path(filepath.name))

        response = HTTPResponse(recv_message(peer_socket))

        with out_filepath.open("wb") as file:
            file.write(response.content)

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
                # pprint.pprint(me)
            case P2ServerCommands.pquery:
                active_peers = load_peers(response)
                # pprint.pprint(active_peers)

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
                    return

            response = send_recv_http_request(request, peer_socket)

            if response.status != 200:
                return None

            match command:
                case P2PCommands.rfcquery:
                    rfcs = load_rfc_index(response)
                    rfc_index.update(rfcs)
                    # pprint.pprint(rfc_index)
            return response

    def execute_command(command: P2ServerCommands | P2PCommands, args: dict = None):
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

    execute_command(P2ServerCommands.register)
    execute_command(P2PCommands.rfcquery, {"hostname": hostname, "port": port})

    keep_alive_thread = threading.Timer(
        TIMEOUT, execute_command, (P2ServerCommands.keepalive,)
    )
    keep_alive_thread.start()

    if commands is not None:
        for (command, args) in commands:
            print(command, args)
            execute_command(command, args)

    keep_alive_thread.cancel()


def client(hostname: str, port: int, commands: list[tuple[str, dict]] = None):
    server_address = (hostname, PORT)

    try:
        with socket.create_connection(server_address) as server_socket:
            server_socket.settimeout(TIMEOUT)

            print(f"Connected to server: {server_address}")

            client_handler(
                hostname=hostname,
                port=port,
                commands=commands,
                server_socket=server_socket,
            )
    except Exception as e:
        print("Client: ", e, file=sys.stderr)
