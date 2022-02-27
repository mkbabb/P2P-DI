import pathlib
import socket
import threading
from dataclasses import dataclass
from typing import *

from src.server.server import PORT, TTL_INTERVAL, Peer, load_peer
from src.utils.http import HTTPResponse, http_request


@dataclass
class RFC:
    number: int
    title: str
    hostname: Peer
    path: pathlib.Path


RFC_INDEX: set[RFC] = {}
