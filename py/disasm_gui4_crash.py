# -*- coding: utf-8 -*-
"""gui4 崩溃点反汇编: VCMI_client.exe+0x59f66 (0xC0000005 空指针读)
带 rip-relative 目标解析 + 字符串引用识别
"""
import struct, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

EXE = r"D:\vcmi-fork-build\bin\VCMI_client.exe"
CRASH_RVA = 0x59F66

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
    secs.append((vaddr, max(vsize, rsize), raddr, s[:8].decode('ascii', 'replace').rstrip('\x00')))

def rva2off(rva):
    for vaddr, size, raddr, _n in secs:
        if vaddr <= rva < vaddr + size:
            return raddr + (rva - vaddr)
    return None

def read_rva(rva, size):
    o = rva2off(rva)
    if o is None:
        return b''
    pe.seek(o)
    return pe.read(size)

def cstr_at(rva, maxlen=90):
    o = rva2off(rva)
    if o is None:
        return None
    pe.seek(o)
    raw = pe.read(maxlen)
    # utf-8 then latin fallback
    s = raw.split(b'\x00')[0]
    try:
        t = s.decode('utf-8')
    except UnicodeDecodeError:
        t = s.decode('latin1', 'replace')
    return t if t else None

md = Cs(CS_ARCH_X86, CS_MODE_64)
md.detail = True

START = CRASH_RVA - 0x120
code = read_rva(START, 0x180)
print("=== disasm exe+0x%x .. (crash at exe+0x%x) imgbase=0x%x ===" % (START, CRASH_RVA, imgbase))
for ins in md.disasm(code, imgbase + START):
    rva = ins.address - imgbase
    mark = ' >>> CRASH' if rva == CRASH_RVA else ''
    extra = ''
    # rip-relative 注释
    if ins.mnemonic in ('lea', 'mov', 'cmp', 'call', 'jmp') and 'rip' in ins.op_str:
        # 计算目标: capstone detail
        for op in ins.operands:
            if op.type == 3:  # MEM
                if op.mem.base == 41:  # X86_REG_RIP? capstone x86 RIP = 41? 实际用 detail 常量
                    pass
        # 简化: 手动解析 "rip + 0x..." / "rip - 0x..."
        txt = ins.op_str
        import re
        m = re.search(r'\[rip ([+-]) (0x[0-9a-f]+)\]', txt)
        if m:
            delta = int(m.group(2), 16) * (1 if m.group(1) == '+' else -1)
            target = ins.address + ins.size + delta - imgbase
            s = cstr_at(target)
            extra = ' ; ->exe+0x%x' % target
            if s and any(c.isprintable() for c in s[:4]) and sum(c.isprintable() for c in s) > len(s) * 0.8:
                extra += ' "%s"' % s[:80]
    print("  exe+0x%05x  %-8s %-42s%s" % (rva, ins.mnemonic, ins.op_str, extra))
    if rva >= CRASH_RVA + 0x20:
        break
