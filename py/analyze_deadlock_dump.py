#!/usr/bin/env python3
"""解析全量 minidump: 全线程栈回溯 (裸栈扫描模块内地址) — GUI 死锁定位
用法: python analyze_deadlock_dump.py <dump路径> [topN]
"""
import sys, struct
from minidump.minidumpfile import MinidumpFile

DUMP = sys.argv[1]
TOPN = int(sys.argv[2]) if len(sys.argv) > 2 else 14

mdf = MinidumpFile.parse(DUMP)
f = open(DUMP, "rb")

mods = []
for m in mdf.modules.modules:
    mods.append((int(m.baseaddress), int(m.size), m.name.replace("\\", "/").split("/")[-1]))
mods.sort()

def find_mod(addr):
    lo, hi = 0, len(mods)
    while lo < hi:
        mid = (lo + hi) // 2
        b, s, n = mods[mid]
        if addr < b: hi = mid
        elif addr >= b + s: lo = mid + 1
        else: return n, addr - b
    return None, 0

def read_rva(rva, size):
    f.seek(rva)
    return f.read(size)

# Memory64List — 手动从 stream directory 解析 (库不保留 base rva)
mem = []
f.seek(0)
hdr = f.read(32)
num_streams = struct.unpack_from("<I", hdr, 8)[0]
dir_rva = struct.unpack_from("<I", hdr, 12)[0]
mem64_rva = None
for i in range(num_streams):
    f.seek(dir_rva + i * 16)
    st, sz, r, d = struct.unpack("<IIII", f.read(16))
    if st == 9:  # Memory64ListStream
        mem64_rva = ("64", r)
    elif st == 5:  # MemoryListStream
        mem64_rva = ("32", r)
if mem64_rva:
    kind, mrva = mem64_rva
    if kind == "64":
        f.seek(mrva)
        buf = f.read(16 + 64 * 200000)
        n = struct.unpack_from("<Q", buf, 0)[0]
        base = struct.unpack_from("<Q", buf, 8)[0]
        off = 16
        for i in range(min(n, 200000)):
            start = struct.unpack_from("<Q", buf, off)[0]
            size = struct.unpack_from("<Q", buf, off + 8)[0]
            mem.append((start, size, base)); base += size; off += 16
    else:
        f.seek(mrva)
        n = struct.unpack_from("<I", f.read(4), 0)[0]
        buf = f.read(n * 16)
        for i in range(n):
            start = struct.unpack_from("<Q", buf, i * 16)[0]
            size = struct.unpack_from("<I", buf, i * 16 + 8)[0]
            rva = struct.unpack_from("<I", buf, i * 16 + 12)[0]
            mem.append((start, size, rva))
print(f"内存段: {len(mem)}")
mem.sort(key=lambda x: x[0])

def read_mem(addr, size):
    lo, hi = 0, len(mem)
    while lo < hi:
        mid = (lo + hi) // 2
        s, sz, rv = mem[mid]
        if addr < s: hi = mid
        elif addr >= s + sz: lo = mid + 1
        else:
            off = addr - s
            n = min(size, sz - off)
            f.seek(rv + off)
            return f.read(n)
    return None

threads = mdf.threads.threads
print(f"线程: {len(threads)}\n")
OFF_RSP, OFF_RIP = 0x98, 0xF8

rows = []
for t in threads:
    tc = t.ThreadContext
    raw = read_rva(tc.Rva, tc.DataSize)
    if not raw or len(raw) < 0x100:
        continue
    rsp = struct.unpack_from("<Q", raw, OFF_RSP)[0]
    rip = struct.unpack_from("<Q", raw, OFF_RIP)[0]
    rows.append((t.ThreadId, rip, rsp))

# 排序: 非 ntdll/kernel32 wait 线程优先 (业务线程)
def score(rip):
    n, _ = find_mod(rip)
    return 0 if n in ("ntdll.dll", "kernel32.dll", "KERNELBASE.dll", "win32u.dll", "user32.dll") else 1

rows.sort(key=lambda x: -score(x[1]))
for tid, rip, rsp in rows[:TOPN]:
    mn, off = find_mod(rip)
    stack = read_mem(rsp, 0x8000)
    frames = []
    dedup = []
    if stack:
        for i in range(len(stack) // 8):
            v = struct.unpack_from("<Q", stack, i * 8)[0]
            n2, o2 = find_mod(v)
            if n2 and o2 > 0:
                frames.append((n2, o2))
        # 去重连续
        dedup = []
        for fr in frames:
            if not dedup or dedup[-1] != fr:
                dedup.append(fr)
    print(f"TID={tid} RIP={mn}+0x{off:X}  栈帧{len(dedup)}:")
    for n2, o2 in dedup[:16]:
        print(f"    {n2} +0x{o2:X}")
    print()
