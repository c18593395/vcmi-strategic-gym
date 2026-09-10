# -*- coding: utf-8 -*-
"""gui8: 读真正的 winpthreads mutex 结构体 (pthread_mutex_t = 指针) 找 owner"""
import struct, bisect

DUMP = r"D:\Bigdata\hero3_fresh\py\gui8_stuck.dmp"
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

# 已知线程 TID (33 线程) 供 owner 匹配
tid_set = set()
try:
    for t in mf.threads.threads:
        tid_set.add(t.ThreadId)
except Exception as e:
    print("threads:", e)
print("线程数:", len(tid_set))

eng_l1 = struct.unpack("<Q", read_mem(exe_base + 0x959c60, 8))[0]
eng = struct.unpack("<Q", read_mem(eng_l1, 8))[0]
mutex_handle_ptr = struct.unpack("<Q", read_mem(eng + 0x98, 8))[0]
print("ENGINE=0x%x  mutex句柄槽(ENGINE+0x98)=0x%x" % (eng, mutex_handle_ptr))

# 真正的 mutex 结构体
mstruct = mutex_handle_ptr
mb = read_mem(mstruct, 0x80)
print("mutex struct @0x%x:" % mstruct)
for i in range(0, min(len(mb), 0x80), 8):
    v = struct.unpack_from("<Q", mb, i)[0]
    note = ''
    if v in tid_set:
        note = '  <<< TID %d (OWNER?)' % v
    print("  +0x%02x: 0x%016x%s" % (i, v, note))
