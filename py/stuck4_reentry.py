# -*- coding: utf-8 -*-
# gui_stuck4: 验证 onPacketReceived 锁地址 + 网络线程栈现场
import struct, bisect

DUMP = r"D:\Bigdata\hero3_fresh\gui_stuck4_0909.dmp"
EXE = r"D:\vcmi-fork-build\bin\VCMI_client.exe"

f = open(DUMP, "rb")
hdr = f.read(32)
num_streams, dir_rva = struct.unpack_from("<II", hdr, 8)
mem64 = []
for i in range(num_streams):
    f.seek(dir_rva + i * 12)
    st, sz, rva = struct.unpack("<III", f.read(12))
    if st == 9:
        f.seek(rva)
        n_ranges, base_rva = struct.unpack("<QQ", f.read(16))
        data_rva = base_rva
        for j in range(n_ranges):
            start, dsize = struct.unpack("<QQ", f.read(16))
            mem64.append((start, dsize, data_rva))
            data_rva += dsize
        break
mem64.sort()
starts = [m[0] for m in mem64]

def read_mem(addr, size):
    out = b""
    idx = bisect.bisect_right(starts, addr) - 1
    while len(out) < size and idx < len(mem64):
        start, dsize, rva = mem64[idx]
        if addr + len(out) < start:
            break
        off = (addr + len(out)) - start
        if off >= dsize:
            idx += 1
            continue
        n = min(size - len(out), dsize - off)
        f.seek(rva + off)
        out += f.read(n)
        idx += 1
    return out

from minidump.minidumpfile import MinidumpFile
mf = MinidumpFile.parse(DUMP)
mods = []
for m in mf.modules.modules:
    mods.append((str(m.name).split("\\")[-1], m.baseaddress, m.size))
def mod_of(va):
    for name, base, size in mods:
        if base <= va < base + size:
            return name, va - base
    return None, None
exe_base = None
for name, base, size in mods:
    if name == "VCMI_client.exe":
        exe_base = base

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

from capstone import Cs, CS_ARCH_X86, CS_MODE_64
import re
md = Cs(CS_ARCH_X86, CS_MODE_64)

print("=== onPacketReceived exe!fn[0x1c3a80) 前 0x140 字节 ===")
o = rva2off(0x1c3a80)
pe.seek(o)
code = pe.read(0x140)
for ins in md.disasm(code, imgbase + 0x1c3a80):
    line = "  +0x%05x: %-8s %s" % (ins.address - imgbase, ins.mnemonic, ins.op_str)
    mm = re.search(r"rip ([+-]) (0x[0-9a-f]+)", ins.op_str)
    if mm:
        d = int(mm.group(2), 16) * (1 if mm.group(1) == "+" else -1)
        tgt = ins.address + ins.size + d
        line += "   ; -> exe+0x%x" % (tgt - imgbase)
    elif ins.mnemonic in ("call", "jmp") and ins.op_str.startswith("0x"):
        line += "   ; exe+0x%x" % (int(ins.op_str, 16) - imgbase)
    print(line)

print("\n=== 网络线程 TID=33148 栈 hit 现场 (0xaaa29ff640 ±0x60) ===")
base_hit = 0xaaa29ff640
blk = read_mem(base_hit - 0x30, 0x90)
for i in range(0, len(blk), 8):
    va = base_hit - 0x30 + i
    v = struct.unpack_from("<Q", blk, i)[0]
    m, r = mod_of(v)
    tag = " (%s+0x%x)" % (m, r) if m else ""
    mark = " <== OWNER" if v == 0x1c8f5f22ea0 else ""
    mark += " <== MUTEX" if v == 0x1c8e518c818 else ""
    print("  0x%x: 0x%016x%s%s" % (va, v, tag, mark))

print("\n=== 主线程 TID=31440 栈 hit 现场 (0xaaa0bff7c0 ±0x60) ===")
base_hit2 = 0xaaa0bff7c0
blk = read_mem(base_hit2 - 0x30, 0x90)
for i in range(0, len(blk), 8):
    va = base_hit2 - 0x30 + i
    v = struct.unpack_from("<Q", blk, i)[0]
    m, r = mod_of(v)
    tag = " (%s+0x%x)" % (m, r) if m else ""
    mark = " <== OWNER" if v == 0x1c8f5f22ea0 else ""
    mark += " <== MUTEX" if v == 0x1c8e518c818 else ""
    print("  0x%x: 0x%016x%s%s" % (va, v, tag, mark))
