# -*- coding: utf-8 -*-
"""gui5: 读正确的 interfaceMutex 地址 (heap ENGINE+0x98) 找 owner"""
import struct, bisect

DUMP = r"D:\Bigdata\hero3_fresh\py\gui5_stuck.dmp"
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
mods = [(str(m.name).split("\\")[-1], m.baseaddress, m.size) for m in mf.modules.modules]
exe_base = next(b for n, b, s in mods if n == "VCMI_client.exe")

game = struct.unpack("<Q", read_mem(exe_base + 0xa879b0, 8))[0]
print("ENGINE/GAME heap obj = 0x%x" % game)

mutex_va = game + 0x98
mb = read_mem(mutex_va, 0x80)
print("interfaceMutex @0x%x:" % mutex_va)
for i in range(0, min(len(mb), 0x60), 8):
    print("  +0x%02x: 0x%016x" % (i, struct.unpack_from("<Q", mb, i)[0]))

# CRITICAL_SECTION 布局解析 (winpthreads mutex 内部 = CS)
if len(mb) >= 0x20:
    dbg, lockcnt, reccnt, owner, sema, spin = struct.unpack_from("<QIIQQQ", mb, 0)
    # LockCount 有符号解释: 未持有 = -1 (0xffffffff), 持有 >= 0
    lk_signed = struct.unpack_from("<i", mb, 8)[0]
    print("\nCRITICAL_SECTION 解析:")
    print("  DebugInfo=0x%x" % dbg)
    print("  LockCount=%d (signed)  [未持有=-1]" % lk_signed)
    print("  RecursionCount=%d" % reccnt)
    print("  OwningThread=0x%x (伪 handle)" % owner)
    print("  LockSemaphore=0x%x" % sema)
    print("  SpinCount=0x%x" % spin)

# 线程 handle -> TID 映射
print("\n线程表:")
try:
    for t in mf.threads.threads:
        print("  TID=%-6d" % t.ThreadId)
except Exception as e:
    print("  fail:", e)
