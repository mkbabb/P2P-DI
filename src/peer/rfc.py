import json
import pathlib
from dataclasses import asdict, dataclass
from typing import *

from src.peer.peer import Peer
from src.utils.http import HTTPRequest, HTTPResponse


@dataclass(frozen=True)
class RFC:
    number: int
    title: str
    hostname: Peer
    path: pathlib.Path


def load_rfc(response: HTTPResponse | HTTPRequest) -> RFC:
    data = json.loads(response.content.decode())
    return RFC(**data)


def dump_rfc(rfc: RFC) -> str:
    return json.dumps(asdict(rfc))


def load_rfc_index(response: HTTPResponse | HTTPRequest) -> set[RFC]:
    data = json.loads(response.content.decode())
    return set([RFC(**i) for i in data])


def dump_rfc_index(rfc_index: list[RFC]) -> str:
    return json.dumps([asdict(i) for i in rfc_index], default=str)
