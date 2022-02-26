import datetime
import socket
import sys
import threading
from dataclasses import dataclass, field
from typing import *

from src.server.server import PORT
from src.utils.http import HTTPRequest, HTTPResponse, make_request
from src.utils.utils import recv_message, send_message


def register(hostname: str, port: int, server_socket: socket.socket):
    headers = {"port": port}

    request = make_request(method="Register", url=hostname, headers=headers)

    send_message(request, server_socket)


def peer_client(hostname: str, port: int) -> None:
    def handle()

    server_address = (hostname, PORT)

    with socket.create_connection(server_address) as server_socket:
        print(f"Connected to server: {server_address}")
        register(hostname, port, server_socket)
        print("Registered with the RS")


peer_client(socket.gethostname(), 1234)
