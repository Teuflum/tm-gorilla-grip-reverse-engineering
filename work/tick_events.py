"""Minimal read-only client for TICK's local live telemetry WebSocket."""

from __future__ import annotations

import base64
import json
import os
import socket
import struct
import urllib.parse

from tick_client import TickClient


class TickEvents:
    def __init__(self, client: TickClient, after_sequence: int = 9007199254740991):
        parsed = urllib.parse.urlparse(client.origin)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or 80
        self.socket = socket.create_connection((host, port), timeout=10)
        self.socket.settimeout(30)
        path = f"/events?afterSequence={after_sequence}&accessToken=" + urllib.parse.quote(client.key, safe="")
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        request = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            "Upgrade: websocket\r\nConnection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
        )
        self.socket.sendall(request.encode("ascii"))
        header = bytearray()
        while b"\r\n\r\n" not in header:
            part = self.socket.recv(1024)
            if not part:
                raise ConnectionError("TICK closed WebSocket handshake")
            header.extend(part)
        prefix, pending = header.split(b"\r\n\r\n", 1)
        if not prefix.startswith(b"HTTP/1.1 101"):
            raise ConnectionError(prefix.split(b"\r\n", 1)[0].decode("ascii", "replace"))
        self.pending = bytearray(pending)

    def close(self):
        self.socket.close()

    def read_exactly(self, count: int) -> bytes:
        while len(self.pending) < count:
            part = self.socket.recv(max(4096, count - len(self.pending)))
            if not part:
                raise ConnectionError("TICK closed telemetry stream")
            self.pending.extend(part)
        data = bytes(self.pending[:count])
        del self.pending[:count]
        return data

    def read_event(self):
        while True:
            first, second = self.read_exactly(2)
            opcode = first & 0x0F
            length = second & 0x7F
            if length == 126:
                length = struct.unpack("!H", self.read_exactly(2))[0]
            elif length == 127:
                length = struct.unpack("!Q", self.read_exactly(8))[0]
            if second & 0x80:
                mask = self.read_exactly(4)
                body = self.read_exactly(length)
                body = bytes(value ^ mask[i % 4] for i, value in enumerate(body))
            else:
                body = self.read_exactly(length)
            if opcode == 8:
                raise ConnectionError("TICK closed telemetry stream")
            if opcode == 1:
                return json.loads(body)


if __name__ == "__main__":
    client = TickClient()
    stream = TickEvents(client)
    try:
        for _ in range(20):
            event = stream.read_event()
            runtime = event.get("runtimeEvent") or {}
            if runtime.get("eventType") == "vehicle-state":
                state = runtime["payload"]
                print({key: state.get(key) for key in ("raceTick", "speedMetersPerSecond", "inputs")})
            else:
                print("event", event.get("type"), runtime.get("eventType"))
    finally:
        stream.close()
