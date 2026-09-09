# -*- coding: utf-8 -*-
# 扫 8256 线程栈, 按调用链结构 rsi -> [rsi+8] -> +8 -> vtable[+0x48] 匹配候选对象
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

def in_heap(va):
    return 0x100000000 < va < 0x800000000000

RSP8256 = 0x7de8dff508
stack = read_mem(RSP8256, 0x4000)
print("stack bytes: %d" % len(stack))

seen = set()
for off in range(0, len(stack) - 8, 8):
    p = struct.unpack_from("<Q", stack, off)[0]
    if not in_heap(p) or p in seen:
        continue
    seen.add(p)
    q_raw = read_mem(p + 8, 8)
    if len(q_raw) < 8:
        continue
    q = struct.unpack("<Q", q_raw)[0]
    if not in_heap(q):
        continue
    # 真实跳板链: sub = [objB+0xb0]; vt = [sub]; fn = [vt+0x48]
    r_raw = read_mem(q + 0xB0, 8)
    if len(r_raw) < 8:
        continue
    r = struct.unpack("<Q", r_raw)[0]
    if not in_heap(r):
        continue
    vt_raw = read_mem(r, 8)
    vt = struct.unpack("<Q", vt_raw)[0]
    fn_raw = read_mem(vt + 0x48, 8)
    if len(fn_raw) < 8:
        continue
    fn = struct.unpack("<Q", fn_raw)[0]
    s = sym(fn)
    if ".exe" in s or ".dll" in s:
        print("栈+0x%04x p=0x%x -> [%x+8]=0x%x -> +8=0x%x vt=%s fn=%s" % (off, p, p, q, r, sym(vt), s))
