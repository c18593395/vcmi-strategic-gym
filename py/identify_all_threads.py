# -*- coding: utf-8 -*-
# 批量: 所有线程栈 -> VCMI_client/VCMI_lib/ModelAI 帧全量解析 (pdata 归属) -> 线程身份表
import struct, bisect, re, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

DUMP = sys.argv[1] if len(sys.argv) > 1 else r"D:\Bigdata\hero3_fresh\gui_stuck4_0909.dmp"
f = open(DUMP, "rb")
d = f.read(32)
num_streams, dir_rva = struct.unpack_from("<II", d, 8)
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

from minidump.minidumpfile import MinidumpFile
mf = MinidumpFile.parse(DUMP)
mods = []
for m in mf.modules.modules:
    mods.append((str(m.name).split("\\")[-1], m.baseaddress, m.size))
def mod_of(va):
    for name, base, size in mods:
        if base <= va < base + size:
            return name, va - base
    return None, None

# .pdata + 函数名启发: exe 与 lib
def load_pdata(path):
    try:
        pe = open(path, "rb")
    except Exception:
        return []
    dd = pe.read(0x400)
    p = struct.unpack_from("<I", dd, 0x3C)[0]
    pe.seek(p); pehdr = pe.read(0x18)
    nsec = struct.unpack_from("<H", pehdr, 6)[0]
    optsize = struct.unpack_from("<H", pehdr, 20)[0]
    pe.read(optsize)
    secs = []
    for i in range(nsec):
        s = pe.read(40)
        nm = s[:8].rstrip(b"\x00").decode(errors="replace")
        vsize, vaddr, rsize, raddr = struct.unpack("<IIII", s[8:24])
        secs.append((nm, vaddr, max(vsize, rsize), raddr))
    out = []
    for nm, vaddr, size, raddr in secs:
        if nm == ".pdata":
            pe.seek(raddr)
            blob = pe.read(size)
            for i in range(0, len(blob) - 12, 12):
                beg, end, unw = struct.unpack_from("<III", blob, i)
                if beg:
                    out.append((beg, end))
    pe.close()
    out.sort()
    return out

exe_funcs = load_pdata(r"D:\vcmi-fork-build\bin\VCMI_client.exe")
lib_funcs = load_pdata(r"D:\vcmi-fork-build\bin\VCMI_lib.dll")

def fn_of(modname, rva, funcs):
    if not funcs:
        return "no-pdata"
    fb = [x[0] for x in funcs]
    i = bisect.bisect_right(fb, rva) - 1
    if i >= 0:
        b, e = funcs[i]
        return "fn[0x%x)" % b
    return "??0x%x" % rva

md = Cs(CS_ARCH_X86, CS_MODE_64)
exe_path = r"D:\vcmi-fork-build\bin\VCMI_client.exe"
pe = open(exe_path, "rb")
dd = pe.read(0x400)
p = struct.unpack_from("<I", dd, 0x3C)[0]
pe.seek(p); pehdr = pe.read(0x18)
nsec = struct.unpack_from("<H", pehdr, 6)[0]
optsize = struct.unpack_from("<H", pehdr, 20)[0]
opt = pe.read(optsize)
imgbase = struct.unpack_from("<Q", opt, 24)[0]
psecs = []
for i in range(nsec):
    s = pe.read(40)
    vsize, vaddr, rsize, raddr = struct.unpack("<IIII", s[8:24])
    psecs.append((vaddr, max(vsize, rsize), raddr))
def rva2off(rva):
    for vaddr, size, raddr in psecs:
        if vaddr <= rva < vaddr + size:
            return raddr + (rva - vaddr)
    return None

def exe_call_targets(func_beg, size=0x90):
    off = rva2off(func_beg)
    if off is None:
        return []
    pe.seek(off)
    code = pe.read(size)
    tgts = []
    for ins in md.disasm(code, imgbase + func_beg):
        m = re.search(r"rip\s*([+-])\s*(0x[0-9a-f]+|\d+)", ins.op_str)
        if m:
            sign = 1 if m.group(1) == "+" else -1
            h = m.group(2)
            disp = sign * (int(h, 16) if h.startswith("0x") else int(h))
            tgts.append(ins.address + ins.size + disp - imgbase)
        elif ins.mnemonic in ("call", "jmp") and ins.op_str.startswith("0x"):
            tgts.append(int(ins.op_str, 16) - imgbase)
        if ins.mnemonic == "ret":
            break
    return tgts

KNOWN_EXE = {
    0x2aaf20: "preprocessEvent(SDL事件switch,USEREVENT分支锁interfaceMutex)",
    0x2abe50: "fetchEvents(SDL_PollEvent循环)",
    0x1c3a80: "onPacketReceived(锁interfaceMutex+retrievePack)",
    0x1c4930: "netThreadWrapper?->onPacketReceived",
    0x2007c0: "threadRunLocalServer lambda _M_run(setThreadName runServer->prepare->promise->server->run)",
    0x78cab0: "std::thread _M_start/execute",
    0x78ec20: "std::thread _Invoke thunk",
    0x78ec60: "std::thread _Invoke thunk2",
}

print("=" * 100)
for t in mf.threads.threads:
    tid = t.ThreadId
    lc = t.ThreadContext
    f.seek(lc.Rva)
    ctx = f.read(lc.DataSize)
    rsp = struct.unpack_from("<Q", ctx, 0x98)[0]
    rip = struct.unpack_from("<Q", ctx, 0xF8)[0]
    stack = read_mem(rsp, 0x6000)
    frames = []
    seen = set()
    for off in range(0, max(0, len(stack) - 8), 8):
        va = struct.unpack_from("<Q", stack, off)[0]
        mname, rva = mod_of(va)
        if mname in ("VCMI_client.exe", "VCMI_lib.dll", "ModelAI.dll", "onnxruntime.dll") and rva > 0x1000:
            key = (mname, rva)
            if key in seen:
                continue
            seen.add(key)
            if len(frames) < 14:
                frames.append("%s!%s" % (mname, fn_of(mname, rva, exe_funcs if mname == "VCMI_client.exe" else lib_funcs if mname == "VCMI_lib.dll" else None)))
    if frames:
        print("TID=%-6d %s" % (tid, " | ".join(frames)))
