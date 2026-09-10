# -*- coding: utf-8 -*-
"""列出 VCMI_client.exe 导入 DLL 与 IAT 范围 + 解析 0xa9e770/0xa9e778 邻近槽位"""
import struct

pe = open(r"D:\vcmi-fork-build\bin\VCMI_client.exe", 'rb')
dd = pe.read(0x400)
p = struct.unpack_from('<I', dd, 0x3C)[0]
pe.seek(p)
pehdr = pe.read(0x18)
nsec = struct.unpack_from('<H', pehdr, 6)[0]
optsize = struct.unpack_from('<H', pehdr, 20)[0]
opt = pe.read(optsize)
imp_rva = struct.unpack_from('<I', opt, 120)[0]
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

pe.seek(rva2off(imp_rva))
rows = []
while True:
    d = pe.read(20)
    if len(d) < 20:
        break
    _c, _t, _f, nameRva, firstThunk = struct.unpack('<IIIII', d)
    if nameRva == 0 and firstThunk == 0:
        break
    nOff = rva2off(nameRva)
    if nOff is None:
        continue
    pe.seek(nOff)
    dll = pe.read(64).split(b'\x00')[0].decode('latin1', 'replace')
    rows.append((dll, firstThunk))

for dll, ft in rows:
    print('%-30s firstThunk=0x%x' % (dll, ft))

# 找覆盖 0xa9e770 的 DLL
print()
for dll, ft in rows:
    print('%-30s range 0x%x - 0x%x' % (dll, ft, ft + 0x800))
