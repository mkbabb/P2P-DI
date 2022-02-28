import pathlib
import socket
import threading
import time

from src.peer.client import client
from src.peer.rfc import RFC
from src.peer.server import P2PCommands, server
from src.server.server import P2ServerCommands


def create_peer(
    hostname: str,
    port: int,
    event: threading.Event(),
    commands: list[tuple[str, dict]] = None,
    rfc_index: set[RFC] = None,
) -> tuple[threading.Thread, ...]:
    server_thread = threading.Thread(
        target=server, args=(hostname, port, event, rfc_index), daemon=True
    )
    server_thread.start()

    client_thread = threading.Thread(
        target=client, args=(hostname, port, commands), daemon=True
    )
    client_thread.start()

    return server_thread, client_thread


def task_1():
    hostname = socket.gethostname()
    start_port = 1234
    base_dir = pathlib.Path("data/")

    threads: list[threading.Thread] = []
    event = threading.Event()

    clients = 2
    rfc_count = 50

    rfc_index = set(
        [
            RFC(i, f"rfc{i}", hostname, base_dir.joinpath(f"rfc{i}.txt"))
            for i in range(rfc_count)
        ]
    )
    p0 = create_peer(
        hostname=hostname,
        port=start_port,
        event=event,
        commands=None,
        rfc_index=rfc_index,
    )
    threads.append(p0[1])

    commands = [
        (P2ServerCommands.pquery, {}),
        (P2PCommands.rfcquery, {"hostname": hostname, "port": start_port}),
        (
            P2PCommands.getrfc,
            {"hostname": hostname, "port": start_port, "rfc_number": 1},
        ),
        (
            P2PCommands.getrfc,
            {"hostname": hostname, "port": start_port, "rfc_number": 2},
        ),
        (
            P2PCommands.getrfc,
            {"hostname": hostname, "port": start_port, "rfc_number": 3},
        ),
    ]

    for i in range(1, clients):
        p_i = create_peer(
            hostname=hostname,
            port=start_port + i,
            event=event,
            commands=commands,
            rfc_index=None,
        )
        threads.append(p_i[1])

    # for t in threads:
    #     t.join()


if __name__ == "__main__":
    task_1()
