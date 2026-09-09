# -*- coding: utf-8 -*-
# 解析 PE .pdata (RUNTIME_FUNCTION) 把 RVA 归属到函数起始, 并反汇编函数头
# 用法: python pdata_funcs.py <exe> <rva>...
import struct, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

path = sys.argv[1]
rvas = []
for x in sys.argv[2:]:
    rvas.append(int(x, 16) if x.startswith("0x") else int(x))

f = open(path, "rb")
d = f.read(0x400)
pe = struct.unpack_from("<I", d, 0x3C)[0]
f.seek(pe); pehdr = f.read(0x18)
nsec = struct.unpack_from("<H", pehdr, 6)[0]
optsize = struct.unpack_from("<H", pehdr, 20)[0]
opt = f.read(optsize)
imgbase = struct.unpack_from("<Q", opt, 24)[0]
secs = []
for i in range(nsec):
    s = f.read(40)
    name = s[:8].rstrip(b"\x00").decode(errors="replace")
    vsize, vaddr, rsize, raddr = struct.unpack("<IIII", s[8:24])
    secs.append((name, vaddr, max(vsize, rsize), raddr))

def rva2off(rva):
    for nm, vaddr, size, raddr in secs:
        if vaddr <= rva < vaddr + size:
            return raddr + (rva - vaddr)
    return None

pdata = None
for nm, vaddr, size, raddr in secs:
    if nm == ".pdata":
        pdata = (vaddr, size, raddr)
pd_off = rva2off(pdata[0])
f.seek(pd_off)
blob = f.read(pdata[1])
funcs = []
for i in range(0, len(blob) - 12, 12):
    beg, end, unw = struct.unpack_from("<III", blob, i)
    if beg == 0:
        continue
    funcs.append((beg, end))
funcs.sort()
print("runtime functions: %d" % len(funcs))
import bisect
fbegins = [x[0] for x in funcs]

md = Cs(CS_ARCH_X86, CS_MODE_64)

# IAT map
ddoff = 112
imp_rva, imp_size = struct.unpack_from("<II", opt, ddoff + 8)
iat_map = {}
o = rva2off(imp_rva)
while True:
    f.seek(o)
    desc = f.read(20)
    if desc == b"\x00" * 20:
        break
    oft_rva, ts, fc, name_rva, ftn_rva = struct.unpack("<IIIII", desc)
    f.seek(rva2off(name_rva)); dllname = f.read(64).split(b"\x00")[0].decode()
    for trva in (ftn_rva, oft_rva):
        if not trva:
            continue
        idx = 0
        while True:
            f.seek(rva2off(trva + idx * 8))
            val = struct.unpack("<Q", f.read(8))[0]
            if val == 0:
                break
            if not (val & (1 << 63)):
                ho = rva2off(val)
                if ho:
                    f.seek(ho + 2)
                    fname = f.read(200).split(b"\x00")[0].decode(errors="replace")
                    iat_map[trva + idx * 8] = "%s!%s" % (dllname, fname)
            idx += 1
            if idx > 6000:
                break
    o += 20

import re
def disasm_fn(beg, size=0x70):
    off = rva2off(beg)
    if off is None:
        return []
    f.seek(off)
    code = f.read(size)
    out = []
    for ins in md.disasm(code, imgbase + beg):
        note = ""
        m = re.search(r"rip\s*([+-])\s*(0x[0-9a-f]+|\d+)", ins.op_str)
        if m:
            sign = 1 if m.group(1) == "+" else -1
            disp = sign * (int(m.group(2), 16) if m.group(2).startswith("0x") else int(m.group(2)))
            tgt = ins.address + ins.size + disp
            note = "  ; " + iat_map.get(tgt, "0x%x" % tgt)
        elif ins.mnemonic in ("call", "jmp") and ins.op_str.startswith("0x"):
            note = "  ; RVA 0x%x" % (int(ins.op_str, 16) - imgbase)
        out.append("  0x%06x %-8s %-38s%s" % (ins.address - imgbase, ins.mnemonic, ins.op_str, note))
        if ins.mnemonic in ("ret", "jmp") and ins.address - imgbase > beg + 0x10:
            break
    return out

for rva in rvas:
    i = bisect.bisect_right(fbegins, rva) - 1
    if i < 0:
        print("RVA 0x%x: not in pdata" % rva)
        continue
    beg, end = funcs[i]
    print("==== RVA 0x%x -> func [0x%x, 0x%x) size=0x%x" % (rva, beg, end, end - beg))
    for line in disasm_fn(beg):
        print(line)
    print()
