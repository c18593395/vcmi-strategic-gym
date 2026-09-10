# -*- coding: utf-8 -*-
"""解析 VCMI_client.exe 导入表: 定位 IAT 槽 0xa9e770/0xa9e778 的导入函数名"""
import struct

pe = open(r"D:\vcmi-fork-build\bin\VCMI_client.exe", 'rb')
dd = pe.read(0x400)
p = struct.unpack_from('<I', dd, 0x3C)[0]
pe.seek(p)
pehdr = pe.read(0x18)
nsec = struct.unpack_from('<H', pehdr, 6)[0]
optsize = struct.unpack_from('<H', pehdr, 20)[0]
opt = pe.read(optsize)
imp_rva, imp_sz = struct.unpack_from('<II', opt, 120)
secs = []
for i in range(nsec):
    s = pe.read(40)
    vsize, vaddr, rsize, raddr = struct.unpack('<IIII', s[8:24])
    secs.append((vaddr, max(vsize, rsize), raddr))

def rva2off(rva):
    for vaddr, size, raddr in secs:
        if vaddr <= rva < vaddr + size:
            return raddr + (rva - vaddr)
    return None

o = rva2off(imp_rva)
pe.seek(o)
TARGETS = {0xa9e770, 0xa9e778, 0xa9bbc0, 0xa9e3a0}
while True:
    d = pe.read(20)
    if len(d) < 20:
        break
    _c, _t, _f, nameRva, firstThunk = struct.unpack('<IIIII', d)
    if nameRva == 0 and firstThunk == 0:
        break
    nOff = rva2off(nameRva)
    tOff = rva2off(firstThunk)
    if nOff is None or tOff is None:
        continue
    pe.seek(nOff)
    dll = pe.read(64).split(b'\x00')[0].decode('latin1', 'replace')
    cur = pe.tell()
    pe.seek(tOff)
    idx = 0
    names = {}
    while True:
        v = struct.unpack('<Q', pe.read(8))[0]
        if v == 0:
            break
        slot = firstThunk + idx * 8
        if slot in TARGETS:
            if v & (1 << 63):
                names[slot] = 'ordinal#%d' % (v & 0xffffffff)
            else:
                save = pe.tell()
                pe.seek(rva2off(v & 0xffffffff) + 2)
                names[slot] = pe.read(90).split(b'\x00')[0].decode('utf-8', 'replace')
                pe.seek(save)
        idx += 1
    if names:
        for slot, nm in sorted(names.items()):
            print('exe+0x%x = %s!%s' % (slot, dll, nm))
    pe.seek(cur)
