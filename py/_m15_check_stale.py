# -*- coding: utf-8 -*-
"""M1.5 工具5: Nullkiller2 全量源/obj mtime 比对, 列 stale obj。"""
import os
import glob

SRC_ROOT = r'D:\Bigdata\hero3_fresh\vcmi\AI\Nullkiller2'
OBJ_ROOT = r'D:\vcmi-fork-build\AI\Nullkiller2\CMakeFiles\Nullkiller2.dir'

stale = []
ok = 0
missing = []
for src in glob.glob(SRC_ROOT + '/**/*.cpp', recursive=True):
    rel = os.path.relpath(src, SRC_ROOT)
    obj = os.path.join(OBJ_ROOT, rel.replace('/', os.path.sep)) + '.obj'
    if not os.path.exists(obj):
        missing.append(rel)
        continue
    if os.path.getmtime(obj) < os.path.getmtime(src):
        stale.append((rel, os.path.getmtime(src) - os.path.getmtime(obj)))
    else:
        ok += 1

print(f'ok={ok} stale={len(stale)} missing={len(missing)}')
for rel, dt in sorted(stale, key=lambda a: -a[1]):
    print(f'  STALE {dt:.0f}s: {rel}')
for rel in missing:
    print(f'  MISSING obj: {rel}')
