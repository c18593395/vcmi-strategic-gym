# -*- coding: utf-8 -*-
"""gui8: 反汇编新二进制 onPacketReceived 区域 (0x1c3a00-0x1c3d00) 定位等待点"""
import struct, re
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

EXE = r"D:\vcmi-fork-build\bin\VCMI_client.exe"
pe = open(EXE, "rb")
dd = pe.read(0x400)
p = struct.unpack_from("<I", dd, 0x3C)[0]
pe.seek(p); pehdr = pe.read(0x18)
nsec = struct.unpack_from("<H", pehdr, 6)[0]
optsize = struct.unpack_from("<H", pehdr, 20)[0]
opt = pe.read(optsize)
imgbase = struct.unpack_from("<Q", opt, 24)[0]
secs = []
for i in range(nsec):
    s = pe.read(40)
    vsize, vaddr, rsize, raddr = struct.unpack("<IIII", s[8:24])
    secs.append((vaddr, max(vsize, rsize), raddr))

def rva2off(rva):
    for vaddr, size, raddr in secs:
        if vaddr <= rva < vaddr + size:
            return raddr + (rva - vaddr)
    return None

def cstr_at(rva, maxlen=110):
    o = rva2off(rva)
    if o is None:
        return None
    pe.seek(o)
    raw = pe.read(maxlen)
    s = raw.split(b'\x00')[0]
    if len(s) < 4:
        return None
    try:
        t = s.decode('utf-8')
    except UnicodeDecodeError:
        return None
    pr = sum(1 for c in t if c.isprintable())
    return t if pr > len(t) * 0.85 else None

md = Cs(CS_ARCH_X86, CS_MODE_64)
o = rva2off(0x1C3A20)
pe.seek(o)
code = pe.read(0x300)
for ins in md.disasm(code, imgbase + 0x1C3A20):
    rva = ins.address - imgbase
    extra = ''
    m = re.search(r'\[rip ([+-]) (0x[0-9a-f]+)\]', ins.op_str)
    if m:
        delta = int(m.group(2), 16) * (1 if m.group(1) == '+' else -1)
        tgt = ins.address + ins.size + delta - imgbase
        extra = ' ; ->+0x%x' % tgt
        s = cstr_at(tgt)
        if s:
            extra += ' "%s"' % s[:70]
    if ins.mnemonic in ('call', 'jmp') and ins.op_str.startswith('0x'):
        extra = ' ; ->+0x%x' % (int(ins.op_str, 16) - imgbase)
    mark = '  <<<' if rva in (0x1c3ae9, 0x1c3c10) else ''
    print('  +0x%05x  %-8s %-38s%s%s' % (rva, ins.mnemonic, ins.op_str, extra, mark))
