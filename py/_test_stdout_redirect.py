#!/usr/bin/env python3
# 验证 stdout 重定向可行性 (2026-09-23): 继承 fd 1 + 行缓冲, C++ 写 stdout 不崩
import sys, os
f = open('/tmp/_fd_test.log', 'w')
d = f.fileno()
sys.stdout = os.fdopen(d, 'w', buffering=1)
print('TEST: python print 走 fd %d' % d, flush=True)
print('TEST: 中文 你好', flush=True)
os.write(d, b'TEST: raw write via os.write\n')
sys.stdout.flush()
f.close()
os._exit(0)
