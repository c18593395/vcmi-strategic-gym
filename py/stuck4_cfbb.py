# -*- coding: utf-8 -*-
# 符号化 VCMI_lib+0xcfbb00: .pdata 函数边界 + 开头反汇编
import struct, bisect
LIB = r"D:\vcmi-fork-build\bin\VCMI_lib.dll"
pe = open(LIB, "rb")
dd = pe.read(0x400)
p = struct.unpack_from("<I", dd, 0x3C)[0]
pe.seek(p); pehdr = pe.read(0x18)
nsec = struct.unpack_from("<H", pehdr, 6)[0]
optsize = struct.unpack_from("<H", pehdr, 20)[0]
pe.read(optsize)
secs = []
for i in range(nsec):
    s = pe.read(40)
    nm = s[:8].rstrip(b"\x00").decode(errors="replace")
    vsize, vaddr, rsize, raddr = struct.unpack("<IIII", s[8:24])
    secs.append((nm, vaddr, max(vsize, rsize), raddr))

def rva2off(rva):
    for nm, vaddr, size, raddr in secs:
        if vaddr <= rva < vaddr + size:
            return raddr + (rva - vaddr)
    return None

pdata_off = None
for nm, vaddr, size, raddr in secs:
    if nm == ".pdata":
        pdata_off, pdata_size = raddr, size
print("sections:", [(n, hex(v), hex(s)) for n, v, s, _ in secs][:8])
if pdata_off is None:
    print("NO .pdata (MinGW DLL may lack it)"); raise SystemExit
pe.seek(pdata_off); blob = pe.read(pdata_size)
funcs = []
for i in range(0, len(blob) - 12, 12):
    b, e, u = struct.unpack_from("<III", blob, i)
    if b:
        funcs.append((b, e))
funcs.sort()
print("pdata funcs:", len(funcs))
fb = [x[0] for x in funcs]
i = bisect.bisect_right(fb, 0xcfbb00) - 1
if i >= 0:
    b, e = funcs[i]
    print("VCMI_lib+0xcfbb00 in fn[0x%x - 0x%x) size=%d" % (b, e, e - b))
    off = rva2off(b)
    pe.seek(off)
    code = pe.read(min(0x60, e - b))
    from capstone import Cs, CS_ARCH_X86, CS_MODE_64
    import re
    md = Cs(CS_ARCH_X86, CS_MODE_64)
    imgbase = 0x180000000
    for ins in md.disasm(code, imgbase + b):
        line = "  +0x%05x: %-8s %s" % (ins.address - imgbase, ins.mnemonic, ins.op_str)
        mm = re.search(r"rip ([+-]) (0x[0-9a-f]+)", ins.op_str)
        if mm:
            d = int(mm.group(2), 16) * (1 if mm.group(1) == "+" else -1)
            print(line, "  ; exe?+0x%x" % (ins.address + ins.size + d - imgbase))
        elif ins.mnemonic in ("call", "jmp") and ins.op_str.startswith("0x"):
            print(line, "  ; lib+0x%x" % (int(ins.op_str, 16) - imgbase))
        else:
            print(line)
        if ins.mnemonic == "ret":
            break
else:
    print("no pdata func covers 0xcfbb00")
