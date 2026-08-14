#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
冒烟 #16: 双端 schema 对照测试 — C 头 (strategic_state.h) vs Python ctypes (strategic_reader.py)
检测: 字段顺序错位/遗漏/类型不一致 (B 章节审计教训: 手写 schema 双端易错)

用法: python3 _schema_check.py [strategic_state.h 路径]
运行于 Windows (读源文件) 即可, 不需 WSL。
"""
import ctypes
import io
import os
import re
import sys

ROOT = r'D:\Bigdata\hero3_fresh'
H_PATH = os.path.join(ROOT, 'vcmi', 'ML', 'strategic_state.h')
if len(sys.argv) > 1:
    H_PATH = sys.argv[1]

sys.path.insert(0, ROOT)
import strategic_reader as sr

# ============ 解析 C 头 ============
with io.open(H_PATH, encoding='utf-8') as f:
    h = f.read()

def parse_c_struct(name):
    """从 C 头解析 struct name 的字段列表 [(c_name, c_type, array_len)]"""
    m = re.search(r'struct\s+' + name + r'\s*\{', h)
    if not m:
        return None
    depth = 0
    i = h.index('{', m.start())
    for j in range(i, len(h)):
        if h[j] == '{': depth += 1
        elif h[j] == '}':
            depth -= 1
            if depth == 0:
                body = h[i+1:j]
                break
    fields = []
    for line in body.split('\n'):
        line = line.strip()
        # 去掉行内注释
        if '//' in line:
            line = line[:line.index('//')].strip()
        line = line.rstrip(';').strip()
        if not line or line.startswith('//') or line.startswith('/*'):
            continue
        # 匹配: type name; 或 type name[N]; 或 type name[N][M];  (N 可能是宏名)
        m2 = re.match(r'(\w[\w:<>]*)\s+(\w+)((?:\[[^\]]*\])*)$', line)
        if m2:
            ctype, cname, arr = m2.group(1), m2.group(2), m2.group(3)
            arrs = []
            for token in re.findall(r'\[([^\]]*)\]', arr):
                if token.isdigit():
                    arrs.append(int(token))
                else:
                    # 宏名 → 查 #define
                    val = parse_c_define(token)
                    arrs.append(val if val is not None else -1)
            fields.append((cname, ctype, arrs))
    return fields

def parse_c_define(name):
    m = re.search(r'#define\s+' + name + r'\s+(\d+)', h)
    return int(m.group(1)) if m else None

# ============ 解析 Python ctypes ============
def py_type_to_c(py_field_type):
    """ctypes 类型 → C 类型名"""
    t = py_field_type
    arr = []
    while hasattr(t, '_length_'):
        arr.append(t._length_)
        t = t._type_
    if t is ctypes.c_int32:
        base = 'int32_t'
    elif t is ctypes.c_int8:
        base = 'int8_t'
    elif t is ctypes.c_char:
        base = 'char'
    else:
        base = repr(t)
    return base, arr

def py_struct_fields(cls):
    out = []
    for fname, ftype in cls._fields_:
        base, arr = py_type_to_c(ftype)
        out.append((fname, base, arr))
    return out

# ============ 对照 ============
errors = []
for cls_name, struct_name in [
    ('StrategicHero', 'StrategicHero'),
    ('StrategicTown', 'StrategicTown'),
    ('StrategicPlayer', 'StrategicPlayer'),
    ('StrategicMine', 'StrategicMine'),
]:
    c_fields = parse_c_struct(struct_name)
    py_fields = py_struct_fields(getattr(sr, cls_name))
    if c_fields is None:
        errors.append(f"[{struct_name}] C 头未找到")
        continue
    print(f"=== {struct_name}: C {len(c_fields)} 字段 vs Python {len(py_fields)} 字段 ===")
    if len(c_fields) != len(py_fields):
        errors.append(f"[{struct_name}] 字段数不一致: C={len(c_fields)} Python={len(py_fields)}")
    for i, (cf, pf) in enumerate(zip(c_fields, py_fields)):
        cname, ctype, carr = cf
        pname, ptype, parr = pf
        # 类型映射: int32_t→c_int32, int8_t→c_int8, char[N]→c_char*N
        if cname != pname:
            errors.append(f"[{struct_name}] 字段{i} 名不一致: C={cname} Python={pname}")
        if carr != parr:
            errors.append(f"[{struct_name}] 字段{i} {cname} 数组维度不一致: C={carr} Python={parr}")
        if (ctype, len(carr)) == ('char', 1) and ptype == 'char':
            pass  # char[32] 名称字段, 类型对
        elif ctype == 'int32_t' and ptype == 'int32_t':
            pass
        elif ctype == 'int8_t' and ptype == 'int8_t':
            pass
        else:
            errors.append(f"[{struct_name}] 字段{i} {cname} 类型不一致: C={ctype} Python={ptype}")

# StrategicState 主结构
c_state = parse_c_struct('StrategicState')
py_state = py_struct_fields(sr.StrategicState)
print(f"\n=== StrategicState: C {len(c_state)} 字段 vs Python {len(py_state)} 字段 ===")
if len(c_state) != len(py_state):
    errors.append(f"[StrategicState] 字段数不一致: C={len(c_state)} Python={len(py_state)}")
for i, (cf, pf) in enumerate(zip(c_state, py_state)):
    cname, ctype, carr = cf
    pname, ptype, parr = pf
    if cname != pname:
        errors.append(f"[StrategicState] 字段{i} 名不一致: C={cname} Python={pname}")
    if carr != parr:
        errors.append(f"[StrategicState] 字段{i} {cname} 数组维度不一致: C={carr} Python={parr}")

# 常量对照
print("\n=== 常量对照 ===")
for cname, pname in [('MAX_HEROES','MAX_HEROES'), ('MAX_TOWNS','MAX_TOWNS'), ('MAX_PLAYERS','MAX_PLAYERS'),
                     ('MAX_MINES','MAX_MINES'), ('LOCAL_WIN','LOCAL_WIN'), ('LOCAL_CH','LOCAL_CH'),
                     ('GLOBAL_GRID','GLOBAL_GRID'), ('MAX_LEVELS','MAX_LEVELS'),
                     ('NAV_SIZE','NAV_SIZE'), ('TARGET_LIST','TARGET_LIST'), ('TARGET_DIM','TARGET_DIM'),
                     ('ENEMY_THREAT','ENEMY_THREAT'), ('BATTLE_PRED','BATTLE_PRED'),
                     ('EVENTS_SIZE','EVENTS_SIZE'), ('RESERVED_SIZE','RESERVED_SIZE')]:
    cv = parse_c_define(cname)
    pv = getattr(sr, pname, None)
    status = "OK" if cv == pv else f"MISMATCH (C={cv} Python={pv})"
    print(f"  {cname}: {status}")
    if cv != pv:
        errors.append(f"[常量] {cname}: C={cv} Python={pv}")

# OBS_DIM 计算验证
obs_dim = 8 + 8*15 + 8*26 + 8*18 + 3*15*15 + 2*32*32 + 8 + 8 + 32 + 8*8 + 7 + 4 + 4 + 134
print(f"\nOBS_DIM 期望: {obs_dim}, 设计文档: 3464")

print("\n" + "="*50)
if errors:
    print(f"❌ {len(errors)} 处不一致:")
    for e in errors:
        print("  -", e)
    sys.exit(1)
else:
    print("✅ 双端 schema 完全一致")
    sys.exit(0)
