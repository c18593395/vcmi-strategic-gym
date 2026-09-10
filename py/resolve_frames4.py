# -*- coding: utf-8 -*-
"""gui5: main() 内 0x825656 等待点归属 + lib 等待原语反汇编"""
import struct, re
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
        pe.seek(pdata[2])
        blob = pe.read(pdata[1])
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
fnsE = PES['exe'][3]
fnsL = PES['lib'][3]

# ---- [1] main 内对 0x1a3ca0 的调用点 ----
print('=== main 范围内 call 0x1a3ca0 的位置 ===')
code = read_rva('exe', 0x8230e0, 0x828000 - 0x8230e0)
for ins in md.disasm(code, PES['exe'][1] + 0x8230e0):
    irva = ins.address - PES['exe'][1]
    if irva > 0x828000:
        break
    if ins.mnemonic == 'call' and re.match(r'^0x', ins.op_str):
        tgt = int(ins.op_str, 16) - PES['exe'][1]
        if tgt in (0x1a3ca0, 0x2abe50, 0x1a3a70):
            print('  call@exe+0x%x -> fn+0x%x' % (irva, tgt))

# ---- [2] 以 0x825656 为中心: 从 main 起点线性反汇编, 只打印 0x8255xx-0x8256xx ----
print('\n=== main 内 0x825656 附近指令 ===')
for ins in md.disasm(code, PES['exe'][1] + 0x8230e0):
    irva = ins.address - PES['exe'][1]
    if irva > 0x825700:
        break
    if 0x8255a0 <= irva <= 0x825690:
        extra = ''
        m = re.search(r'\[rip ([+-]) (0x[0-9a-f]+)\]', ins.op_str)
        if m:
            delta = int(m.group(2), 16) * (1 if m.group(1) == '+' else -1)
            tgt = ins.address + ins.size + delta - PES['exe'][1]
            s = cstr_at('exe', tgt)
            extra = ' ; +0x%x' % tgt
            if s:
                extra += ' "%s"' % s[:70]
        if ins.mnemonic in ('call', 'jmp') and re.match(r'^0x', ins.op_str):
            t2 = int(ins.op_str, 16) - PES['exe'][1]
            extra = ' ; %s' % ('fn+0x%x' % t2 if t2 in fnsE else '+0x%x' % t2)
        print('  exe+0x%05x  %-8s %-36s%s' % (irva, ins.mnemonic, ins.op_str, extra))

# ---- [3] lib fn+0x75d20 与 fn+0x941730 ----
def disasm_lib(fn, n, label):
    print('\n=== lib fn+0x%x (%s) ===' % (fn, label))
    code = read_rva('lib', fn, n * 14 + 32)
    cnt = 0
    for ins in md.disasm(code, PES['lib'][1] + fn):
        irva = ins.address - PES['lib'][1]
        extra = ''
        m = re.search(r'\[rip ([+-]) (0x[0-9a-f]+)\]', ins.op_str)
        if m:
            delta = int(m.group(2), 16) * (1 if m.group(1) == '+' else -1)
            tgt = ins.address + ins.size + delta - PES['lib'][1]
            s = cstr_at('lib', tgt)
            extra = ' ; +0x%x' % tgt
            if s:
                extra += ' "%s"' % s[:70]
        if ins.mnemonic in ('call', 'jmp') and re.match(r'^0x', ins.op_str):
            t2 = int(ins.op_str, 16) - PES['lib'][1]
            extra = ' ; %s' % ('fn+0x%x' % t2 if t2 in fnsL else '+0x%x' % t2)
        print('  lib+0x%05x  %-8s %-36s%s' % (irva, ins.mnemonic, ins.op_str, extra))
        cnt += 1
        if cnt >= n:
            break

disasm_lib(0x75d20, 16, 'runNetwork 等待中转')
disasm_lib(0x941730, 20, '共享等待原语')
