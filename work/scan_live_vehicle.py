"""Read-only Windows process scan for the active vehicle physics structure.

Known from the local Trackmania.exe decompile: input gas, brake, steer are
float32 at vehicle offsets 0x98, 0x9c, 0xa0. This script only uses
OpenProcess/VirtualQueryEx/ReadProcessMemory and never modifies the game.
"""

from __future__ import annotations

import argparse
import ctypes as C
import struct
import time
from ctypes import wintypes as W


PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400
MEM_COMMIT = 0x1000
MEM_PRIVATE = 0x20000
PAGE_GUARD = 0x100
PAGE_NOACCESS = 0x01


class MEMORY_BASIC_INFORMATION(C.Structure):
    _fields_ = [
        ("BaseAddress", C.c_void_p),
        ("AllocationBase", C.c_void_p),
        ("AllocationProtect", W.DWORD),
        ("PartitionId", W.WORD),
        ("RegionSize", C.c_size_t),
        ("State", W.DWORD),
        ("Protect", W.DWORD),
        ("Type", W.DWORD),
    ]


kernel = C.WinDLL("kernel32", use_last_error=True)
kernel.OpenProcess.argtypes = (W.DWORD, W.BOOL, W.DWORD)
kernel.OpenProcess.restype = W.HANDLE
kernel.VirtualQueryEx.argtypes = (W.HANDLE, C.c_void_p, C.POINTER(MEMORY_BASIC_INFORMATION), C.c_size_t)
kernel.VirtualQueryEx.restype = C.c_size_t
kernel.ReadProcessMemory.argtypes = (W.HANDLE, C.c_void_p, C.c_void_p, C.c_size_t, C.POINTER(C.c_size_t))
kernel.ReadProcessMemory.restype = W.BOOL
kernel.CloseHandle.argtypes = (W.HANDLE,)


def read(handle, address: int, length: int) -> bytes:
    buffer = C.create_string_buffer(length)
    got = C.c_size_t()
    if not kernel.ReadProcessMemory(handle, C.c_void_p(address), buffer, length, C.byref(got)):
        return b""
    return buffer.raw[:got.value]


def regions(handle):
    address = 0
    info = MEMORY_BASIC_INFORMATION()
    while address < 0x800000000000:
        size = kernel.VirtualQueryEx(handle, C.c_void_p(address), C.byref(info), C.sizeof(info))
        if not size:
            break
        base = info.BaseAddress or address
        end = base + info.RegionSize
        if info.State == MEM_COMMIT and info.Type == MEM_PRIVATE and not info.Protect & (PAGE_GUARD | PAGE_NOACCESS):
            yield base, info.RegionSize
        if end <= address:
            break
        address = end


def scan(handle, steer: float, gas: float, brake: float) -> list[int]:
    pattern = struct.pack("<fff", gas, brake, steer)
    start = time.monotonic()
    bytes_read = 0
    matches = []
    for base, length in regions(handle):
        # Keep reads small enough to avoid a single huge allocation.
        for offset in range(0, length, 16 * 1024 * 1024):
            chunk = read(handle, base + offset, min(16 * 1024 * 1024, length - offset))
            bytes_read += len(chunk)
            position = chunk.find(pattern)
            while position >= 0:
                vehicle = base + offset + position - 0x98
                header = read(handle, vehicle, 0x1b00)
                if len(header) == 0x1b00:
                    count = struct.unpack_from("<I", header, 0x380)[0]
                    contacts = [struct.unpack_from("<I", header, 0x17b4 + 0xb8 * i)[0]
                                for i in range(4)]
                    model = struct.unpack_from("<Q", header, 0x88)[0]
                    if count == 4 and all(value < 16 for value in contacts) and model > 0x100000000:
                        matches.append(vehicle)
                        print(f"candidate vehicle=0x{vehicle:x} model=0x{model:x} contacts={contacts}", flush=True)
                position = chunk.find(pattern, position + 1)
    print(f"read {bytes_read/1e9:.2f} GB in {time.monotonic()-start:.2f}s; {len(matches)} candidates", flush=True)
    return matches


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pid", type=int)
    parser.add_argument("steer", type=float)
    parser.add_argument("gas", type=float)
    parser.add_argument("brake", type=float)
    args = parser.parse_args()
    handle = kernel.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, args.pid)
    if not handle:
        raise OSError(C.get_last_error(), "OpenProcess failed")
    try:
        scan(handle, args.steer, args.gas, args.brake)
    finally:
        kernel.CloseHandle(handle)


if __name__ == "__main__":
    main()
