import json
import time
from dataclasses import asdict, dataclass, field
from typing import *

from p2p_di.utils.http import HTTPRequest, HTTPResponse

TTL = 7200
TTL_INTERVAL = 5.0


@dataclass
class Peer:
    hostname: str
    cookie: int
    port: int

    last_active_time: float = field(default_factory=time.time)
    registration_count: int = 0
    active: bool = True
    ttl: int = TTL

    def refresh(self) -> None:
        self.active = True
        self.ttl = TTL

    def leave(self) -> None:
        self.active = False
        self.ttl = 0


class PeerIndex:
    def __init__(self) -> None:
        self.peers: dict[int, Peer] = {}
        self.id = 0

    def register(self, hostname: str, port: int) -> Peer:
        peer = None

        for p in self.peers.values():
            if p.hostname == hostname and p.port == port:
                peer = p
                peer.refresh()
                break
        else:
            peer = Peer(hostname=hostname, cookie=self.id, port=port)
            self.peers[self.id] = peer
            self.id += 1

        return peer

    def get(self, key: int, default: Any = None) -> Peer | Any:
        return self.peers.get(key, default)

    def get_active_peers(self) -> dict[int, Peer]:
        return {peer_id: peer for peer_id, peer in self.peers.items() if peer.active}

    def decrement_peer_ttls(self) -> None:
        for peer in self.get_active_peers().values():
            if peer.ttl == 0:
                peer.active = False
            else:
                peer.ttl -= 1


def load_peer(response: HTTPResponse | HTTPRequest) -> Peer:
    data = json.loads(response.content.decode())
    return Peer(**data)


def load_peers(response: HTTPResponse | HTTPRequest) -> list[Peer]:
    data = [json.loads(i) for i in json.loads(response.content)]
    return [Peer(**peer_data) for peer_data in data]


def dump_peer(peer: Peer) -> str:
    return json.dumps(asdict(peer))
