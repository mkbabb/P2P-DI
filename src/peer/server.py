import datetime
import socket
import sys
import threading
from dataclasses import dataclass
from typing import *

from src.utils.http import HTTPRequest, HTTPResponse
from src.utils.utils import recv_message, send_message


def server_receiver(peer_socket: socket.socket) -> None:
    def handle(http_request: HTTPRequest) -> str:

        match request_type:
            case "GET":
                return None

    try:
        while request := recv_message(peer_socket):
            http_request = HTTPRequest(request)

            arr = request.split(" ")
            request_type = arr[0]

            message = handle(request, request_type)
            send_message(message.encode(), peer_socket)
    except KeyboardInterrupt:
        pass

    peer_socket.close()
    sys.exit(0)


def server() -> None:
    address = (sock.gethostname(), PORT)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(10)
        sock.connect(address)

        try:
            while True:
                conn, _ = sock.accept()
                t = threading.Thread(target=server_receiver, args=(conn,))
                t.start()
        except KeyboardInterrupt:
            pass
