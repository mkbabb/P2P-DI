import threading

from src.peer.client import peer_client
from src.peer.server import peer_server




def main() -> None:
    hostname = input("Enter hostname: ")
    port = int(input("Enter port: "))

    address = (hostname, port)

    peer_client_thread = threading.Thread(target=peer_client, args=address)
    peer_client_thread.setDaemon(True)
    peer_client_thread.start()

    # connect_server_thread = threading.Thread(target=peer_server, args=address)
    # connect_server_thread.setDaemon(True)
    # connect_server_thread.start()

    # connect_server_thread.join()
    peer_client_thread.join()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
