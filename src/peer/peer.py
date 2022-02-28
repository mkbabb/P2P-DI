import threading

from src.peer.client import client
from src.peer.server import server


def main() -> None:
    hostname = input("Enter hostname: ")
    port = int(input("Enter port: "))

    address = (hostname, port)

    client_thread = threading.Thread(target=client, args=address)
    client_thread.setDaemon(True)
    client_thread.start()

    server_thread = threading.Thread(target=server, args=address)
    server_thread.setDaemon(True)
    server_thread.start()

    server_thread.join()
    client_thread.join()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
