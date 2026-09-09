# -*- coding: utf-8 -*-
# 从 full dump 读各关键线程 CONTEXT 寄存器, 定位 interfaceMutex 持有者
# 主线程 (13848) 卡在 pthread_mutex_lock: Rcx = mutex 地址
# winpthreads pthread_mutex_t: 含 owner TID 字段
import struct, sys, bisect

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
    # 跨段读取
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

def ctx_regs(tid):
    for t in mf.threads.threads:
        if t.ThreadId != tid:
            continue
        lc = t.ThreadContext
        f.seek(lc.Rva)
        ctx = f.read(lc.DataSize)
        names = ["Rax", "Rcx", "Rdx", "Rbx", "Rsp", "Rbp", "Rsi", "Rdi",
                 "R8", "R9", "R10", "R11", "R12", "R13", "R14", "R15"]
        regs = {}
        for i, nm in enumerate(names):
            regs[nm] = struct.unpack_from("<Q", ctx, 0x78 + i * 8)[0]
        regs["Rip"] = struct.unpack_from("<Q", ctx, 0xF8)[0]
        return regs
    return None

# winpthreads 线程 TID 在 pthread 结构内以 DWORD 形式存在
all_tids = set(t.ThreadId for t in mf.threads.threads)

def scan_tids(base, size=64):
    b = read_mem(base, size)
    hits = []
    for i in range(0, max(0, len(b) - 3), 4):
        v = struct.unpack_from("<I", b, i)[0]
        if v in all_tids:
            hits.append(("+%02x" % i, v))
    return hits

print("==== 主线程 13848 (卡 interfaceMutex lock) ====")
r = ctx_regs(13848)
print({k: hex(v) for k, v in r.items()})
mutex_va = r["Rcx"]
print("mutex @ 0x%x" % mutex_va)
mb = read_mem(mutex_va, 64)
print("mutex raw:", mb.hex())
print("mutex 内 TID 候选:", scan_tids(mutex_va))

print()
print("==== 线程 8256 (卡 cond wait) ====")
r2 = ctx_regs(8256)
print({k: hex(v) for k, v in r2.items()})
# cond 相关寄存器可能在 Rdx/R8
for nm in ("Rdx", "R8", "Rbx", "Rdi", "Rsi"):
    va = r2[nm]
    if 0x10000 < va < 0x7fffffffffff:
        b = read_mem(va, 48)
        if b:
            h = scan_tids(va, 48)
            if h:
                print("  %s @0x%x 内 TID:" % (nm, va), h, b.hex())
