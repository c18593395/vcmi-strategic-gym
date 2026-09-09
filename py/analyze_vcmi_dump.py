#!/usr/bin/env python3
"""解析 VCMI_client.exe minidump (手动 CONTEXT x64 解析版)
用法: python analyze_vcmi_dump.py [dump路径]
"""
import sys, struct, io
from minidump.minidumpfile import MinidumpFile

DUMP = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\Administrator\Documents\My Games\vcmi\logs\VCMI_client.exe_crashinfo.dmp"

mdf = MinidumpFile.parse(DUMP)
f = open(DUMP, "rb")  # 原始文件句柄

# 模块表
mods = []
for m in mdf.modules.modules:
    mods.append((int(m.baseaddress), int(m.size), m.name.replace("\\", "/").split("/")[-1]))
mods.sort()

def find_mod(addr):
    for base, size, name in mods:
        if base <= addr < base + size:
            return name, addr - base
    return None, 0

def read_rva(rva, size):
    f.seek(rva)
    return f.read(size)

# 内存块 (Memory64List 或 MemoryList)
mem = []  # (start, size, rva)
try:
    m64 = mdf.memory_segments_64
    if m64 and getattr(m64, "memory_segments", None):
        rva = m64.mem_rva if hasattr(m64, "mem_rva") else None
        total = 0
        for seg in m64.memory_segments:
            start = int(seg.start_virtual_address); size = int(seg.size)
            mem.append((start, size, rva + total))
            total += size
        print(f"Memory64List: {len(mem)} 段")
except Exception as e:
    print("memory64 fail:", e)
if not mem:
    try:
        ml = mdf.memory_segments
        if ml and getattr(ml, "memory_segments", None):
            for seg in ml.memory_segments:
                start = int(seg.start_virtual_address)
                size = int(seg.size)
                # MemoryList 每段自带 rva
                rva = int(getattr(seg, "file_offset", 0) or getattr(seg, "rva", 0) or 0)
                if rva:
                    mem.append((start, size, rva))
            print(f"MemoryList: {len(mem)} 段")
    except Exception as e:
        print("memorylist fail:", e)

def read_mem(addr, size):
    for start, msize, mrva in mem:
        if start <= addr < start + msize:
            off = addr - start
            n = min(size, msize - off)
            f.seek(mrva + off)
            return f.read(n)
    return None

# 异常线程 (ExceptionList 第一项)
exc_tid = 0x8088
print("=== 异常 ===")
print(f"异常线程 TID={exc_tid:#x}  ExceptionAddress=0x7fffa354182f (ntdll 堆报告路径)")

# 上下文 x64 偏移
OFF_RSP, OFF_RIP = 0x98, 0xF8

threads = mdf.threads.threads
print(f"\n共 {len(threads)} 线程; 输出异常线程 + 全部线程 RIP 摘要")

def ctx_of(t):
    tc = t.ThreadContext
    raw = read_rva(tc.Rva, tc.DataSize)
    if not raw or len(raw) < 0x100:
        return None, None, None
    rsp, rip = struct.unpack_from("<Q", raw, OFF_RSP)[0], struct.unpack_from("<Q", raw, OFF_RIP)[0]
    regs = struct.unpack_from("<16Q", raw, 0x78)  # Rax..R15
    return rip, rsp, regs

target = None
for t in threads:
    if t.ThreadId == exc_tid:
        target = t
        break
if target is None and threads:
    target = threads[0]

rip, rsp, regs = ctx_of(target)
print(f"\n=== 崩溃线程 TID={target.ThreadId} ===")
if rip is None:
    print("上下文读取失败")
else:
    mn, off = find_mod(rip)
    print(f"RIP=0x{rip:016X} ({mn}+0x{off:X})  RSP=0x{rsp:016X}")
    regn = ["Rax","Rcx","Rdx","Rbx","Rsp","Rbp","Rsi","Rdi","R8","R9","R10","R11","R12","R13","R14","R15"]
    print("  " + " ".join(f"{regn[i]}=0x{regs[i]:X}" for i in range(16) if regn[i] != "Rsp"))
    # 裸栈扫描
    stack = read_mem(rsp, 0x20000)
    if stack:
        hits = []
        for i in range(len(stack) // 8):
            v = struct.unpack_from("<Q", stack, i * 8)[0]
            mn2, off2 = find_mod(v)
            if mn2 and off2 > 0:
                hits.append((rsp + i * 8, mn2, off2))
        print(f"\n裸栈模块地址 (前 45 / 共 {len(hits)}):")
        for a, tn, off2 in hits[:45]:
            print(f"  [0x{a:012X}] {tn} +0x{off2:X}")
    else:
        print("(栈内存不在 dump)")

print("\n=== 全线程 RIP 摘要 ===")
for t in threads:
    r, s, _ = ctx_of(t)
    if r is None:
        print(f"  TID={t.ThreadId:>6} (无上下文)")
        continue
    mn, off = find_mod(r)
    mark = " <== 异常" if t.ThreadId == exc_tid else ""
    print(f"  TID={t.ThreadId:>6} RIP={mn}+0x{off:X}{mark}")
