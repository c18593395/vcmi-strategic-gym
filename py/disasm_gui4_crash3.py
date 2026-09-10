# -*- coding: utf-8 -*-
"""反汇编崩溃函数 0x59ef0 的完整后半段 + 全局 0x958920 附近数据"""
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

def read_rva(rva, size):
    o = rva2off(rva)
    if o is None: return b''
    pe.seek(o); return pe.read(size)

def cstr_at(rva, maxlen=100):
    o = rva2off(rva)
    if o is None: return None
    pe.seek(o)
    raw = pe.read(maxlen)
    s = raw.split(b'\x00')[0]
    try:
        t = s.decode('utf-8')
    except UnicodeDecodeError:
        t = s.decode('latin1', 'replace')
    return t if t and all(31 < ord(c) < 127 or ord(c) > 0x4e00 for c in t[:20]) else None

md = Cs(CS_ARCH_X86, CS_MODE_64)
START = 0x59EF0
code = read_rva(START, 0x1C0)
print("=== full fn exe+0x59ef0 ===")
for ins in md.disasm(code, imgbase + START):
    rva = ins.address - imgbase
    extra = ''
    m = re.search(r'\[rip ([+-]) (0x[0-9a-f]+)\]', ins.op_str)
    if m:
        delta = int(m.group(2), 16) * (1 if m.group(1) == '+' else -1)
        tgt = ins.address + ins.size + delta - imgbase
        extra = ' ; ->exe+0x%x' % tgt
        s = cstr_at(tgt)
        if s:
            extra += ' "%s"' % s[:70]
    if ins.mnemonic.startswith('call') and re.match(r'^0x', ins.op_str):
        tgt = int(ins.op_str, 16) - imgbase
        extra = ' ; ->exe+0x%x' % tgt
    print("  exe+0x%05x  %-8s %-40s%s" % (rva, ins.mnemonic, ins.op_str, extra))
    if ins.mnemonic == 'ret':
        break
