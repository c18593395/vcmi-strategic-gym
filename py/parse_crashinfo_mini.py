# -*- coding: utf-8 -*-
"""解析 VCMI 官方 crashinfo.dmp (mini dump): Exception 流 + MemoryList 栈回溯
用法: python parse_crashinfo_mini.py <dump.dmp>
"""
import sys, struct

path = sys.argv[1]
f = open(path, 'rb')

# ---- 目录 ----
f.seek(0)
hdr = f.read(32)
num_streams, dir_rva = struct.unpack_from('<II', hdr, 8)
streams = {}
for i in range(num_streams):
    f.seek(dir_rva + i * 12)
    st, sz, rva = struct.unpack('<III', f.read(12))
    if st != 0:
        streams[st] = (sz, rva)

# ---- 模块表 ----
mods = []
sz, rva = streams[4]
f.seek(rva)
n = struct.unpack('<I', f.read(4))[0]
for i in range(n):
    e = f.read(108)  # MINIDUMP_MODULE
    base, msize, cksum, ts, name_rva = struct.unpack('<QIIII', e[:24])
    pos = f.tell()
    f.seek(name_rva)
    ln = struct.unpack('<I', f.read(4))[0]
    name = f.read(ln * 2).decode('utf-16-le', 'replace')
    mods.append((base, msize, name.replace('\\', '/').split('/')[-1]))
    f.seek(pos)
mods.sort()

def sym(addr):
    for base, msize, name in mods:
        if base <= addr < base + msize:
            return '%s+0x%x' % (name, addr - base)
    return '0x%x' % addr

# ---- Exception 流 (MINIDUMP_EXCEPTION_STREAM) ----
esz,erva = streams[6]
f.seek(erva)
tid, align = struct.unpack('<II', f.read(8))
exc = f.read(152)
code, flags, inner, addr_ex, nparams, _u = struct.unpack('<IIQQII', exc[:32])
exinfo = struct.unpack('<15Q', exc[32:152])
ctx_sz, ctx_rva = struct.unpack('<II', f.read(8))
f.seek(ctx_rva)
ctx = f.read(ctx_sz)

def q(off):
    return struct.unpack_from('<Q', ctx, off)[0]

print('=== Exception ===')
print('TID=%d code=0x%08X addr=0x%x (%s)' % (tid, code, addr_ex, sym(addr_ex)))
print('Parameters:', exinfo[:nparams])
print('Rax=0x%x Rcx=0x%x Rdx=0x%x Rbx=0x%x' % (q(0x78), q(0x80), q(0x88), q(0x90)))
print('Rsp=0x%x Rbp=0x%x Rsi=0x%x Rdi=0x%x' % (q(0x98), q(0xA0), q(0xA8), q(0xB0)))
print('R8 =0x%x R9 =0x%x R10=0x%x R11=0x%x' % (q(0xB8), q(0xC0), q(0xC8), q(0xD0)))
print('Rip=0x%x (%s)' % (q(0xF8), sym(q(0xF8))))

# ---- MemoryList ----
msz, mrva = streams[5]
f.seek(mrva)
n = struct.unpack('<I', f.read(4))[0]
mem = []
for i in range(n):
    start, dsz, drva = struct.unpack('<QQI', f.read(20))
    mem.append((start, dsz, drva))

def read_mem(a, s):
    for start, dsz, drva in mem:
        if start <= a < start + dsz:
            off = a - start
            f.seek(drva + off)
            return f.read(min(s, dsz - off))
    return b''

# ---- 栈回溯: 从 RSP 扫描非目录返回地址 (x64 无帧指针) ----
rsp = q(0x98)
stack = read_mem(rsp, 0x4000)
print('\n=== Stack scan from RSP=0x%x (%d bytes in dump) ===' % (rsp, len(stack)))
seen = []
for off in range(0, len(stack) - 8, 8):
    val = struct.unpack_from('<Q', stack, off)[0]
    s = sym(val)
    if '+' in s and not s.startswith('0x'):
        mod = s.split('+')[0]
        if mod not in ('ntdll.dll', 'kernel32.dll', 'kernelbase.dll', 'ucrtbase.dll'):
            seen.append((rsp + off, val, s))
for a, v, s in seen[:30]:
    print('  [rsp+0x%-4x] 0x%x  %s' % (a - rsp, v, s))
