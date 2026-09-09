# -*- coding: utf-8 -*-
# gui_stuck4: 找持锁线程 — owner 堆块内容 + 全线程栈搜索 owner 指针
import struct, bisect

DUMP = r"D:\Bigdata\hero3_fresh\gui_stuck4_0909.dmp"

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

OWNER = 0x1c8f5f22ea0

print("=== owner 线程对象 0x%x 的前 0x140 字节 ===" % OWNER)
blk = read_mem(OWNER, 0x140)
for i in range(0, len(blk), 8):
    v = struct.unpack_from("<Q", blk, i)[0]
    if v:
        m, r = mod_of(v)
        tag = " (%s+0x%x)" % (m, r) if m else ""
        # 找像 TID 的值
        print("  +0x%03x: 0x%016x%s" % (i, v, tag))

print("\n=== 全线程栈搜索 owner 值 0x%x ===" % OWNER)
pat = struct.pack("<Q", OWNER)
owner_hex = "%016x" % OWNER
for t in mf.threads.threads:
    tid = t.ThreadId
    lc = t.ThreadContext
    f2 = lc
    import struct as _s
    ctx_off = lc.Rva
    f.seek(ctx_off)
    ctx = f.read(lc.DataSize)
    rsp = _s.unpack_from("<Q", ctx, 0x98)[0]
    rip = _s.unpack_from("<Q", ctx, 0xF8)[0]
    stack = read_mem(rsp, 0x9000)
    hits = []
    off = 0
    while True:
        idx = stack.find(pat, off)
        if idx < 0:
            break
        hits.append(rsp + idx)
        off = idx + 1
    if hits:
        m, r = mod_of(rip)
        print("TID=%-6d rip=%s+0x%x hits=%d @0x%s" % (tid, m, r, len(hits), " 0x%x" * min(len(hits), 3) % tuple(hits[:3]) if hits else ""))
