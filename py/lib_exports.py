# -*- coding: utf-8 -*-
# VCMI_lib.dll: 导出表 + .pdata 归属栈 RVA -> 函数
import struct, bisect, sys

path = r"D:\vcmi-fork-build\bin\VCMI_lib.dll"
f = open(path, "rb")
d = f.read(0x400)
pe = struct.unpack_from("<I", d, 0x3C)[0]
f.seek(pe); pehdr = f.read(0x18)
nsec = struct.unpack_from("<H", pehdr, 6)[0]
optsize = struct.unpack_from("<H", pehdr, 20)[0]
opt = f.read(optsize)
ddoff = 112
exp_rva, exp_size = struct.unpack_from("<II", opt, ddoff)
pdata_rva, pdata_size = struct.unpack_from("<II", opt, ddoff + 12 * 8)
secs = []
for i in range(nsec):
    s = f.read(40)
    nm = s[:8].rstrip(b"\x00").decode(errors="replace")
    vsize, vaddr, rsize, raddr = struct.unpack("<IIII", s[8:24])
    secs.append((nm, vaddr, max(vsize, rsize), raddr))

def rva2off(rva):
    for nm, vaddr, size, raddr in secs:
        if vaddr <= rva < vaddr + size:
            return raddr + (rva - vaddr)
    return None

# 导出
exports = []
eo = rva2off(exp_rva)
if eo:
    f.seek(eo)
    ed = f.read(exp_size)
    nnames = struct.unpack_from("<I", ed, 24)[0]
    nameso = rva2off(struct.unpack_from("<I", ed, 36)[0])
    addrto = rva2off(struct.unpack_from("<I", ed, 40)[0])
    f.seek(nameso); nblob = f.read(nnames * 4)
    f.seek(addrto); ablob = f.read(nnames * 4)
    for i in range(nnames):
        nrva = struct.unpack_from("<I", nblob, i * 4)[0]
        no = rva2off(nrva)
        if no is None:
            continue
        f.seek(no)
        name = f.read(300).split(b"\x00")[0].decode(errors="replace")
        rva = struct.unpack_from("<I", ablob, i * 4)[0]
        exports.append((rva, name))
    exports.sort()
    print("exports: %d" % len(exports))

# pdata (按节名找, x64 .pdata 不在 DataDirectory)
po = None
pdata_size = 0
for nm, vaddr, size, raddr in secs:
    if nm == ".pdata":
        po = rva2off(vaddr)
        pdata_size = size
if po is None:
    sys.exit("no .pdata")
f.seek(po)
blob = f.read(pdata_size)
funcs = []
for i in range(0, len(blob) - 12, 12):
    beg, end, unw = struct.unpack_from("<III", blob, i)
    if beg == 0:
        continue
    funcs.append((beg, end))
funcs.sort()
fb = [x[0] for x in funcs]
print("funcs: %d" % len(funcs))

def name_of(rva):
    i = bisect.bisect_right([x[0] for x in exports], rva) - 1
    if i >= 0:
        er, en = exports[i]
        if rva - er < 0x4000:
            return en[:100] + " (+0x%x)" % (rva - er)
    j = bisect.bisect_right(fb, rva) - 1
    if j >= 0:
        b, e = funcs[j]
        return "func[0x%x..0x%x)" % (b, e)
    return "??"

for arg in sys.argv[1:]:
    rva = int(arg, 16) if arg.startswith("0x") else int(arg)
    print("0x%x -> %s" % (rva, name_of(rva)))
