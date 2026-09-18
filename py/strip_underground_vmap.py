#!/usr/bin/env python3
"""
strip_underground_vmap.py — vmap 去地下层后处理 (2026-09-18)

背景:
  h3m2vmap (B4 二进制) 直通/规则转换官方 H3M 后, 产物 vmap 带地下层.
  训练需要单层图 (T01-T06 全单层, 引擎已验证形态). 本脚本在 vmap JSON 层
  删除地下层, 不碰 C++, 不碰双树.

处理内容:
  1. objects.json: 删除所有 z==1 条目; surface (z==0) 上残留的
     subterraneanGate (地下门) 联动删除 (地下没了, 门成死门);
  2. header.json: mapLevels 删除 underground 键 (保留 surface);
     players[*] 若有 mainTownPos/pos 且 z!=0 则归零 (防悬空引用);
  3. zip 条目: 删除地下 terrain 文件 (名字含 underground/under 的
     terrain json), 其余条目字节原样保留;
  4. 自校验: 复查产物无 z==1 对象 / 无 underground 键 / terrain 对齐.

产出命名: <stem>_nounder_adventure.vmap (adventure 关键词过
strategic_env.py L522 图名断言; nounder 标识无地下层).

判据链: 本脚本自校验 → h3m2vmap verify → ep_runner 冒烟 →
sync_maps_to_runtime.py --strict.

用法:
  python py/strip_underground_vmap.py <in.vmap> [<in2.vmap> ...] [--peek] [--outdir DIR]
  --peek    只打印内部结构, 不写文件
  --outdir  输出目录 (默认与输入同目录)
"""
import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

# 地下去除后需从 surface 联动清除的对象类型 (地下专属/死门)
SURFACE_PURGE_TYPES = {"subterraneanGate"}


def strip_comments(text):
    """VCMI saveMap 的 JSON 带 `// game` 注释, 剥离后再 parse."""
    out = []
    for line in text.split("\n"):
        i, in_str, buf = 0, False, []
        while i < len(line):
            ch = line[i]
            if ch == '"' and (i == 0 or line[i - 1] != "\\"):
                in_str = not in_str
            if not in_str and ch == "/" and i + 1 < len(line) and line[i + 1] == "/":
                break
            buf.append(ch)
            i += 1
        out.append("".join(buf))
    return "\n".join(out)


def load_json(z, name):
    raw = z.read(name).decode("utf-8")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return json.loads(strip_comments(raw))


def obj_z(o):
    """h3m2vmap 产物: 顶层 l (layer) + x + y; 兼容 position/z 形态."""
    if "l" in o:
        return int(o["l"])
    p = o.get("position")
    if isinstance(p, dict):
        return int(p.get("z", 0))
    if isinstance(p, list) and len(p) == 3:
        return int(p[2])
    if "z" in o:
        return int(o["z"])
    return 0


def obj_type(o):
    return (o.get("type") or o.get("typeName") or "").lower()


def peek(path):
    """打印内部结构 (探测模式)."""
    with zipfile.ZipFile(path) as z:
        print(f"=== {path} ===")
        for n in z.namelist():
            print(f"  {n}  ({z.getinfo(n).file_size} B)")
        h = load_json(z, "header.json")
        ml = h.get("mapLevels") or {}
        print(f"  mapLevels keys: {list(ml.keys())}")
        for k, v in ml.items():
            print(f"    {k}: {json.dumps(v)[:200]}")
        print(f"  header keys: {list(h.keys())}")
        objs = load_json(z, "objects.json")
        zs = {}
        types_under = {}
        for o in objs:
            zz = obj_z(o)
            zs[zz] = zs.get(zz, 0) + 1
            if zz != 0:
                types_under[obj_type(o)] = types_under.get(obj_type(o), 0) + 1
        print(f"  objects: {len(objs)}  z 分布: {zs}")
        if objs:
            print(f"  对象[0] keys: {list(objs[0].keys())}")
            print(f"  对象[0]: {json.dumps(objs[0])[:500]}")
        print(f"  地下对象类型: {types_under}")
        # 城 owner 分布 (owner 在 options.owner; R1 归零后全 neutral)
        tw_surface, tw_under = [], []
        for o in objs:
            if obj_type(o) != "town":
                continue
            own = str((o.get("options") or {}).get("owner", "?"))
            (tw_under if obj_z(o) != 0 else tw_surface).append(f"{o.get('instanceName','?')}({own})@({o.get('x')},{o.get('y')},l{obj_z(o)})")
        print(f"  surface 城: {tw_surface}")
        print(f"  地下城: {tw_under}")
        gate = [obj_type(o) for o in objs
                if obj_type(o) in SURFACE_PURGE_TYPES and obj_z(o) == 0]
        print(f"  surface 死门候选: {len(gate)} {set(gate)}")
        pl = h.get("players")
        if isinstance(pl, dict):
            for k, v in list(pl.items())[:4]:
                keys = [x for x in (v or {}) if "own" in x.lower() or "pos" in x.lower()]
                print(f"  player[{k}] pos相关键: {({x: v[x] for x in keys})}")
        heroes = h.get("heroes")
        if heroes:
            print(f"  header.heroes: {len(heroes)} 条")


