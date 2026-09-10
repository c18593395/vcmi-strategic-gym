# -*- coding: utf-8 -*-
"""gui5 冻结: 批量解析 exe/lib 关键帧 -> 反汇编定位函数 (向前找 CC padding 边界)"""
import struct, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

FILES = {
    'exe': r"D:\vcmi-fork-build\bin\VCMI_client.exe",
    'lib': r"D:\vcmi-fork-build\bin\VCMI_lib.dll",
}

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
        secs.append((vaddr, max(vsize, rsize), raddr))
    return pe, imgbase, secs

PES = {}
for k, path in FILES.items():
    PES[k] = load_pe(path)

def rva2off(key, rva):
    pe, imgbase, secs = PES[key]
    for vaddr, size, raddr in secs:
        if vaddr <= rva < vaddr + size:
            return raddr + (rva - vaddr)
    return None

def read_rva(key, rva, size):
    o = rva2off(key, rva)
    if o is None:
        return b''
    pe, _, _ = PES[key]
    pe.seek(o)
    return pe.read(size)

def find_fn_start(key, rva, back=0x1800):
    """向前找 >=3 个连续 0xCC 边界"""
    blob = read_rva(key, rva - back, back)
    run = 0
    start = rva - back
    for i, b in enumerate(blob):
        if b == 0xCC:
            run += 1
        else:
            if run >= 3:
                start = rva - back + i
            run = 0
    return start

md = Cs(CS_ARCH_X86, CS_MODE_64)

def disasm(key, rva, n=14, label=''):
    start = find_fn_start(key, rva)
    code = read_rva(key, start, min(n * 12 + 32, 0x400))
    print('=== %s exe/base+0x%x (fn start ~0x%x, off 0x%x) %s ===' % (key, rva, start, rva - start, label))
    cnt = 0
    for ins in md.disasm(code, PES[key][1] + start):
        irva = ins.address - PES[key][1]
        tag = ' <<<' if irva == rva else ''
        print('  +0x%05x  %-8s %s%s' % (irva, ins.mnemonic, ins.op_str, tag))
        cnt += 1
        if cnt >= n:
            break
    print()

FRAMES = [
    ('exe', 0x825656, 'main-thread wait site (TID=2076)'),
    ('exe', 0x8230e0, 'main-thread caller'),
    ('exe', 0x1c3a80, 'TID=12156 wait caller'),
    ('exe', 0x1c4930, 'TID=12156 thread entry'),
    ('exe', 0x2007c0, 'TID=10092 frame'),
    ('exe', 0x78cab0, 'TID=10092 thread entry'),
    ('lib', 0x941730, 'shared wait (both threads)'),
    ('lib', 0x87130, 'shared frame'),
]

for key, rva, label in FRAMES:
    disasm(key, rva, 12, label)
