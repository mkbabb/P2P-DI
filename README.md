# P2P-DI

Implementation of a peer-to-peer distributed index (P2P-DI) system. This uses a host
registration server (RS), found in [`server.py`](src/server/server.py), wherein each
peer client, [`client.py`](src/peer/client.py), registers first with. Each peer also has
a server component, [`server.py`](src/peer/server.py), which is used to house a peer's
index information, and facilitate all P2P communication.

## Quick Start

No dependencies! Just Python **3.10**. Very important as we employ a judicious usage of
Python `3.10`'s new `match` statement (pattern matching, think a sophisticated switch
statement).

Nearly every file found herein is a Python _module_, thus it must be run like so:

    python3 -m $MODULE_NAME

To run the required tasks of the project, first initialize the registration server:

    python3 -m src.server.server

Finally, run the `peer` module (containing a special
[`__main__.py`](src/peer/__main__.py) file that allows it to be run directly):

    python3 -m src.peer

This will execute either of the tasks - just comment one, or none, out to change the
output.

To run the simple test case, execute `__main__.py` without any modifications - using the
above command.

## SocketIO

### Layer 1

Low-level socket communication is achieved by way of two layers of abstraction. First,
each and every message sent and received herein is wrapped by `send_message` and
`recv_message` (found within [`utils.py`](src/utils/utils.py)). These simple utility
functions encode the message into a pseudo-TLV format, wherein, the length (a 10-byte
long sequence) of the value component is appended onto the high-order section of the
message.

### Layer 2

The final layer includes a pseudo-HTTP protocol, wherein _nearly_ every message is
enwrapped. This protocol is almost identical to HTTP in every way, using the low-level
facilities found within the Python `http` module - mirrored by
[`http.py`](src/utils/http.py). This is used to achieve a standardized process whereby
pseudo-HTTP packets are created and parsed (header creation, content decoding, etc). A
typical packet is very much reminiscent of HTTP/1.1.

These HTTP packets come in two forms, `response` and `request` - again, mirroring the
standard HTTP/1.1 format. Each has a preamble section - containing an address-like
string, and headers - as well as an optional `body` section. Like with HTTP/1.1, if the
body contains any content, the header section **must** contain a `Content-Length`
attribute - this is automatically added when using the request/response utilities found
within [`http.py`](src/utils/http.py).

### `HTTPRequest`

```
getrfc fff-c.local HTTP/1.0
RFC-Number: 48
Host: fff-c.local
OS: Darwin 21.3.0
Date: Tue, 01 Mar 2022 00:26:06GMT
```

Above is the typification of the address line, plus the headers section. Notice the
header keys are case invariant, as is the method. By default, every HTTP object contains
the following header keys: `Host`, `OS`, `Date`.

> Example packet from `get_rfc`.

### `HTTPResponse`

```
11 200 OK
```

> Example OK response.

## Object List

Several objects are used to represent the project data.

### [`Peer`](src/peer/peer.py)

A `Peer` object represents a peer and has the following structure:

```python
class Peer:
    hostname: str
    cookie: int
    port: int

    last_active_time: float
    registration_count: int = 0
    active: bool = True
    ttl: int = TTL
```

### [`PeerIndex`](src/peer/peer.py)

A `PeerIndex` object is a simple wrapper containing a list of `Peer` objects, as well
has some utility functions for manipulating the peers therein.

### [`RFC`](src/peer/rfc.py)

A `RFC` object is an object reflecting several data attributes of an RFC:

```python
class RFC:
    number: int
    title: str
    hostname: Peer
    path: str
```

## Peer-To-Server

A peer client can communicate with the registration server by the following HTTP-like
methods:

### `Register`

Registers the peer with the RS, merging it into a `PeerIndex` data structure. If the
peer with that hostname and port address combination has already been registered, the
original peer is returned, re-activated.

#### Success Value:

```js
{
    status: 200,
    headers: default,
    body: json(peer)
}
```

### `Leave`

Contained within the request header is a `Peer-Cookie` field, containing the cookie
value for the chosen peer. If it's found in the PeerIndex, the peer is set to inactive.
If not, an error message is returned.

#### Success Value:

```js
{
    status: 200;
}
```

### `PQuery`

Contained within the request header is a `Peer-Cookie` field, containing the cookie
value for the chosen peer. If it's found in the PeerIndex, the peer is refreshed and a
list of active peers (not including the current peer) is returned within the body field
of the response. Else, and error is returned.

#### Success Value:

```js
{
    status: 200,
    headers: default,
    body: json(active_peers)
}
```

### `KeepAlive`

ontained within the request header is a `Peer-Cookie` field, containing the cookie value
for the chosen peer. If it's found in the PeerIndex, the peer is refreshed and returned
in the response body.

#### Success Value:

```js
{
    status: 200,
    headers: default,
    body: json(peer)
}
```

## Peer-To-Peer

A peer client can communicate with another peer's server by the following HTTP-like
methods.

### `RFCQuery`

Query the peer's RFC index (stored on the peer's server, remember). This is a simple
JSON dump of the RFC index into the response body. This index is then merged into the
caller's index.

#### Success Value:

```js
{
    status: 200,
    headers: default,
    body: json(rfc_index)
}
```

### `GetRFC`

This request takes and input rfc number, found within the request header's `RFC-Number`
field. If that RFC number is found within the peer's RFC index, the RFC object is dumped
and sent back to the caller, awaiting the message. Upon successful receipt of this RFC
object, the RFC file is located and sent to back to the caller via a success response -
this is done by placing the raw-bytes of the file object into the response's body
section.

This isn't optimal, as it stores an entire file in memory at a time. In the real world,
you'd likely chunk the file streaming into some quantum of chunks, and stream the result
to and from the caller.

Finally, the caller processes the raw bytes of the response's content section, and
creates a new file object with the same name. This new file is defined to be statically
located within the `./out/` directory.

#### Success Value 1:

```js
{
    status: 200,
    headers: default,
    body: json(rfc)
}
```

#### Success Value 1:

```js
{
    status: 200,
    headers: default,
    body: bytes(rfc_file)
}
```
