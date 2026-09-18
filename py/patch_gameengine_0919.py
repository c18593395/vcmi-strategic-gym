#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""09-19 WSL 重建补丁：GameEngine.cpp 死锁诊断打点跨平台化。

09-10 的 LoggingMutex 打点用了 Win32 GetCurrentThreadId，Linux 编译不过。
方案：包一层 _dbg_tid()，Win 下走原 API，Linux 下走 syscall(SYS_gettid)。幂等可重放。
"""
F = "/home/administrator/vcmi-native/client/GameEngine.cpp"

s = open(F).read()

helper = '''#ifdef _WIN32
static inline unsigned long _dbg_tid() { return GetCurrentThreadId(); }
#else
#include <sys/syscall.h>
#include <unistd.h>
static inline unsigned long _dbg_tid() { return (unsigned long)syscall(SYS_gettid); }
#endif
'''

if '_dbg_tid' in s:
    print('已应用过，跳过')
    raise SystemExit(0)

if 'GetCurrentThreadId' not in s:
    print('未发现 GetCurrentThreadId，文件已无 Windows API，跳过')
    raise SystemExit(0)

# 1) 注入 helper（锚定 LoggingMutex::lock 前的注释块尾部）
anchor = 'void GameEngine::LoggingMutex::lock()'
assert anchor in s, '未找到 LoggingMutex::lock'
s = s.replace(anchor, helper + '\n' + anchor, 1)

# 2) 替换全部调用点
n = s.count('GetCurrentThreadId()')
s = s.replace('GetCurrentThreadId()', '_dbg_tid()')
# helper 内的定义行也被替换了，需复原
s = s.replace('static inline unsigned long _dbg_tid() { return _dbg_tid(); }',
              'static inline unsigned long _dbg_tid() { return GetCurrentThreadId(); }')

open(F, 'w').write(s)
print(f'补丁应用成功: helper 注入 + {n} 处调用点替换')
