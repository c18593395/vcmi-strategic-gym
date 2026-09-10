# -*- coding: utf-8 -*-
"""gui5: 验证 ENGINE 静态对象布局 + 找出被持有的锁"""
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

def mod_of(va):
    for n, b, s in mods:
        if b <= va < b + s:
            return "%s+0x%x" % (n, va - b)
    return "heap/unknown 0x%x" % va

slot_958920 = struct.unpack("<Q", read_mem(exe_base + 0x958920, 8))[0]
print("[0x958920] = 0x%x  (%s)" % (slot_958920, mod_of(slot_958920)))

val_a879b0 = struct.unpack("<Q", read_mem(exe_base + 0xa879b0, 8))[0]
print("[0xa879b0] = 0x%x  (%s)" % (val_a879b0, mod_of(val_a879b0)))

# ENGINE 对象候选 = slot_958920 的值 (exe+0xa879b0)。前 8 字节应是 vtable (exe 内)
eng = slot_958920
head = read_mem(eng, 0x10)
vt, f2 = struct.unpack_from("<QQ", head, 0)
print("ENGINE 对象头: [0]=0x%x (%s) [8]=0x%x (%s)" % (vt, mod_of(vt), f2, mod_of(f2)))

# 转储 ENGINE+0x80..0x180 区域找 CRITICAL_SECTION/cond 形态
print("\nENGINE+0x80..0x180 内存:")
base = eng + 0x80
mb = read_mem(base, 0x100)
for i in range(0, len(mb), 8):
    v = struct.unpack_from("<Q", mb, i)[0]
    note = ''
    if 0 < v < 0x20000:
        note = ' <- TID?'
    if v and (mod_of(v).startswith('VCMI') or 'heap' in mod_of(v)):
        pass
    print("  +0x%03x: 0x%016x%s" % (0x80 + i, v, note))
