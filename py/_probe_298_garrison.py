#!/usr/bin/env python3
"""#298 驻军假说验证: good_to_go/judgement/elbow 城对象 garrison 字段 vs 课程图蓝城 (09-23 只读)"""
import json, zipfile, re

MAPS = [
    ("good_to_go_h3m.vmap", "/mnt/d/Bigdata/hero3_fresh/maps/training/h3m_pool"),
    ("judgement_day_h3m.vmap", "/mnt/d/Bigdata/hero3_fresh/maps/training/h3m_pool"),
    ("elbow_room_h3m.vmap", "/mnt/d/Bigdata/hero3_fresh/maps/training/h3m_pool"),
    ("a_viking_we_shall_go_h3m.vmap", "/mnt/d/Bigdata/hero3_fresh/maps/training/h3m_pool"),
    ("T05_adventure_52X52_01.vmap", "/mnt/d/Bigdata/hero3_fresh/maps/training"),
]

def loads_permissive(s):
    try:
        return json.loads(s)
    except Exception:
        return json.loads(re.sub(r'^\s*//.*$', '', s, flags=re.M))

for name, base in MAPS:
    print(f"\n===== {name} =====")
    z = zipfile.ZipFile(f"{base}/{name}")
    objs = loads_permissive(z.read("objects.json").decode("utf-8", "replace"))
    olist = objs.get("objects", objs) if isinstance(objs, dict) else objs
    for o in olist:
        t = str(o.get("type", "?"))
        if "town" in t.lower():
            # 打印城对象除模板字段外的关键字段
            keys = {k: v for k, v in o.items() if k not in ("type", "x", "y", "l", "id", "instanceName", "template")}
            s = json.dumps(keys, ensure_ascii=False)
            print(f"  {o.get('instanceName')} ({o.get('x')},{o.get('y')}) {t}")
            print(f"    字段键: {list(keys.keys())[:15]}")
            # garrison/army 相关
            for gk in ("garrison", "army", "stacks", "creatures", "options", "spellStrength"):
                if gk in keys:
                    print(f"    {gk}: {json.dumps(keys[gk], ensure_ascii=False)[:220]}")
