"""King of Pain 精简 vmap 就地修补: town subtype 'core:object' -> 真族系
直接从完整 vmap 的 options.availableFactions[0] 读族系, 无需重跑整转换"""
import zipfile, json, shutil, re, sys, os

FULL = "vcmi/data/Maps/vmap_from_h3m/King of Pain.h3m.vmap"
TARGETS = [
    "maps/training/King_of_Pain_h3m.vmap",
    "vcmi/data/Maps/King_of_Pain_h3m.vmap",
    "vcmi_gym/envs/v13/maps/King_of_Pain_h3m.vmap",
]
FACTION_ORDER = ["castle", "rampart", "tower", "inferno", "necropolis",
                 "dungeon", "stronghold", "fortress", "conflux"]


def strip_json_comments(s):
    s = re.sub(r'//[^\n]*', '', s)
    s = re.sub(r'/\*.*?\*/', '', s, flags=re.S)
    return json.loads(s)


def get_faction_from_full(src_vmap):
    """从完整 vmap 的 randomTown options.availableFactions[0] 读每镇的族系"""
    with zipfile.ZipFile(src_vmap) as z:
        objs = strip_json_comments(z.read("objects.json").decode('utf-8'))
    towns = []
    for obj in objs:
        if obj.get("type") == "randomTown":
            opts = obj.get("options") or {}
            avail = opts.get("availableFactions") or []
            if isinstance(avail, list) and avail:
                fac = str(avail[0]).split(':')[-1]
            else:
                fac = "dungeon"
            towns.append({
                "x": int(obj["x"]), "y": int(obj["y"]),
                "faction": fac, "owner": opts.get("owner"),
                "subtype_raw": obj.get("subtype"),
            })
    return towns


def pick_faction(towns, i):
    """第 i 个镇 (按转换时 x 顺序) 的族系: 优先 x/y 完全匹配"""
    return towns[i]["faction"] if i < len(towns) else "dungeon"


def fix(target, towns_full, dry=False):
    # 读入
    with zipfile.ZipFile(target) as z:
        members = {n: z.read(n) for n in z.namelist()}
    obj = json.loads(members["objects.json"])
    town_keys = sorted([k for k in obj if k.startswith("town_")],
                       key=lambda s: int(s.split("_")[1]))
    before = [obj[k].get("subtype") for k in town_keys]
    # 重设 subtype: 按 (x, y) 匹配完整 vmap 的镇
    fixed = 0
    for k in town_keys:
        cur = obj[k]
        cx, cy = int(cur.get("x", 0)), int(cur.get("y", 0))
        matched = next((t for t in towns_full if t["x"] == cx and t["y"] == cy), None)
        new_sub = ("core:" + matched["faction"]) if matched else "core:dungeon"
        if cur.get("subtype") != new_sub:
            cur["subtype"] = new_sub
            fixed += 1
    if dry:
        print(f"[dry] {target}: {fixed} 处修复")
        return fixed
    # 重写 zip
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
        for n, data in members.items():
            if n == "objects.json":
                z.writestr(n, json.dumps(obj, indent=2, ensure_ascii=False))
            else:
                z.writestr(n, data)
    print(f"OK {target}: {fixed} 处修复")
    return fixed


if __name__ == "__main__":
    print(f"[1] 读完整 vmap: {FULL}")
    towns_full = get_faction_from_full(FULL)
    print(f"    完整 vmap 有 {len(towns_full)} 镇:")
    for t in towns_full:
        print(f"      ({t['x']},{t['y']}) faction={t['faction']} owner={t['owner']}")
    dry = "--dry" in sys.argv
    print(f"[2] 修补目标 ({'dry' if dry else 'write'}):")
    for tp in TARGETS:
        if not os.path.exists(tp):
            print(f"    [skip] {tp} 不存在")
            continue
        fix(tp, towns_full, dry=dry)
