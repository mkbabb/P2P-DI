import datetime
from enum import Enum
import http
import http.client
import http.server
import platform
import socket
from functools import wraps
from io import BytesIO
import time
from typing import *

from src.utils.utils import recv_message, send_message

HTTP_VERSION = "HTTP/1.1"

SUCCESS_CODE = 200
FAIL_CODE = 403

TIME_FMT = "%a, %d %b %Y %H:%M:%S"


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
            self.content = self.read(len(response))

    def __str__(self) -> str:
        return f"""{self.version} {self.status} {self.reason}
{self.headers}"""


class HTTPRequest(http.server.BaseHTTPRequestHandler):
    def __init__(self, request: bytes):
        self.rfile = BytesIO(request)
        self.raw_requestline = self.rfile.readline()
        self.error_code = self.error_message = None
        self.parse_request()
        self.content = self.rfile.read()
        self.rfile.seek(0)

    def __str__(self) -> str:
        return f"""{self.command} {self.path} {self.protocol_version}
{self.headers}"""


def create_status_line(status_code: int = 200) -> bytes:
    code_phrase = http.HTTPStatus(status_code).phrase
    return f"{HTTP_VERSION} {status_code} {code_phrase}".encode()


def get_default_request_headers() -> dict[str, str]:
    return {
        "Host": socket.gethostname(),
        "OS": f"{platform.system()} {platform.release()}",
        "Date": time.strftime(TIME_FMT, time.gmtime()) + "GMT",
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
    method: str,
    url: str = "/",
    headers: Optional[dict[str, str]] = None,
    body: str = "",
) -> bytes:
    if headers is None:
        headers = {}

    headers |= get_default_request_headers()

    start_line = f"{method} {url} {HTTP_VERSION}".encode()
    return _make_response(start_line, headers, body)


def send_recv_http_request(
    request: bytes, server_socket: socket.socket
) -> HTTPResponse:
    send_message(request, server_socket)
    response = recv_message(server_socket)
    return HTTPResponse(response)


HTTPRequestReturn = tuple[str, str] | tuple[str, str, dict] | tuple[str, str, dict, str]

HTTPResponseReturn = tuple[int] | tuple[int, dict] | tuple[int, dict, str]


def http_request(func: Callable[..., HTTPRequestReturn]):
    @wraps(func)
    def wrapper(*args, **kwargs) -> HTTPRequest:
        method, url, *rest = func(*args, **kwargs)
        if isinstance(method, Enum):
            method = method.name

        headers: Optional[dict] = rest[0] if len(rest) > 0 else None
        body: str = rest[1] if len(rest) > 1 else ""

        request = make_request(method=method, url=url, headers=headers, body=body)

        r = HTTPRequest(bytes(request))
        print(r)

        return request

    return wrapper


def http_response(func: Callable[..., HTTPResponseReturn]):
    @wraps(func)
    def wrapper(*args, **kwargs) -> bytes:
        status_code, *rest = func(*args, **kwargs)
        headers: Optional[dict] = rest[0] if len(rest) > 0 else None
        body: str = rest[1] if len(rest) > 1 else ""

        response = make_response(status_code=status_code, headers=headers, body=body)

        r = HTTPResponse(bytes(response))
        print(r)

        return response

    return wrapper


@http_response
def FAIL_RESPONSE():
    return FAIL_CODE


@http_response
def SUCCESS_RESPONSE():
    return SUCCESS_CODE


if __name__ == "__main__":
    response = make_response(
        200,
        {
            "Date": datetime.datetime.now().isoformat(),
            "Content-Type": 'text/xml; charset="utf-8"',
            "Connection": "close",
        },
        "testing",
    )

    parsed = HTTPResponse(response)
    print(parsed)

    request = make_request("GET", body="hellow")
    parsed = HTTPRequest(request)
    print(parsed)
