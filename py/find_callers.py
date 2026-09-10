# -*- coding: utf-8 -*-
"""扫描 .text 中所有 E8 call, 按目标分组, 找崩溃函数(0x59ef0附近)的调用者; 并反汇编候选起点前的边界"""
import struct
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

# .text
tv = ts = tr = None
for vaddr, size, raddr in secs:
    if vaddr <= 0x59F66 < vaddr + size:
        tv, ts, tr = vaddr, size, raddr
        break
pe.seek(tr)
tbytes = pe.read(ts)

# ---- 反汇编崩溃函数候选起点前的 64 字节找边界 (ret/cc/int3) ----
md = Cs(CS_ARCH_X86, CS_MODE_64)
back = 0x100
code = pe.read(0)
o = rva2off(0x59EF0 - back)
pe.seek(o)
code = pe.read(back + 0x10)
print("=== 0x59ef0 前 0x100 字节线性反汇编 (从对齐锚点) ===")
for ins in md.disasm(code, imgbase + 0x59EF0 - back):
    rva = ins.address - imgbase
    tag = ''
    if ins.mnemonic in ('ret', 'jmp', 'int3') or ins.bytes[0] == 0xCC:
        tag = '  <-- boundary?'
    print("  exe+0x%05x  %-8s %s%s" % (rva, ins.mnemonic, ins.op_str, tag))

# ---- 全 .text E8 扫描: 目标落在 [0x59ef0, 0x59ef8] ----
print("\n=== calls into 0x59ef0-0x59ef8 ===")
for i in range(len(tbytes) - 5):
    if tbytes[i] == 0xE8:
        rel = struct.unpack_from('<i', tbytes, i + 1)[0]
        src_rva = tv + i
        tgt = src_rva + 5 + rel
        if 0x59EF0 <= tgt <= 0x59EF8:
            print("  caller exe+0x%x -> exe+0x%x" % (src_rva, tgt))
