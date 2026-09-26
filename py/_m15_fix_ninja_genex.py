# -*- coding: utf-8 -*-
"""M1.5 临时工具2: 移除 build.ninja 中未被 CMake 4.4.2 求值的 $<LINK_ONLY:...> genex。"""
import re
import shutil

P = r'D:\vcmi-fork-build\build.ninja'
shutil.copyfile(P, P + '.bak_0927_m15b')
data = open(P, 'r', encoding='utf-8').read()
found = re.findall(r'\$<LINK_ONLY:[^>]*>', data)
print('genex found:', len(found), sorted(set(found)))
fixed = re.sub(r'\$<LINK_ONLY:[^>]*>', '', data)
open(P, 'w', encoding='utf-8', newline='').write(fixed)
print('fixed, size', len(fixed))
