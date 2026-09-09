# -*- coding: utf-8 -*-
# gui_stuck4: 检查 GAME 对象 + mutex 周边内存是否堆损坏
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

GAME = 0x1c8e518c780
MUTEX = GAME + 0x98

print("=== GAME 对象 [0x%x, +0x110) ===" % GAME)
blk = read_mem(GAME, 0x110)
for i in range(0, len(blk), 8):
    v = struct.unpack_from("<Q", blk, i)[0]
    m, r = mod_of(v)
    tag = " (%s+0x%x)" % (m, r) if m else ""
    mark = " <== MUTEX+0x00(owner)" if GAME + i == MUTEX else (" <== MUTEX 区" if MUTEX < GAME + i < MUTEX + 0x30 else "")
    print("  +0x%03x: 0x%016x%s%s" % (i, v, tag, mark))

# 对照: 其他 GameEngine 级 mutex/对象成员是否完好
# 上轮数据: onPacketReceived 用全局 GAME 槽 exe+0x958920, 主线程用 exe+0xa879b0
print("\n=== 主线程全局槽 exe+0xa879b0 与 网络线程全局槽 exe+0x958920 指向对照 ===")
exe_base = None
for name, base, size in mods:
    if name == "VCMI_client.exe":
        exe_base = base
for slot_rva in (0xa879b0, 0x958920):
    b = read_mem(exe_base + slot_rva, 8)
    if b:
        v = struct.unpack("<Q", b)[0]
        print("  exe+0x%x -> 0x%x %s" % (slot_rva, v, "(GAME)" if v == GAME else "(≠GAME!)"))

# owner 指针所在堆块与 GAME 的堆块是否相邻(溢出源分析)
print("\n=== 堆地址上下文 ===")
for label, addr in (("GAME", GAME), ("OWNER", 0x1c8f5f22ea0), ("MUTEX", MUTEX)):
    before = read_mem(addr - 0x20, 0x20)
    print("  %s (0x%x) 前 0x20 字节:" % (label, addr))
    for i in range(0, len(before), 8):
        print("    -0x%02x: 0x%016x" % (0x20 - i, struct.unpack_from("<Q", before, i)[0]))
