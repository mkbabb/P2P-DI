import pathlib
import random
import socket
import threading
import time

from p2p_di.peer.client import client
from p2p_di.peer.rfc import RFC
from p2p_di.peer.server import P2PCommands, server
from p2p_di.registration_server.server import P2ServerCommands
from p2p_di.utils.utils import timethat

RFC_TOTAL = 500
HOSTNAME = socket.gethostname()
START_PORT = 1234
BASE_DIR = pathlib.Path("rfcs/")


def create_peer(
    hostname: str,
    port: int,
    commands: list[tuple[str, dict]] = None,
    rfc_index: set[RFC] = None,
) -> tuple[threading.Thread, ...]:
    server_thread = threading.Thread(
        target=server, args=(hostname, port, rfc_index), daemon=True
    )
    client_thread = threading.Thread(target=client, args=(hostname, port, commands))

    return server_thread, client_thread


def make_get_rfc(hostname: str, port: int, rfc_number: int):
    return (
        P2PCommands.getrfc,
        {"hostname": hostname, "port": port, "rfc_number": rfc_number},
    )


def make_rfc_index(
    hostname: str, base_dir: pathlib.Path, count: int, randomize: bool = True
):
    numbers = (
        list(range(1, count + 1))
        if not randomize
        else random.sample(range(1, RFC_TOTAL + 1), count)
    )

    return set(
        [RFC(i, f"rfc{i}", hostname, base_dir.joinpath(f"rfc{i}.txt")) for i in numbers]
    )


def task_1():
    threads: list[threading.Thread] = []

    clients = 20
    rfc_count = 60

    rfc_index = make_rfc_index(HOSTNAME, BASE_DIR, rfc_count, False)

    p0 = create_peer(
        hostname=HOSTNAME,
        port=START_PORT,
        commands=None,
        rfc_index=rfc_index,
    )
    threads.append(p0)

    commands = [
        (P2ServerCommands.pquery, {}),
        (P2PCommands.rfcquery, {"hostname": HOSTNAME, "port": START_PORT}),
    ]

    commands.extend(
        (make_get_rfc(HOSTNAME, START_PORT, i) for i in range(1, rfc_count - 10 + 1))
    )

    for i in range(1, clients):
        p_i = create_peer(
            hostname=HOSTNAME,
            port=START_PORT + i,
            commands=commands,
            rfc_index=None,
        )
        threads.append(p_i)

    for server_thread, client_thread in threads:
        server_thread.start()
        client_thread.start()


def task_2():
    threads: list[threading.Thread] = []

    clients = 20
    rfc_count = 10

    rfc_indexes = {
        i: make_rfc_index(HOSTNAME, BASE_DIR, rfc_count) for i in range(clients)
    }

    commands = [
        (P2ServerCommands.pquery, {}),
        (P2PCommands.rfcquery, {"hostname": HOSTNAME, "port": START_PORT}),
    ]

    for i in range(clients):
        rfc_index_i = rfc_indexes[i]

        get_commands = []
        for key, value in rfc_indexes.items():
            if key != i:
                get_commands.extend(
                    [
                        make_get_rfc(HOSTNAME, START_PORT + key, rfc.number)
                        for rfc in value
                    ]
                )

        p_i = create_peer(
            hostname=HOSTNAME,
            port=START_PORT + i,
            commands=[*commands, *get_commands],
            rfc_index=rfc_index_i,
        )
        server_thread, _ = p_i
        server_thread.start()

        threads.append(p_i)

    for server_thread, client_thread in threads:
        client_thread.start()


def simple_test():
    rfc_count = 2

    rfc_index = make_rfc_index(HOSTNAME, BASE_DIR, rfc_count, False)

    A_port = START_PORT
    B_port = START_PORT + 1

    A_commands = [
        (P2ServerCommands.pquery, {}),
        make_get_rfc(HOSTNAME, B_port, 1),
        (P2ServerCommands.pquery, {}),
    ]

    B_commands = [(P2ServerCommands.leave, {})]

    A = create_peer(
        hostname=HOSTNAME,
        port=A_port,
        commands=A_commands,
        rfc_index=None,
    )
    A[0].start()

    B = create_peer(
        hostname=HOSTNAME,
        port=B_port,
        commands=B_commands,
        rfc_index=rfc_index,
    )
    B[0].start()

    A[1].start()
    B[1].start()


if __name__ == "__main__":
    simple_test()
    # task_1()
    # task_2()
