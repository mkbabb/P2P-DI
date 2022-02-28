import json
import pathlib
import socket
import threading
from dataclasses import dataclass, asdict
from typing import *

from src.server.server import PORT, TTL_INTERVAL, Peer, load_peer
from src.utils.http import HTTPResponse, http_request


@dataclass
class RFC:
    number: int
    title: str
    hostname: Peer
    path: pathlib.Path


RFC_INDEX: list[RFC] = []


def load_rfc_index(response: HTTPResponse):
    data = json.loads(response.content.decode())
    return [RFC(**i) for i in data]


def dump_rfc_index(rfc_index: list[RFC]):
    return json.dumps([asdict(i) for i in rfc_index], default=str)
