# -*- coding: utf-8 -*-
"""gui12 第三崩溃: 反汇编 VCMI_client.exe 函数 0x20bf60 (崩点 0x20c09f)
SPECTATOR(-4) 观众视角战斗结算 UI 同族空指针
用法: python disasm_gui12_crash3.py
"""
import struct, re
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

EXE = r"D:\vcmi-fork-build\bin\VCMI_client.exe"
FN_START = 0x20bf60
CRASH = 0x20c09f

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

# ---- .pdata 函数边界 ----
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

fs, fe = fn_of(CRASH)
print('function bounds: +0x%x .. +0x%x  (size=0x%x)  crash=+0x%x (fn+0x%x)'
      % (fs, fe, fe - fs, CRASH, CRASH - fs))

# ---- 反汇编崩点前后窗口 (对齐扫描) ----
WIN_LO, WIN_HI = CRASH - 0x120, CRASH + 0x60
o = rva2off(WIN_LO)
pe.seek(o)
code = pe.read(WIN_HI - WIN_LO + 0x30)
md = Cs(CS_ARCH_X86, CS_MODE_64)
md.detail = False
best = None
for back in range(0x20, 0x08, -1):
    start = WIN_LO + back
    o = rva2off(start)
    pe.seek(o)
    code = pe.read(WIN_HI - start + 0x20)
    ins_list = list(md.disasm(code, imgbase + start))
    if any(ins.address - imgbase == CRASH for ins in ins_list):
        best = ins_list
        break
for ins in best or []:
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
        t2 = int(ins.op_str, 16) - imgbase
        extra = ' ; ->+0x%x' % t2
        s2 = cstr_at(t2)
        if s2:
            extra += ' "%s"' % s2[:70]
    mark = ''
    if rva == CRASH:
        mark = '   <<< CRASH (rax=0, rdx=r8=-4 SPECTATOR)'
    print('  +0x%05x  %-8s %-38s%s%s' % (rva, ins.mnemonic, ins.op_str, extra, mark))
