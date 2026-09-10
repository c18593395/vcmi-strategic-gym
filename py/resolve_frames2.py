# -*- coding: utf-8 -*-
"""gui5 冻结: 从 pdata 函数起点反汇编 + rip-rel 字符串引用"""
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
    # .pdata
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

def cstr_at(key, rva, maxlen=110):
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

def disasm_fn(key, fn_rva, n=26):
    pe, imgbase, secs, fns = PES[key]
    code = read_rva(key, fn_rva, n * 14 + 48)
    print('=== %s fn+0x%x ===' % (key, fn_rva))
    cnt = 0
    for ins in md.disasm(code, imgbase + fn_rva):
        irva = ins.address - imgbase
        extra = ''
        m = re.search(r'\[rip ([+-]) (0x[0-9a-f]+)\]', ins.op_str)
        if m:
            delta = int(m.group(2), 16) * (1 if m.group(1) == '+' else -1)
            tgt = ins.address + ins.size + delta - imgbase
            s = cstr_at(key, tgt)
            extra = ' ; ->+0x%x' % tgt
            if s:
                extra += ' "%s"' % s[:76]
        if ins.mnemonic in ('call', 'jmp') and re.match(r'^0x[0-9a-f]+$', ins.op_str):
            tgt = int(ins.op_str, 16) - imgbase
            k2 = 'fn+0x%x' % tgt if tgt in fns else '+0x%x' % tgt
            extra = ' ; %s' % k2
        print('  +0x%05x  %-8s %-38s%s' % (irva, ins.mnemonic, ins.op_str, extra))
        cnt += 1
        if cnt >= n:
            break
    print()

JOBS = [
    ('exe', 0x7447a0, 'main-thread top frame A'),
    ('exe', 0x744cf0, 'main-thread top frame B'),
    ('exe', 0x8230e0, 'MAIN THREAD wait caller (KEY)'),
    ('exe', 0x1c4930, 'TID=12156 thread entry (KEY)'),
    ('exe', 0x1c3a80, 'TID=12156 wait caller'),
    ('exe', 0x78cab0, 'TID=10092 thread entry (KEY)'),
    ('exe', 0x2007c0, 'TID=10092 mid frame'),
    ('exe', 0x78ec60, 'TID=10092 frame B'),
    ('lib', 0x941730, 'shared wait primitive'),
    ('lib', 0x706b0, 'TID=12156 chain top'),
    ('lib', 0x70270, 'TID=12156 chain'),
]

for key, rva, label in JOBS:
    print('--- %s ---' % label)
    disasm_fn(key, rva, 22)
