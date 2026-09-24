"""Read the small physics-model curves involved in grip-mode activation."""

import argparse
import ctypes as C
import struct

from scan_live_vehicle import PROCESS_QUERY_INFORMATION, PROCESS_VM_READ, kernel, read


parser = argparse.ArgumentParser()
parser.add_argument("pid", type=int)
parser.add_argument("vehicle", type=lambda value: int(value, 0))
args = parser.parse_args()

handle = kernel.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, args.pid)
if not handle:
    raise OSError(C.get_last_error(), "OpenProcess failed")
try:
    vehicle = read(handle, args.vehicle, 0x1D00)
    model_address = struct.unpack_from("<Q", vehicle, 0x88)[0]
    model = read(handle, model_address, 0x2200)
    print("vehicle", hex(args.vehicle), "model", hex(model_address))
    print("model ice coefficient", struct.unpack_from("<f", model, 0xCD4)[0])
    print("neutral timeout", struct.unpack_from("<I", model, 0x1198)[0])
    print("force delay", struct.unpack_from("<I", model, 0x1194)[0])
    for offset in (0xCF0, 0xD40, 0xFA0):
        flags, pointer, count = struct.unpack_from("<I4xQI", model, offset)
        print("curve", hex(offset), "flags", hex(flags), "count", count)
        if count > 100 or count == 0:
            continue
        points = read(handle, pointer, count * 8)
        print("points", [struct.unpack_from("<ff", points, i * 8)
                         for i in range(count)])
finally:
    kernel.CloseHandle(handle)
