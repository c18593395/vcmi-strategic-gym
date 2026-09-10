# -*- coding: utf-8 -*-
"""gui8: 读 interfaceMutex owner (fresh dump, ENGINE@0x959c60 链)"""
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

eng_slot = exe_base + 0x959c60
eng_l1 = struct.unpack("<Q", read_mem(eng_slot, 8))[0]
print("[0x959c60] = 0x%x (静态槽)" % eng_l1)
eng = struct.unpack("<Q", read_mem(eng_l1, 8))[0]
print("ENGINE heap = 0x%x" % eng)

mutex_va = eng + 0x98
mb = read_mem(mutex_va, 0x70)
print("interfaceMutex @0x%x:" % mutex_va)
KNOWN = {5128: 'main(5128)', 27596: 'runNetwork(27596)', 9772: 'runServer(9772)',
         6240: 'libwait(6240)', 11372: 'libwait(11372)', 13172: 'sdl-thread(13172)', 8256: 'audio(8256)'}
for i in range(0, min(len(mb), 0x60), 8):
    v = struct.unpack_from("<Q", mb, i)[0]
    note = ''
    if v in KNOWN:
        note = '  <<< %s' % KNOWN[v]
    elif 0x100 < v < 0x20000:
        note = '  <- TID 值?'
    print("  +0x%02x: 0x%016x%s" % (i, v, note))
