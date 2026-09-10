# -*- coding: utf-8 -*-
"""枚举 minidump 流 + 尝试 MemoryListStream(6) 解析崩溃线程栈"""
import sys, struct

path = sys.argv[1]
f = open(path, 'rb')
f.seek(0)
hdr = f.read(32)
num_streams, dir_rva = struct.unpack_from('<II', hdr, 8)
print('streams=%d' % num_streams)

NAMES = {0:'Unused',3:'ThreadList',4:'ModuleList',5:'MemoryList',6:'Exception',7:'SystemInfo',
         8:'ThreadExList',9:'Memory64List',10:'CommentA',11:'CommentW',12:'HandleData',13:'FunctionTable',
         14:'UnloadedModuleList',15:'MiscInfo',16:'MemoryInfoList',17:'ThreadInfoList',18:'HandleOperationList',
         19:'Token',22:'SystemMemoryInfo',23:'ProcessVmCounters'}

streams = {}
for i in range(num_streams):
    f.seek(dir_rva + i * 12)
    st, sz, rva = struct.unpack('<III', f.read(12))
    streams.setdefault(st, []).append((sz, rva))
    print('stream %2d %-18s size=%-9d rva=%d' % (st, NAMES.get(st, '?'), sz, rva))
