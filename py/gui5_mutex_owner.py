# -*- coding: utf-8 -*-
"""gui5 冻结: 读 ENGINE->interfaceMutex (ENGINE@exe+0x958920, +0x98) 内存找 owner"""
import struct, bisect

DUMP = r"D:\Bigdata\hero3_fresh\py\gui5_stuck.dmp"
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
mods = [(str(m.name).split("\\")[-1], m.baseaddress, m.size) for m in mf.modules.modules]
exe_base = next(base for name, base, size in mods if name == "VCMI_client.exe")
print("exe actual base = 0x%x" % exe_base)

# ---- ENGINE 全局 ----
eng_ptr_va = exe_base + 0x958920
buf = read_mem(eng_ptr_va, 8)
eng = struct.unpack("<Q", buf)[0]
print("[ENGINE] ptr@exe+0x958920 -> 0x%x" % eng)

# ---- interfaceMutex @ ENGINE+0x98 ----
mutex_va = eng + 0x98
mb = read_mem(mutex_va, 0x80)
print("[ENGINE+0x98] interfaceMutex raw @0x%x:" % mutex_va)
words = []
for i in range(0, min(len(mb), 0x60), 8):
    v = struct.unpack_from("<Q", mb, i)[0]
    words.append(v)
    print("  +0x%02x: 0x%016x" % (i, v))

# ---- libwinpthread pthread_mutex_t 布局解析 ----
# pthread_mutex_t (mingw-w64): { LockCount/CRITICAL_SECTION wrapper? }
# mingw pthread 使用 CRITICAL_SECTION + 附加字段 (递归计数/类型)
print("\n解析1: CRITICAL_SECTION (DebugInfo,LockCount,RecursionCount,OwningThread,LockSemaphore,SpinCount)")
if len(mb) >= 0x20:
    dbg, lockcnt, reccnt, owner, sema, spin = struct.unpack_from("<QIIQQQ", mb, 0)
    print("  DebugInfo=0x%x LockCount=%d(0x%x) RecursionCount=%d OwningThread=0x%x SpinCount=%d" % (
        dbg, lockcnt, lockcnt, reccnt, owner, spin))
    if owner:
        # owner 是线程 HANDLE; 找 dump 里对应线程 (ThreadList 有 handle)
        try:
            for t in mf.threads.threads:
                pass
        except Exception:
            pass

print("\n解析2: 假定 ptr-sized 字段为线程 TID 候选")
for i, v in enumerate(words):
    if 0x400 < v < 0x20000:  # TID 值范围
        print("  +0x%02x: 0x%x  <-- 可能是 TID=%d" % (i * 8, v, v))

# ---- 全 dump 线程表: TID + handle ----
print("\n线程表 (TID@RIP):")
try:
    for t in mf.threads.threads:
        print("  TID=%d handle=0x%x" % (t.ThreadId, t.Handle))
except Exception as e:
    print("threads parse fail:", e)
