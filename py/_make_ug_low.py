#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_make_ug_low.py — batch3 地下图「减怪低密度」重转 (09-27, 用户拍板路线)

背景: 全密度 13 张 _ug 图条件5/6实测全 hold (31~40 步 HERO_DEATH, dense_neutral 怪太密)。
用户路线: 地下图减怪重转 + 地图重编号 (新系列 _ug_low), 全密度 _ug 原图保留 (batch:99 待 ckpt 提升后重评)。

处理: 输入 = 池内全密度 <safe>_ug_h3m.vmap (已 sanitize 玩家痕迹)。
     只删 地表层(l==0) 中性系怪物族对象 (monster/randommonster*/randomcreature*/creaturegenerator*),
     保留 red/blue owner 的兵 (开局军队), 保留地下层对象 (英雄无门到不了, 无影响), 保留资源/矿/城/门。
     删除策略 = 中性怪全集中删 50% (按文件序交替, 确定性可复现)。
输出: <safe>_ug_low_h3m.vmap → 池 + 运行时 H3M_DIR + index batch:3 (low_density 标记)。
命名: _ug_low 新编号系列, 与全密度 _ug 并存互不覆盖 (图名断言 L534 认 h3m 关键字, 可过)。

用法 (WSL):
  cd /mnt/d/Bigdata/hero3_fresh && /home/administrator/vcmi-workspace/venv/bin/python py/_make_ug_low.py [--dry]
"""
import json, os, sys, re, time, shutil, zipfile, glob
sys.path.insert(0, "/mnt/d/Bigdata/hero3_fresh/py")
import strip_underground_vmap as su

ROOT = "/mnt/d/Bigdata/hero3_fresh"
POOL = f"{ROOT}/maps/training/h3m_pool"
H3M_DIR = os.environ.get("H3M_DIR", "/home/administrator/vcmi-native/rel/bin/data/Maps")
POOL_INDEX = f"{ROOT}/maps/h3m_to_vmap/_pool_index.json"

# 中性系怪物族 (地表删减对象); 玩家 owner 的兵永不删
MONSTER_RE = re.compile(r"^(monster|randommonster|randomcreature|creaturegenerator)")
NEUTRAL_OWNERS = {None, "", "neutral"}

DRY = "--dry" in sys.argv


def neutral_surface_monsters(objs):
    """返回 (全部中性地表怪下标按文件序, 总数, 类型分布). 只 l==0 + owner 中性 + 怪物族."""
    idxs, bytype = [], {}
    for i, o in enumerate(objs):
        if not isinstance(o, dict):
            continue
        if su.obj_z(o) != 0:
            continue
        owner = (o.get("options") or {}).get("owner", o.get("owner"))
        if owner not in NEUTRAL_OWNERS:
            continue
        t = su.obj_type(o)
        if MONSTER_RE.match(t):
            idxs.append(i)
            bytype[t] = bytype.get(t, 0) + 1
    return idxs, bytype


def make_low(src_vmap, dst_vmap, ratio=0.5):
    """src 全密度 → dst 低密度 (确定性删 ceil(n*ratio) 个: 文件序交替取)."""
    with zipfile.ZipFile(src_vmap) as z:
        names = z.namelist()
        data = {n: z.read(n) for n in names}
    objs = su.load_json(zipfile.ZipFile(src_vmap), "objects.json")  # list
    idxs, bytype = neutral_surface_monsters(objs)
    # 交替取 (0,2,4...) 保留, 删 (1,3,5...) → 确定 ceil(n/2)
    keep = set(i for i in range(0, len(idxs), 2))  # 偶数位保留
    drop = [idxs[j] for j in range(1, len(idxs), 2)]
    new_objs = [o for i, o in enumerate(objs) if i not in set(drop)]
    removed = len(drop)
    audit = {
        "src": os.path.basename(src_vmap), "dst": os.path.basename(dst_vmap),
        "neutral_surface_monsters": len(idxs), "removed": removed,
        "kept": len(idxs) - removed, "bytype": bytype,
        "objects_total": len(objs), "objects_after": len(new_objs),
    }
    # 重建 zip: 仅 objects.json 重写, 其余条目字节原样
    out = os.path.join(os.path.dirname(dst_vmap), ".tmp_" + os.path.basename(dst_vmap))
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zo:
        for n in names:
            if n == "objects.json":
                zo.writestr(n, json.dumps(new_objs))
            else:
                zo.writestr(n, data[n])
    # 自检
    with zipfile.ZipFile(out) as z:
        assert z.testzip() is None, "zip 自检失败"
        h = su.load_json(z, "header.json")
        objs2 = su.load_json(z, "objects.json")
        assert "underground" in (h.get("mapLevels") or {}), "地下层丢了?!"
        assert len(objs2) == len(new_objs), "objects 数不一致"
        pl = h.get("players")
        assert isinstance(pl, dict) and pl, "players 空?!"
    if DRY:
        os.remove(out)
        return audit, True
    shutil.move(out, dst_vmap)
    return audit, False


def main():
    idx = json.load(open(POOL_INDEX, encoding="utf-8"))
    ug_full = sorted(os.path.basename(p) for p in glob.glob(POOL + "/*_ug_h3m.vmap")
                    if not p.endswith("_ug_low_h3m.vmap"))
    print(f"全密度 _ug 源 {len(ug_full)} 张, dry={DRY}")
    n_ok = 0
    for fn in ug_full:
        safe = fn.replace("_ug_h3m.vmap", "")
        low_name = f"{safe}_ug_low_h3m.vmap"
        dst = os.path.join(POOL, low_name)
        if os.path.exists(dst) and idx.get(low_name, {}).get("batch") == 3:
            print(f"  [SKIP] {low_name} 已在池 batch=3")
            continue
        audit, skipped = make_low(os.path.join(POOL, fn), dst)
        if skipped:
            print(f"  [DRY] {safe}: 中性地表怪 {audit['neutral_surface_monsters']} → 删 {audit['removed']} 留 {audit['kept']} {audit['bytype']}")
            continue
        # 部署: 运行时 + index
        if os.path.isdir(H3M_DIR):
            shutil.copy(dst, os.path.join(H3M_DIR, low_name))
        entry = idx.get(low_name, {})
        entry.update({
            "blue_ai": "MMAI_RANDOM", "layer": "underground", "batch": 3,
            "low_density": True, "based_on": fn,
            "reduce": f"地表中性怪 {audit['neutral_surface_monsters']} 删{audit['removed']}留{audit['kept']} (怪物族 {list(audit['bytype'].keys())})",
            "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        })
        idx[low_name] = entry
        print(f"  [PASS] {low_name}: 删 {audit['removed']}/{audit['neutral_surface_monsters']} "
              f"(对象 {audit['objects_total']}→{audit['objects_after']})")
        n_ok += 1
        with open(POOL_INDEX, "w", encoding="utf-8") as f:
            json.dump(idx, f, indent=2, ensure_ascii=False)
    print(f"\n==== 减怪重转: {n_ok} 张 (dry={DRY}) ====")
    return 0


if __name__ == "__main__":
    sys.exit(main())
