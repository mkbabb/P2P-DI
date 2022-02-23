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


class HTTPResponse(http.client.HTTPResponse):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.content = b""


class HTTPRequest(http.server.BaseHTTPRequestHandler):
    def __init__(self, request: bytes):
        self.rfile = BytesIO(request)
        self.raw_requestline = self.rfile.readline()
        self.error_code = self.error_message = None
        self.parse_request()
        self.content = self.rfile.read()
        self.rfile.seek(0)


def parse_response(response: bytes) -> HTTPResponse:
    class FakeSocket:
        def __init__(self, response_bytes):
            self._file = BytesIO(response_bytes)

        def makefile(self, *args, **kwargs):
            return self._file

    sock = FakeSocket(response)
    parsed: HTTPResponse = HTTPResponse(sock)
    parsed.begin()

    if (length := parsed.getheader("Content-Length")) is not None:
        parsed.content = parsed.read(int(length))

    return parsed


def parse_request(request: bytes) -> HTTPRequest:
    return HTTPRequest(request)


response = make_response(
    200,
    {
        "Date": datetime.datetime.now().isoformat(),
        "Content-Type": 'text/xml; charset="utf-8"',
        "Connection": "close",
    },
    "testing",
)

response = make_request(HTTPMethod.CONNECT, body="hellow")


parsed = parse_request(response)
print(parsed.headers)
print(parsed.content)
