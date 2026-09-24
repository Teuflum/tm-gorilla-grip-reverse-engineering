"""Fast linear x64 disassembly to find direct references to 0.1f constants."""

import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).with_name("vendor")))
import capstone
import pefile
from capstone.x86_const import X86_OP_MEM, X86_REG_RIP


path = Path(__file__).with_name("Trackmania.exe")
pe = pefile.PE(str(path))
data = path.read_bytes()
base = pe.OPTIONAL_HEADER.ImageBase
constants = set()
for section in pe.sections:
    if section.Name.rstrip(b"\0") != b".rdata":
        continue
    blob = section.get_data()
    pattern = struct.pack("<f", 0.1)
    start = 0
    while True:
        index = blob.find(pattern, start)
        if index < 0:
            break
        constants.add(base + section.VirtualAddress + index)
        start = index + 1

text = next(section for section in pe.sections if section.Name.rstrip(b"\0") == b".text")
start_va = base + text.VirtualAddress
disasm = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
disasm.detail = True
disasm.skipdata = True
rows = []
for insn in disasm.disasm(text.get_data(), start_va):
    if insn.id == 0:
        continue
    for operand in insn.operands:
        if operand.type == X86_OP_MEM and operand.mem.base == X86_REG_RIP:
            target = insn.address + insn.size + operand.mem.disp
            if target in constants:
                rows.append((insn.address, target, insn.mnemonic, insn.op_str))

output = Path(__file__).with_name("float_0p1_code_refs.txt")
output.write_text(
    "\n".join(f"{addr:016x} -> {target:016x}  {mnemonic} {operands}" for addr, target, mnemonic, operands in rows),
    encoding="utf-8",
)
print(len(constants), "0.1f constants;", len(rows), "direct code refs; output", output)
for row in rows:
    print("%016x -> %016x  %s %s" % row)
