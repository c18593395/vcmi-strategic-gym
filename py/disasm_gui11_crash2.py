# -*- coding: utf-8 -*-
"""gui11: 崩点指令对齐反汇编 (枚举起始偏移, 找能对齐到 0x216556 的解码路径)"""
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
TARGET = 0x216556
best = None
for back in range(0x30, 0x10, -1):
    start = TARGET - back
    o = rva2off(start)
    pe.seek(o)
    code = pe.read(back + 16)
    ins_list = list(md.disasm(code, imgbase + start))
    hit = [ins for ins in ins_list if ins.address - imgbase == TARGET]
    if hit:
        best = ins_list
        break

if best:
    for ins in best:
        rva = ins.address - imgbase
        extra = ''
        m = re.search(r'\[rip ([+-]) (0x[0-9a-f]+)\]', ins.op_str)
        if m:
            delta = int(m.group(2), 16) * (1 if m.group(1) == '+' else -1)
            tgt = ins.address + ins.size + delta - imgbase
            extra = ' ; ->+0x%x' % tgt
            s2 = cstr_at(tgt)
            if s2:
                extra += ' "%s"' % s2[:76]
        if ins.mnemonic in ('call', 'jmp') and ins.op_str.startswith('0x'):
            extra = ' ; ->+0x%x' % (int(ins.op_str, 16) - imgbase)
        mark = '   <<< CRASH' if rva == TARGET else ''
        print('  +0x%05x  %-8s %-34s%s%s' % (rva, ins.mnemonic, ins.op_str, extra, mark))
        if rva >= TARGET + 0x14:
            break
else:
    print("no alignment found")
