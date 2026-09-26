# -*- coding: utf-8 -*-
"""解析 minidump exception stream: 拿异常地址 + 模块映射, 定位 RVA。"""
import struct
import sys

DMP = r'C:\Users\Administrator\Documents\My Games\vcmi\logs\VCMI_client.exe_crashinfo.dmp'

data = open(DMP, 'rb').read()
sig, ver, n_streams, dir_rva, checksum, ts, flags = struct.unpack_from('<IIIIIIQ', data, 0)
assert sig == 0x504D444D, hex(sig)  # 'MDMP'
print(f'streams={n_streams}')

streams = {}
for i in range(n_streams):
    st, size, rva = struct.unpack_from('<III', data, dir_rva + 12 * i)
    streams.setdefault(st, []).append((size, rva))

# ExceptionStream = 6
exc_size, exc_rva = streams[6][0]
# MINIDUMP_EXCEPTION_STREAM: ThreadId(4) __alignment(4) ExceptionRecord MINIDUMP_EXCEPTION(152) ThreadContext MINIDUMP_LOCATION_DESCRIPTOR(8)
tid = struct.unpack_from('<I', data, exc_rva)[0]
code, exc_flags, rec, addr = struct.unpack_from('<IIQQ', data, exc_rva + 8)
n_params = struct.unpack_from('<I', data, exc_rva + 8 + 24)[0]
print(f'crash thread={tid} code={code:#x} address={addr:#x} params={n_params}')
for i in range(min(n_params, 4)):
    p = struct.unpack_from('<Q', data, exc_rva + 8 + 32 + 8 * i)[0]
    print(f'  param[{i}]={p:#x}')

# ModuleListStream = 4: count + MINIDUMP_MODULE[n](108 bytes each)
mod_size, mod_rva = streams[4][0]
n_mod = struct.unpack_from('<I', data, mod_rva)[0]
print(f'modules={n_mod}')
target = None
for i in range(n_mod):
    base = mod_rva + 4 + 108 * i
    base_addr, size_of_img, checksum2, ts2, name_rva = struct.unpack_from('<QIIII', data, base)
    name_len = struct.unpack_from('<I', data, name_rva)[0]
    name = data[name_rva + 4:name_rva + 4 + name_len].decode('utf-16-le', errors='replace')
    if base_addr <= addr < base_addr + size_of_img:
        target = (name, base_addr, size_of_img)
        print(f'CRASH MODULE: {name} base={base_addr:#x} size={size_of_img:#x}')
    else:
        short = name.split('\\')[-1]
        if any(k in short.lower() for k in ('vcmi', 'client')):
            print(f'  module: {short} base={base_addr:#x} size={size_of_img:#x}')

if target:
    name, b, s = target
    print(f'\n==> crash RVA in {name.split(chr(92))[-1]} = {addr - b:#x}')