def strip_underground(path, outdir=None):
    """执行去地下层, 返回 (输出路径, 审计 dict)."""
    path = Path(path)
    audit = {"input": str(path)}
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        header = load_json(z, "header.json")
        objects = load_json(z, "objects.json")

        # 1) 对象: 删 z!=0 + surface 死门
        total = len(objects)
        kept, removed_under, removed_gate = [], 0, 0
        for o in objects:
            zz = obj_z(o)
            if zz != 0:
                removed_under += 1
                continue
            if obj_type(o) in SURFACE_PURGE_TYPES:
                removed_gate += 1
                continue
            kept.append(o)
        audit["objects_total"] = total
        audit["objects_removed_underground"] = removed_under
        audit["objects_removed_deadgate"] = removed_gate
        audit["objects_kept"] = len(kept)

        # 2) header: mapLevels 删 underground
        ml = header.get("mapLevels") or {}
        had_ug = "underground" in ml
        ml.pop("underground", None)
        header["mapLevels"] = ml
        audit["mapLevels_had_underground"] = had_ug
        audit["mapLevels_now"] = list(ml.keys())

        # players 内 mainTown/pos 类字段层归零 (防悬空地下引用)
        pl = header.get("players")
        fixed_pos = 0
        if isinstance(pl, dict):
            for v in pl.values():
                if not isinstance(v, dict):
                    continue
                for key in ("mainTown", "pos", "mainTownPos"):
                    p = v.get(key)
                    if isinstance(p, dict):
                        zkey = "l" if "l" in p else ("z" if "z" in p else None)
                        if zkey and int(p.get(zkey, 0)) != 0:
                            p[zkey] = 0
                            fixed_pos += 1
                    elif isinstance(p, list) and len(p) == 3 and int(p[2]) != 0:
                        p[2] = 0
                        fixed_pos += 1
        audit["player_pos_fixed"] = fixed_pos

        # 3) 组装新 zip: 地下 terrain 丢弃, 其余原样, 动过的重写
        drop = [n for n in names
                if re.search(r"under", n, re.I) and n.endswith(".json")
                and n not in ("header.json", "objects.json")]
        audit["terrain_dropped"] = drop
        out_name = path.stem + "_nounder_adventure.vmap"
        out_dir = Path(outdir) if outdir else path.parent
        out_path = out_dir / out_name

        with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zo:
            for n in names:
                if n in drop:
                    continue
                if n == "header.json":
                    zo.writestr(n, json.dumps(header, ensure_ascii=False))
                elif n == "objects.json":
                    zo.writestr(n, json.dumps(kept, ensure_ascii=False))
                else:
                    zo.writestr(n, z.read(n))

    # 4) 自校验: 复查产物
    with zipfile.ZipFile(out_path) as z:
        h2 = load_json(z, "header.json")
        o2 = load_json(z, "objects.json")
        errs = []
        if "underground" in (h2.get("mapLevels") or {}):
            errs.append("mapLevels.underground 仍存在")
        bad_z = [o for o in o2 if obj_z(o) != 0]
        if bad_z:
            errs.append(f"仍有 {len(bad_z)} 个 z!=0 对象")
        still_gate = [o for o in o2 if obj_type(o) in SURFACE_PURGE_TYPES]
        if still_gate:
            errs.append(f"仍有 {len(still_gate)} 个死门")
        need_terrain = [k for k in (h2.get("mapLevels") or {})]
        have_terrain = [n for n in z.namelist() if "terrain" in n.lower()]
        audit["terrain_files_now"] = have_terrain
        if len(have_terrain) < len(need_terrain):
            errs.append(f"terrain 文件 {have_terrain} 与层数 {need_terrain} 不齐")
    audit["selfcheck"] = "OK" if not errs else "FAIL: " + "; ".join(errs)
    audit["output"] = str(out_path)
    audit["output_size"] = out_path.stat().st_size
    return out_path, audit


def main():
    ap = argparse.ArgumentParser(description="vmap 去地下层后处理")
    ap.add_argument("inputs", nargs="+", help="输入 vmap (一个或多个)")
    ap.add_argument("--peek", action="store_true", help="只探测结构不写文件")
    ap.add_argument("--outdir", default="", help="输出目录 (默认与输入同目录)")
    args = ap.parse_args()

    if args.peek:
        for p in args.inputs:
            peek(p)
        return 0

    rc = 0
    for p in args.inputs:
        out, audit = strip_underground(p, args.outdir or None)
        for k, v in audit.items():
            print(f"  {k}: {v}")
        if audit["selfcheck"] != "OK":
            rc = 1
        print()
    return rc


if __name__ == "__main__":
    sys.exit(main())
