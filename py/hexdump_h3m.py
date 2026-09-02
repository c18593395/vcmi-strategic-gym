#!/usr/bin/env python3
"""hexdump h3m 头部 100 字节 + 对照 h3m_tool 布局注释"""
import gzip, sys

raw = gzip.decompress(open(sys.argv[1], 'rb').read())
print("raw len:", len(raw))
for off in range(0, min(96, len(raw)), 16):
    seg = raw[off:off+16]
    hexs = ' '.join(f'{b:02x}' for b in seg)
    asc = ''.join(chr(b) if 32 <= b < 127 else '.' for b in seg)
    print(f"{off:4d}: {hexs:<48s} {asc}")
