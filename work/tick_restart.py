"""Restart the current Trackmania race so TICK plays the loaded input again.

Brings the game window forward and presses Delete (give up). On the finish
screen it then presses Enter for "Improve". TICK's live telemetry confirms the
restart. The GorillaGripLogger restart command did not start TICK playback in
testing, which is why this sends keys instead.

Usage: py -3 tick_restart.py --pid <Trackmania PID>
"""

from __future__ import annotations

import argparse
import ctypes as C
import math
import threading
import time
from ctypes import wintypes as W

from tick_client import TickClient
from tick_events import TickEvents


user32 = C.WinDLL("user32", use_last_error=True)


class Live:
    """Latest TICK vehicle-state event, updated from a background thread."""

    def __init__(self, client: TickClient) -> None:
        self.tick = -1
        self.sim = -1
        self.position = (math.nan, math.nan, math.nan)
        self.restarted = False
        self.error = None
        self.stream = TickEvents(client)
        self.stop = threading.Event()
        threading.Thread(target=self.listen, daemon=True).start()

    def listen(self) -> None:
        try:
            while not self.stop.is_set():
                event = self.stream.read_event().get("runtimeEvent") or {}
                if event.get("eventType") != "vehicle-state":
                    continue
                payload = event["payload"]
                tick = payload.get("raceTick")
                if tick is None:
                    continue
                if 0 <= tick < 200:
                    self.restarted = True
                p = payload.get("position") or {}
                self.position = (p.get("x", math.nan), p.get("y", math.nan), p.get("z", math.nan))
                self.sim = payload.get("simulationTick", -1)
                self.tick = tick
        except Exception as exc:
            self.error = repr(exc)

    def wait(self, predicate, seconds: float, what: str) -> None:
        deadline = time.monotonic() + seconds
        while not predicate():
            if self.error:
                raise RuntimeError(self.error)
            if time.monotonic() > deadline:
                raise TimeoutError(f"Timed out waiting for {what} (race {self.tick} ms)")
            time.sleep(0.001)

    def close(self) -> None:
        self.stop.set()
        self.stream.close()


class KEYBDINPUT(C.Structure):
    _fields_ = [("wVk", W.WORD), ("wScan", W.WORD), ("dwFlags", W.DWORD),
                ("time", W.DWORD), ("dwExtraInfo", C.c_size_t)]


class INPUT(C.Structure):
    _fields_ = [("type", W.DWORD), ("ki", KEYBDINPUT), ("pad", C.c_ubyte * 8)]


def tap(scan: int, flags: int = 0) -> None:
    for extra in (0, 0x0002):  # key down, key up
        event = INPUT(type=1, ki=KEYBDINPUT(0, scan, 0x0008 | flags | extra, 0, 0))
        user32.SendInput(1, C.byref(event), C.sizeof(INPUT))
        time.sleep(0.08)


def restart(pid: int, client: TickClient, live: Live) -> None:
    """Bring the game forward and restart: Delete in a run; Delete, Enter ("Improve") when finished."""
    found = []

    @C.WINFUNCTYPE(W.BOOL, W.HWND, W.LPARAM)
    def visit(hwnd, _):
        owner = W.DWORD()
        user32.GetWindowThreadProcessId(hwnd, C.byref(owner))
        if owner.value == pid and user32.IsWindowVisible(hwnd) and user32.GetWindowTextLengthW(hwnd):
            found.append(hwnd)
        return True

    user32.EnumWindows(visit, 0)
    if not found:
        raise RuntimeError("Game window not found")
    # Windows only lets a process take focus right after keyboard input; tap Alt first.
    tap(0x38)
    user32.ShowWindow(found[0], 9)  # SW_RESTORE
    user32.SetForegroundWindow(found[0])
    time.sleep(0.4)
    owner = W.DWORD()
    user32.GetWindowThreadProcessId(user32.GetForegroundWindow(), C.byref(owner))
    if owner.value != pid:
        raise RuntimeError("Could not bring the game window to the foreground")
    # TICK reports no map on the finish screen.
    finished = client.get("runtime/status")["currentMapUid"] is None
    live.restarted = False
    tap(0x53, 0x0001)  # Delete (extended): give up
    if finished:
        time.sleep(1.0)
        tap(0x1C)  # Enter: "Improve" on the finish screen
    live.wait(lambda: live.restarted, 30, "race restart")
    print(f"race restarted (at {live.tick} ms)", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pid", type=int, required=True)
    args = parser.parse_args()
    client = TickClient()
    live = Live(client)
    try:
        restart(args.pid, client, live)
    finally:
        live.close()


if __name__ == "__main__":
    main()
