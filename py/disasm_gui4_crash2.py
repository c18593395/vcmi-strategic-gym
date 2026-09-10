# -*- coding: utf-8 -*-
"""找崩溃函数起点: 向前扫描 0xCC padding / 函数序言, 再反汇编整个函数"""
import struct, re
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

EXE = r"D:\vcmi-fork-build\bin\VCMI_client.exe"
CRASH_RVA = 0x59F66

pe = open(EXE, "rb")
dd = pe.read(0x400)
p = struct.unpack_from("<I", dd, 0x3C)[0]
pe.seek(p); pehdr = pe.read(0x18)
nsec = struct.unpack_from("<H", pehdr, 6)[0]
optsize = struct.unpack_from("<H", pehdr, 20)[0]
opt = pe.read(optsize)
imgbase = struct.unpack_from("<Q", opt, 24)[0]
secs = []
for i in range(nsec):
    s = pe.read(40)
    vsize, vaddr, rsize, raddr = struct.unpack("<IIII", s[8:24])
    secs.append((vaddr, max(vsize, rsize), raddr))

def rva2off(rva):
    for vaddr, size, raddr in secs:
        if vaddr <= rva < vaddr + size:
            return raddr + (rva - vaddr)
    return None

def read_rva(rva, size):
    o = rva2off(rva)
    if o is None:
        return b''
    pe.seek(o)
    return pe.read(size)

# ---- 向前找函数起点: 连续 >=2 个 0xCC (int3 对齐填充) 之后即函数边界 ----
SCAN_START = CRASH_RVA - 0x2000
blob = read_rva(SCAN_START, CRASH_RVA - SCAN_START)
fn_start = None
run = 0
for i, b in enumerate(blob):
    if b == 0xCC:
        run += 1
    else:
        if run >= 3:
            fn_start = SCAN_START + i
        run = 0
if fn_start is None:
    fn_start = CRASH_RVA - 0x400
print("function start candidate: exe+0x%x (gap before crash: 0x%x bytes)" % (fn_start, CRASH_RVA - fn_start))

md = Cs(CS_ARCH_X86, CS_MODE_64)
code = read_rva(fn_start, 0x100)
print("=== prologue ===")
for ins in md.disasm(code, imgbase + fn_start):
    rva = ins.address - imgbase
    print("  exe+0x%05x  %-8s %s" % (rva, ins.mnemonic, ins.op_str))
    if ins.address - imgbase >= fn_start + 0x60:
        break

# ---- 全 exe .text 扫描 call 指令目标 = fn_start (E8 rel32) ----
text = None
for vaddr, size, raddr in secs:
    if vaddr <= CRASH_RVA < vaddr + size:
        text = (vaddr, size, raddr)
        break
tvaddr, tsize, traddr = text
pe.seek(traddr)
tbytes = pe.read(tsize)
callers = []
target_va = imgbase + fn_start
for i in range(len(tbytes) - 5):
    if tbytes[i] == 0xE8:
        rel = struct.unpack_from('<i', tbytes, i + 1)[0]
    else:
        continue
    src_va = imgbase + tvaddr + i
    if src_va + 5 + rel == target_va:
        callers.append(src_va - imgbase)
print("\ncallers of exe+0x%x: %s" % (fn_start, ['exe+0x%x' % c for c in callers]))
