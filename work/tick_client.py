"""Small authenticated client for the local TICK 1.5.1 data service.

The credential is read at runtime from TICK's own local config and is never
printed or saved in this workspace.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


CONFIG = Path.home() / "AppData/Local/TICK/versions/1.5.1/ui/runtime-config.js"


class TickClient:
    def __init__(self) -> None:
        match = re.search(r"=\s*(\{.*\});", CONFIG.read_text(encoding="utf-8"))
        if match is None:
            raise RuntimeError("TICK runtime config format changed")
        config = json.loads(match.group(1))
        self.origin = config["dataServiceOrigin"].rstrip("/")
        self.key = config["dataServiceApiKey"]

    def request(self, method: str, path: str, body=None, *, raw: bool = False):
        url = f"{self.origin}/api/{path}"
        headers = {"X-Tick-Data-Service-Key": self.key}
        data = None
        if body is not None:
            if raw:
                data = body.encode("utf-8")
                headers["Content-Type"] = "text/plain; charset=utf-8"
            else:
                data = json.dumps(body, ensure_ascii=False).encode("utf-8")
                headers["Content-Type"] = "application/json"
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                content = response.read()
                return json.loads(content) if content else None
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:1000]
            raise RuntimeError(f"TICK {method} {path}: HTTP {exc.code}: {detail}") from exc

    def get(self, path: str):
        return self.request("GET", path)

    def post(self, path: str, body=None, *, raw: bool = False):
        return self.request("POST", path, body, raw=raw)

    def patch(self, path: str, body):
        return self.request("PATCH", path, body)


def encoded(value: str) -> str:
    return urllib.parse.quote(str(value), safe="")
