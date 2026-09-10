# -*- coding: utf-8 -*-
"""gui5 冻结: 深挖 fn+0x8230e0 / fn+0x1c3a80 / lib 等待原语 + 0x825656 归属函数"""
import struct, re, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

FILES = {'exe': r"D:\vcmi-fork-build\bin\VCMI_client.exe", 'lib': r"D:\vcmi-fork-build\bin\VCMI_lib.dll"}

def load_pe(path):
    pe = open(path, 'rb')
    dd = pe.read(0x400)
    p = struct.unpack_from('<I', dd, 0x3C)[0]
    pe.seek(p); pehdr = pe.read(0x18)
    nsec = struct.unpack_from('<H', pehdr, 6)[0]
    optsize = struct.unpack_from('<H', pehdr, 20)[0]
    opt = pe.read(optsize)
    imgbase = struct.unpack_from('<Q', opt, 24)[0]
    secs = []
    for i in range(nsec):
        s = pe.read(40)
        vsize, vaddr, rsize, raddr = struct.unpack('<IIII', s[8:24])
        secs.append((vaddr, max(vsize, rsize), raddr, s[:8].decode('ascii', 'replace').rstrip('\x00')))
    pdata = None
    for vaddr, size, raddr, name in secs:
        if name == '.pdata':
            pdata = (vaddr, size, raddr)
    fns = set()
    if pdata:
        pv, psz, pr = pdata
        pe.seek(pr)
        blob = pe.read(psz)
        for i in range(0, len(blob) - 12, 12):
            s, e, _u = struct.unpack_from('<III', blob, i)
            if s:
                fns.add(s)
    return pe, imgbase, secs, fns

PES = {k: load_pe(p) for k, p in FILES.items()}

def rva2off(key, rva):
    pe, imgbase, secs, fns = PES[key]
    for vaddr, size, raddr, _n in secs:
        if vaddr <= rva < vaddr + size:
            return raddr + (rva - vaddr)
    return None

def read_rva(key, rva, size):
    o = rva2off(key, rva)
    if o is None:
        return b''
    pe, _, _, _ = PES[key]
    pe.seek(o)
    return pe.read(size)

def cstr_at(key, rva, maxlen=120):
    o = rva2off(key, rva)
    if o is None:
        return None
    pe, _, _, _ = PES[key]
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

def disasm_range(key, start, length, fns):
    pe, imgbase, secs, _ = PES[key]
    code = read_rva(key, start, length)
    for ins in md.disasm(code, imgbase + start):
        irva = ins.address - imgbase
        extra = ''
        m = re.search(r'\[rip ([+-]) (0x[0-9a-f]+)\]', ins.op_str)
        if m:
            delta = int(m.group(2), 16) * (1 if m.group(1) == '+' else -1)
            tgt = ins.address + ins.size + delta - imgbase
            s = cstr_at(key, tgt)
            extra = ' ; +0x%x' % tgt
            if s:
                extra += ' "%s"' % s[:86]
        if ins.mnemonic in ('call', 'jmp') and re.match(r'^0x[0-9a-f]+$', ins.op_str):
            t2 = int(ins.op_str, 16) - imgbase
            extra = ' ; %s' % ('fn+0x%x' % t2 if t2 in fns else '+0x%x' % t2)
        print('  %s+0x%05x  %-8s %-36s%s' % (key, irva, ins.mnemonic, ins.op_str, extra))

fnsE = PES['exe'][3]
fnsL = PES['lib'][3]

print('=== [1] exe fn+0x8230e0 前 90 条 (主线程 KEY 函数, 找字符串) ===')
disasm_range('exe', 0x8230e0, 0x420, fnsE)

print('\n=== [2] exe 0x825656 附近 (RIP 现场) ===')
disasm_range('exe', 0x825600, 0x60, fnsE)

print('\n=== [3] lib fn+0x75d20 (runNetwork 筭中转) ===')
disasm_range('lib', 0x75d20, 0x70, fnsL)

print('\n=== [4] lib fn+0x941730 (共享等待) ===')
disasm_range('lib', 0x941730, 0x70, fnsL)
