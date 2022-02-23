import datetime
import http
import http.client
import http.server
import platform
import socket
from enum import Enum, auto
from io import BytesIO
from typing import *

HTTP_VERSION = "HTTP/1.1"


class HTTPMethod(Enum):
    GET = auto()
    HEAD = auto()
    POST = auto()
    PUT = auto()
    DELETE = auto()
    CONNECT = auto()
    OPTIONS = auto()
    TRACE = auto()
    PATCH = auto()


def create_status_line(status_code: int = 200) -> bytes:
    code_phrase = http.HTTPStatus(status_code).phrase
    return f"{HTTP_VERSION} {status_code} {code_phrase}".encode()


def get_default_request_headers() -> dict[str, str]:
    return {
        "Host": socket.gethostname(),
        "OS": f"{platform.system()} {platform.release()}",
    }


def format_headers(headers: dict[str, str]) -> bytes:
    return b"\r\n".join(f"{k}: {v}".encode() for k, v in headers.items())


def _make_response(
    start_line: bytes, headers: Optional[dict[str, str]] = None, body: str = ""
) -> bytes:
    if headers is None:
        headers = {}

    if len(body) > 0:
        headers["Content-Length"] = str(len(body))
        body = "\r\n" + body

    content = [
        start_line,
        format_headers(headers),
        body.encode(),
    ]

    response = b"\r\n".join(content)

    return response


def make_response(
    status_code: int = 200,
    headers: Optional[dict[str, str]] = None,
    body: str = "",
) -> bytes:
    start_line = create_status_line(status_code)
    return _make_response(start_line, headers, body)


def make_request(
    method: HTTPMethod,
    url: str = "/",
    headers: Optional[dict[str, str]] = None,
    body: str = "",
):
    if headers is None:
        headers = {}

    headers |= get_default_request_headers()

    start_line = f"{method.name} {url} {HTTP_VERSION}".encode()
    return _make_response(start_line, headers, body)


class _FakeSocket(socket.socket):
    def __init__(self, response: bytes):
        self._file = BytesIO(response)

    def makefile(self, *args, **kwargs):
        return self._file


class HTTPResponse(http.client.HTTPResponse):
    def __init__(self, response: bytes):
        super().__init__(_FakeSocket(response))
        self.content = b""

        self.begin()

        if (length := self.getheader("Content-Length")) is not None:
            self.content = self.read(int(length))


class HTTPRequest(http.server.BaseHTTPRequestHandler):
    def __init__(self, request: bytes):
        self.rfile = BytesIO(request)
        self.raw_requestline = self.rfile.readline()
        self.error_code = self.error_message = None
        self.parse_request()
        self.content = self.rfile.read()
        self.rfile.seek(0)


response = make_response(
    200,
    {
        "Date": datetime.datetime.now().isoformat(),
        "Content-Type": 'text/xml; charset="utf-8"',
        "Connection": "close",
    },
    "testing",
)

request = make_request(HTTPMethod.CONNECT, body="hellow")


parsed = HTTPResponse(response)
print(parsed.headers)
print(parsed.content)
