# -*- coding: utf-8 -*-
# MinGW PE 反汇编 + IAT 符号化: 给定 RVA 列表, 反汇编附近代码, call/jmp [rip+X] 解析为 DLL!函数
# 用法: python iat_disasm.py <exe/dll> <rva1> <rva2> ...
import struct, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

def pe_info(path):
    f = open(path, "rb")
    d = f.read(0x400)
    pe = struct.unpack_from("<I", d, 0x3C)[0]
    f.seek(pe)
    pehdr = f.read(0x18)
    nsec = struct.unpack_from("<H", pehdr, 6)[0]
    optsize = struct.unpack_from("<H", pehdr, 20)[0]
    opt = f.read(optsize)
    magic = struct.unpack_from("<H", opt, 0)[0]
    assert magic == 0x20b
    imgbase = struct.unpack_from("<Q", opt, 24)[0]
    ddoff = 112
    imp_rva, imp_size = struct.unpack_from("<II", opt, ddoff + 8)  # import dir
    iat_rva, iat_size = struct.unpack_from("<II", opt, ddoff + 96)  # IAT = DataDirectory[12]
    secs = []
    for i in range(nsec):
        s = f.read(40)
        name = s[:8].rstrip(b"\x00").decode(errors="replace")
        vsize, vaddr, rsize, raddr = struct.unpack("<IIII", s[8:24])
        secs.append((vaddr, max(vsize, rsize), raddr, name))

    def rva2off(rva):
        for vaddr, size, raddr, _ in secs:
            if vaddr <= rva < vaddr + size:
                return raddr + (rva - vaddr)
        return None

    iat_map = {}
    o = rva2off(imp_rva)
    if o:
        while True:
            f.seek(o)
            desc = f.read(20)
            if desc == b"\x00" * 20:
                break
            oft_rva, _, _, name_rva, ftn_rva = struct.unpack("<IIIII", desc)
            no = rva2off(name_rva)
            f.seek(no)
            dllname = f.read(64).split(b"\x00")[0].decode(errors="replace")
            # 走 FirstThunk (IAT)
            to = rva2off(ftn_rva)
            idx = 0
            while True:
                f.seek(to + idx * 8)
                val = struct.unpack("<Q", f.read(8))[0]
                if val == 0:
                    break
                ho = rva2off(oft_rva + idx * 8) if oft_rva else rva2off(ftn_rva + idx * 8)
                f.seek(ho)
                hint = struct.unpack_from("<H", f.read(2), 0)[0]
                fname = f.read(128).split(b"\x00")[0].decode(errors="replace")
                iat_map[ftn_rva + idx * 8] = "%s!%s" % (dllname, fname)
                idx += 1
            o += 20
    return f, imgbase, secs, iat_map

def main():
    path = sys.argv[1]
    rvas = [int(x, 16) if x.startswith("0x") else int(x) for x in sys.argv[2:]]
    f, imgbase, secs, iat_map = pe_info(path)
    md = Cs(CS_ARCH_X86, CS_MODE_64)

    def rva2off(rva):
        for vaddr, size, raddr, _ in secs:
            if vaddr <= rva < vaddr + size:
                return raddr + (rva - vaddr)
        return None

    for rva in rvas:
        start = rva - 0x60
        size = 0xB0
        off = rva2off(start)
        f.seek(off)
        code = f.read(size)
        print("==== %s RVA 0x%x (base 0x%x, VA 0x%x)" % (path.split("\\")[-1], rva, imgbase, imgbase + rva))
        for ins in md.disasm(code, imgbase + start):
            marker = " >>>" if abs((ins.address - imgbase) - rva) < 4 else "    "
            note = ""
            # rip 相对内存操作数解析
            if "[" in ins.op_str and "rip" in ins.op_str:
                try:
                    disp = int(ins.op_str.split("rip")[1].split("]")[0].replace(" + ", "+").replace(" - ", "-").replace("+", "").replace("-", "-") or "0", 16)
                except Exception:
                    disp = None
                # capstone op_str 形如 [rip + 0x1234] 或 [rip - 0x10]
                import re
                m = re.search(r"rip\s*([+-])\s*(0x[0-9a-f]+|\d+)", ins.op_str)
                if m:
                    sign = 1 if m.group(1) == "+" else -1
                    disp = sign * int(m.group(2), 16) if m.group(2).startswith("0x") else sign * int(m.group(2))
                    tgt = ins.address + ins.size + disp
                    if tgt in iat_map:
                        note = "   ; -> " + iat_map[tgt]
                    else:
                        note = "   ; -> 0x%x (data?)" % tgt
            elif ins.mnemonic in ("call", "jmp") and ins.op_str.startswith("0x"):
                tva = int(ins.op_str, 16)
                note = "   ; -> RVA 0x%x" % (tva - imgbase)
            print("%s 0x%08x  %-8s %-40s%s" % (marker, ins.address - imgbase, ins.mnemonic, ins.op_str, note))
        print()

if __name__ == "__main__":
    main()
