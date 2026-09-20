#!/usr/bin/env python3
"""_fix_vmap2h3m_strip_comments.py — vmap2h3m.py 读 vmap 时未处理 // 注释导致 JSONDecodeError (#294)

VCMI saveMap 输出的 vmap zip 里 JSON 带 `// game` 行注释, vmap2h3m.py 的 read_vmap
直接 json.loads 必炸。h3m2vmap.py 已有 _loads_permissive (容错 json.loads), 本 patch 把
同一套 (注释剥离 + 容错 loads) 引入 vmap2h3m.py 并替换 read_vmap 里的 3 处 json.loads。

锚点: read_vmap 函数原文 (L154-162)。
幂等: 已含 `_strip_json_comments` 则跳过。
"""
import re
import sys

TARGET = r"D:\Bigdata\hero3_fresh\py\vmap2h3m.py"

OLD_READVMAP = """def read_vmap(path):
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        header = json.loads(z.read('header.json'))
        tfiles = sorted(n for n in names if n.endswith('_terrain.json'))
        terrains = [json.loads(z.read(n)) for n in tfiles]
        objs_raw = json.loads(z.read('objects.json'))
    objects = list(objs_raw.values()) if isinstance(objs_raw, dict) else objs_raw
    return header, terrains, objects"""

NEW_HELPERS = """def strip_json_comments(text):
    \"\"\"VCMI saveMap 输出 JSON 带 `// game` 行注释, 非合法 JSON; 逐行剥离 (字符串内 // 保留)\"\"\"
    out = []
    for line in text.split('\\n'):
        i, in_str, buf = 0, False, []
        while i < len(line):
            ch = line[i]
            if ch == '"' and (i == 0 or line[i - 1] != '\\\\'):
                in_str = not in_str
            if not in_str and ch == '/' and i + 1 < len(line) and line[i + 1] == '/':
                break
            buf.append(ch)
            i += 1
        out.append(''.join(buf))
    return '\\n'.join(out)


def _loads_permissive(s):
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return json.loads(strip_json_comments(s))


def read_vmap(path):
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        header = _loads_permissive(z.read('header.json').decode())
        tfiles = sorted(n for n in names if n.endswith('_terrain.json'))
        terrains = [_loads_permissive(z.read(n).decode()) for n in tfiles]
        objs_raw = _loads_permissive(z.read('objects.json').decode())
    objects = list(objs_raw.values()) if isinstance(objs_raw, dict) else objs_raw
    return header, terrains, objects"""


def main():
    src = open(TARGET, encoding='utf-8').read()
    if '_strip_json_comments' in src:
        print('skip: already patched')
        return 0
    if 'def strip_json_comments(text):' in src:
        print('ERROR: 已有 strip_json_comments (非本 patch 版本?), 手动检查', file=sys.stderr)
        return 2
    assert OLD_READVMAP in src, 'anchor read_vmap not found'
    src = src.replace(OLD_READVMAP, NEW_HELPERS, 1)
    open(TARGET, 'w', encoding='utf-8').write(src)
    print('patched: read_vmap + _strip_json_comments/_loads_permissive')
    # 语法自检
    import py_compile
    py_compile.compile(TARGET, doraise=True)
    print('py_compile OK')
    return 0


if __name__ == '__main__':
    sys.exit(main())
