import pathlib
import socket
import threading

from src.peer.client import client
from src.peer.rfc import RFC
from src.peer.server import server


def create_peer(
    hostname: str,
    port: int,
    commands: list[tuple[str, dict]] = None,
    rfc_index: set[RFC] = None,
) -> None:
    server_thread = threading.Thread(target=server, args=(hostname, port, rfc_index), daemon=True)
    server_thread.start()

    client_thread = threading.Thread(target=client, args=(hostname, port, commands))
    client_thread.start()


def task_1():
    hostname = socket.gethostname()
    start_port = 1234
    base_dir = pathlib.Path("data/")

    clients = 2
    rfc_count = 50

    rfc_index = set(
        [
            RFC(i, f"rfc{i}", hostname, base_dir.joinpath(f"rfc{i}.txt"))
            for i in range(rfc_count)
        ]
    )
    p0 = create_peer(hostname, start_port, None, rfc_index)

    commands = [
        # ("pquery", {}),
        # ("rfcquery", {"hostname": hostname, "port": start_port}),
    ]

    for i in range(1, clients):
        create_peer(hostname, start_port + i, commands, None)


if __name__ == "__main__":
    task_1()
