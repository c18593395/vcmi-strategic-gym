# -*- coding: utf-8 -*-
"""gui8: 定位主线程 SDL_WaitThread 调用者 (0x2ab835 / 0x2ac3ad) 的函数身份"""
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
pdata = None
for i in range(nsec):
    s = pe.read(40)
    vsize, vaddr, rsize, raddr = struct.unpack("<IIII", s[8:24])
    name = s[:8].decode('ascii', 'replace').rstrip('\x00')
    secs.append((vaddr, max(vsize, rsize), raddr, name))
    if name == '.pdata':
        pdata = (vaddr, max(vsize, rsize), raddr)

def rva2off(rva):
    for vaddr, size, raddr, _n in secs:
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

pe.seek(pdata[2])
blob = pe.read(pdata[1])
fns = []
for i in range(0, len(blob) - 12, 12):
    s, e, _u = struct.unpack_from('<III', blob, i)
    if s:
        fns.append((s, e))
fns.sort()

def fn_of(rva):
    for s, e in fns:
        if s <= rva < e:
            return s, e
    return None

md = Cs(CS_ARCH_X86, CS_MODE_64)

# 反汇编 0x2ab835 与 0x2ac3ad 所在函数, 各打前后文
for target in (0x2ab835, 0x2ac3ad):
    fs, fe = fn_of(target)
    print('=== 0x%x in fn [0x%x - 0x%x) size=0x%x ===' % (target, fs, fe, fe - fs))
    o = rva2off(fs)
    pe.seek(o)
    code = pe.read(min(fe - fs, 0x300))
    count = 0
    for ins in md.disasm(code, imgbase + fs):
        rva = ins.address - imgbase
        extra = ''
        m = re.search(r'\[rip ([+-]) (0x[0-9a-f]+)\]', ins.op_str)
        if m:
            delta = int(m.group(2), 16) * (1 if m.group(1) == '+' else -1)
            tgt = ins.address + ins.size + delta - imgbase
            extra = ' ; ->+0x%x' % tgt
            s2 = cstr_at(tgt)
            if s2:
                extra += ' "%s"' % s2[:70]
        if ins.mnemonic in ('call', 'jmp') and ins.op_str.startswith('0x'):
            extra = ' ; ->+0x%x' % (int(ins.op_str, 16) - imgbase)
        mark = '  <<<' if rva == target else ''
        print('  +0x%05x  %-8s %-36s%s%s' % (rva, ins.mnemonic, ins.op_str, extra, mark))
        count += 1
        if count > 70 or (ins.mnemonic == 'ret' and rva >= target):
            break
    print()
