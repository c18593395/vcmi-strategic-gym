# -*- coding: utf-8 -*-
# gui_stuck4 死锁分析: IAT 解析 + 主线程等待点反汇编 (两阶段, 带进度)
import struct, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

DUMP = r"D:\Bigdata\hero3_fresh\gui_stuck4_0909.dmp"
EXE = r"D:\vcmi-fork-build\bin\VCMI_client.exe"
OUT = r"D:\Bigdata\hero3_fresh\py\stuck4_analysis.txt"

out = open(OUT, "w", encoding="utf-8")
def P(s):
    out.write(s + "\n"); out.flush()

# ---- PE ----
pe = open(EXE, "rb")
dd = pe.read(0x400)
p = struct.unpack_from("<I", dd, 0x3C)[0]
pe.seek(p); pehdr = pe.read(0x18)
nsec = struct.unpack_from("<H", pehdr, 6)[0]
optsize = struct.unpack_from("<H", pehdr, 20)[0]
opt = pe.read(optsize)
imgbase = struct.unpack_from("<Q", opt, 24)[0]
imp_rva, imp_sz = struct.unpack_from("<II", opt, 120)
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

P("[1] building IAT...")
iat = {}
P("[1] IAT SKIPPED (hang workaround), rip-rel targets printed raw")

md = Cs(CS_ARCH_X86, CS_MODE_64)

def disasm_fn(rva, size, label):
    o = rva2off(rva)
    if o is None:
        P("  rva 0x%x not mapped" % rva); return
    pe.seek(o)
    code = pe.read(size)
    P("--- %s: exe!fn[0x%x) ---" % (label, rva))
    n = 0
    for ins in md.disasm(code, imgbase + rva):
        line = "  +0x%04x: %-8s %s" % (ins.address - imgbase, ins.mnemonic, ins.op_str)
        m = ins.op_str
        if "rip +" in m or "rip - " in m:
            mm = __import__("re").search(r"rip ([+-]) (0x[0-9a-f]+)", m)
            if mm:
                d = int(mm.group(2), 16) * (1 if mm.group(1) == "+" else -1)
                tgt = ins.address + ins.size + d
                line += "   ; -> exe+0x%x (VA 0x%x)" % (tgt - imgbase, tgt)
        elif ins.mnemonic in ("call", "jmp") and ins.op_str.startswith("0x"):
            t = int(ins.op_str, 16)
            line += "   ; exe+0x%x" % (t - imgbase) if t >= imgbase else "   ; abs 0x%x" % t
        P(line)
        n += 1
        if n > 60:
            P("  ...(truncated)")
            break
        if ins.mnemonic == "ret":
            break

P("[2] disasm main-thread wait fn")
disasm_fn(0x1a3a70, 0x100, "主线程 fetchEvents 内等待点")
disasm_fn(0x1a3ca0, 0x80, "主线程外层调用者")
P("[done]")
out.close()
pe.close()
print("written to", OUT)
