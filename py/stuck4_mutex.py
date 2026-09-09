# -*- coding: utf-8 -*-
# gui_stuck4: 反汇编锁函数 + 从 dump 读 mutex 内存找 owner
import struct, bisect

DUMP = r"D:\Bigdata\hero3_fresh\gui_stuck4_0909.dmp"
EXE = r"D:\vcmi-fork-build\bin\VCMI_client.exe"

f = open(DUMP, "rb")
hdr = f.read(32)
num_streams, dir_rva = struct.unpack_from("<II", hdr, 8)
mem64 = []
for i in range(num_streams):
    f.seek(dir_rva + i * 12)
    st, sz, rva = struct.unpack("<III", f.read(12))
    if st == 9:
        f.seek(rva)
        n_ranges, base_rva = struct.unpack("<QQ", f.read(16))
        data_rva = base_rva
        for j in range(n_ranges):
            start, dsize = struct.unpack("<QQ", f.read(16))
            mem64.append((start, dsize, data_rva))
            data_rva += dsize
        break
mem64.sort()
starts = [m[0] for m in mem64]

def read_mem(addr, size):
    out = b""
    idx = bisect.bisect_right(starts, addr) - 1
    while len(out) < size and idx < len(mem64):
        start, dsize, rva = mem64[idx]
        if addr + len(out) < start:
            break
        off = (addr + len(out)) - start
        if off >= dsize:
            idx += 1
            continue
        n = min(size - len(out), dsize - off)
        f.seek(rva + off)
        out += f.read(n)
        idx += 1
    return out

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

print("=== exe+0x6cef50 (锁获取函数) ===")
o = rva2off(0x6cef50)
pe.seek(o)
code = pe.read(0x60)
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
md = Cs(CS_ARCH_X86, CS_MODE_64)
import re
for ins in md.disasm(code, imgbase + 0x6cef50):
    line = "  +0x%05x: %-8s %s" % (ins.address - imgbase, ins.mnemonic, ins.op_str)
    mm = re.search(r"rip ([+-]) (0x[0-9a-f]+)", ins.op_str)
    if mm:
        d = int(mm.group(2), 16) * (1 if mm.group(1) == "+" else -1)
        tgt = ins.address + ins.size + d
        line += "   ; exe+0x%x" % (tgt - imgbase)
    elif ins.mnemonic in ("call", "jmp") and ins.op_str.startswith("0x"):
        line += "   ; exe+0x%x" % (int(ins.op_str, 16) - imgbase)
    print(line)
    if ins.mnemonic == "ret":
        break

# ---- 实际模块基址 (ASLR) ----
from minidump.minidumpfile import MinidumpFile
mf = MinidumpFile.parse(DUMP)
mods = []
for m in mf.modules.modules:
    mods.append((str(m.name).split("\\")[-1], m.baseaddress, m.size))
exe_base = None
for name, base, size in mods:
    if name == "VCMI_client.exe":
        exe_base = base
print("\nexe actual base = 0x%x (PE preferred 0x%x)" % (exe_base, imgbase))

def mod_of(va):
    for name, base, size in mods:
        if base <= va < base + size:
            return name, va - base
    return "??", 0

# IAT thunk: jmp [exe+0xa9e770] -> 读该地址存的函数 VA
for thunk_rva in (0xa9e770,):
    iat_slot = read_mem(exe_base + thunk_rva, 8)
    if iat_slot:
        fn_va = struct.unpack("<Q", iat_slot)[0]
        mname, mrva = mod_of(fn_va)
        print("IAT exe+0x%x -> 0x%x = %s+0x%x" % (thunk_rva, fn_va, mname, mrva))

# GAME 全局指针 VA = exe_base + 0xa879b0
game_ptr_va = exe_base + 0xa879b0
buf = read_mem(game_ptr_va, 8)
if not buf:
    print("read GAME ptr failed")
    raise SystemExit
game = struct.unpack("<Q", buf)[0]
gm, grva = mod_of(game)
print("[GAME] ptr@exe+0xa879b0 -> 0x%x (%s+0x%x)" % (game, gm, grva))

if game:
    mutex_va = game + 0x98
    mb = read_mem(mutex_va, 0x60)
    print("[GAME+0x98] mutex raw @0x%x:" % mutex_va)
    for i in range(0, min(len(mb), 0x40), 8):
        print("  +0x%02x: 0x%016x" % (i, struct.unpack_from("<Q", mb, i)[0]))
    # CRITICAL_SECTION 布局: DebugInfo(8) LockCount(4) RecursionCount(4) OwningThread(8) LockSemaphore(8) SpinCount(8)
    if len(mb) >= 0x20:
        dbg, lockcnt, reccnt, owner, sema, spin = struct.unpack_from("<QIIQQQ", mb, 0)
        print("\n  解析为 CRITICAL_SECTION:")
        print("    LockCount=%d(0x%x) RecursionCount=%d OwningThread=0x%x SpinCount=%d" % (
            lockcnt - (-2**31 if lockcnt >= 2**31 else 0) if False else lockcnt, lockcnt, reccnt, owner, spin))
        print("    (OwningThread 为 handle 值; 0=未持有)")
