#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""09-19 WSL 重建补丁：v13 GLOBAL_ENCODING 补 BATTLE_ROUND 条目。

根因：v13 types.h 的 GlobalAttribute 有 BATTLE_ROUND（11 项，index 1），
但 constants.h 的 GLOBAL_ENCODING 只有 10 条，static_assert（未初始化+乱序）炸。
对应服务器知识库"补 BATTLE_ROUND 到 GLOBAL_ENCODING"历史操作；
写法抄 v14 同位置先例（LE 编码保维度）。幂等可重放。
"""
F = "/home/administrator/vcmi-native/AI/MMAI/schema/v13/constants.h"

s = open(F).read()
if 'X::GA::BATTLE_ROUND' in s:
    print('已应用过，跳过')
    raise SystemExit(0)

i = s.find('E5(X::GA::BATTLE_SIDE, X::CS, 1),')
assert i >= 0, '锚点 BATTLE_SIDE 条目未找到，需人工检查'
ls = s.rfind('\n', 0, i) + 1            # 条目所在行行首
indent = s[ls:i]                        # 前导空白（tab/空格自适应）
k = s.find('\n', i)
line = f"{indent}E5(X::GA::BATTLE_ROUND, X::LE, MAX_ROUNDS + 1),\n"
s = s[:k + 1] + line + s[k + 1:]
open(F, 'w').write(s)
print('补丁应用成功: GLOBAL_ENCODING 补 BATTLE_ROUND (LE, MAX_ROUNDS+1) 于 index 1')
