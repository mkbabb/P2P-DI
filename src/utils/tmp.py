from http.client import HTTPResponse
from io import BytesIO

http_response_str = """HTTP/1.1 200 OK
Date: Thu, Jul  3 15:27:54 2014
Content-Type: text/xml; charset="utf-8"
Connection: close
Content-Length: 626

teststring"""

http_response_bytes = http_response_str.encode()

class FakeSocket():
    def __init__(self, response_bytes):
        self._file = BytesIO(response_bytes)
    def makefile(self, *args, **kwargs):
        return self._file

source = FakeSocket(http_response_bytes)
response = HTTPResponse(source)
response.begin()
print( "status:", response.status)
# status: 200
print( "single header:", response.getheader('Content-Type'))
# single header: text/xml; charset="utf-8"
print(response.headers)
print( "content:", response.read(len(http_response_str)))
# content: b'teststring'
