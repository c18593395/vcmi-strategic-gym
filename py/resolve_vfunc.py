# -*- coding: utf-8 -*-
# 从 dump 解析 8256 线程卡死的虚函数: this(R12) -> +0xb0 子对象 -> vtable[9] -> 模块 RVA
import struct, bisect

path = r"D:\Bigdata\hero3_fresh\dumps\gui_stuck_0908.dmp"
f = open(path, "rb")
d = f.read(32)
num_streams, dir_rva = struct.unpack_from("<II", d, 8)
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
mf = MinidumpFile.parse(path)
mods = []
for m in mf.modules.modules:
    mods.append((str(m.name).split("\\")[-1], m.baseaddress, m.size))

def sym(va):
    for name, base, size in mods:
        if base <= va < base + size:
            return "%s+0x%x" % (name, va - base)
    return "0x%x" % va

this_ptr = 0x1b042586c10
obj = read_mem(this_ptr + 0xB0, 8)
subobj = struct.unpack("<Q", obj)[0]
print("this=0x%x  this+0xb0 -> subobj=0x%x" % (this_ptr, subobj))
vt = read_mem(subobj, 8)
vtptr = struct.unpack("<Q", vt)[0]
print("subobj vtable = %s" % sym(vtptr))
slot9 = read_mem(vtptr + 0x48, 8)
fn = struct.unpack("<Q", slot9)[0]
print("vtable[9] (vtable+0x48) = %s" % sym(fn))

# 打印 subobj 头部内存, 便于人工对照
raw = read_mem(subobj, 0x40)
print("subobj dump:", raw.hex())

# vtable 前 12 个槽
vb = read_mem(vtptr, 0x60)
print("vtable slots:")
for i in range(0, 0x60, 8):
    v = struct.unpack_from("<Q", vb, i)[0]
    print("  [%d] %s" % (i // 8, sym(v)))
