#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""09-19 WSL 重建补丁：VCMIDirsXDG 补 libraryName/libraryPath 实现（D 盘副本缺原 WSL 本地补丁）。

口径与 VCMIDirsWIN32 一致（ML 便携模式，均返回 "." / lib<basename>.so）。
幂等可重放。
"""
F = "/home/administrator/vcmi-native/lib/VCMIDirs.cpp"

s = open(F).read()
name_impl = 'std::string libraryName(const std::string & basename) const override { return "lib" + basename + ".so"; }'
path_impl = 'bfs::path libraryPath() const override { return "."; }'

i = s.find('class VCMIDirsXDG')
assert i >= 0, '未找到 VCMIDirsXDG 类定义'
seg_end = s.find('};', i)
assert seg_end > i, 'VCMIDirsXDG 类体未闭合'
seg = s[i:seg_end]

changed = []
if name_impl not in seg:
    j = seg.find('binaryPath() const override;')
    assert j >= 0, 'VCMIDirsXDG 类内未找到 binaryPath 声明'
    k = s.find('\n', i + j)
    s = s[:k + 1] + '    ' + name_impl + '\n' + s[k + 1:]
    changed.append('libraryName')

if path_impl not in s[i:seg_end + 200]:
    # 重定位（插入后偏移变化）
    i = s.find('class VCMIDirsXDG')
    seg_end = s.find('};', i)
    seg = s[i:seg_end]
    j = seg.find('binaryPath() const override;')
    k = s.find('\n', i + j)
    s = s[:k + 1] + '    ' + path_impl + '\n' + s[k + 1:]
    changed.append('libraryPath')

if changed:
    open(F, 'w').write(s)
    print('补丁应用成功:', ' + '.join(changed))
else:
    print('已应用过，跳过')
