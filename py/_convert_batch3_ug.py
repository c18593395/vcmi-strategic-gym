#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_convert_batch3_ug.py — batch3 14 张地下图「保留地下层」转换 + 入池 + batch:3 标记

背景 (09-26 条件3):
  09-19 批转时 14 张被 strip_underground 成单层版入池 (index.batch=None 未放行)。
  batch3 要的是保留地下层的版本 (OBS 同层假设重验 = 条件4 的前置件)。

流程 (每张图):
  1. h3m 源定位: H3M_DIR 下按 safe 名匹配 (全小写实存)
  2. h3m2vmap --save --no-r1 → raw vmap (cwd=vcmi-native, #248)
  3. 不做 strip (保留地下层)
  4. sanitize 玩家痕迹 (复用 py/sanitize_vmap_players_0920.py)
  5. 自检: header.mapLevels 含 underground + objects 有 z==1 + players 非空 (三件套)
  6. 命名 <safe>_ug_h3m.vmap → 池 maps/training/h3m_pool + 运行时 rel/bin/data/Maps
  7. _pool_index.json 加条目 {batch:3, blue_ai:"MMAI_RANDOM", layer:"underground", verify, ts}
     双副本纪律: 主仓 _pool_index.json 改完, 服务器副本同步另排 (服务器当前断线)

用法:
  wsl bash -c "cd /mnt/d/Bigdata/hero3_fresh && /home/administrator/vcmi-workspace/venv/bin/python py/_convert_batch3_ug.py"
  --dry 只定位+自检不写池
"""
import json, os, re, sys, time, shutil, subprocess, zipfile, glob

ROOT = "/mnt/d/Bigdata/hero3_fresh"
H3M_DIR = os.environ.get("H3M_DIR", "/home/administrator/vcmi-native/rel/bin/data/Maps")
BIN = os.environ.get("BIN", "/home/administrator/vcmi-native/tools/h3m2vmap/build/h3m2vmap")
WORKDIR = "/home/administrator/vcmi-native"          # #248 转换器 cwd
WORK = "/tmp/batch3_ug"
POOL = f"{ROOT}/maps/training/h3m_pool"
POOL_INDEX = f"{ROOT}/maps/h3m_to_vmap/_pool_index.json"
BATCHES = f"{ROOT}/maps/h3m_to_vmap/_pool_batches.json"

sys.path.insert(0, f"{ROOT}/py")
import strip_underground_vmap as su   # 复用 load_json (带 // 注释剥离)


def find_h3m(h3m_field):
    """用 batch 表的 h3m 字段 (如 \"Darwin's Prize(Allies).h3m\") 在 H3M_DIR 里
    大小写不敏感匹配实存文件 (实存全小写). 返回绝对路径或 None."""
    if not os.path.isdir(H3M_DIR):
        return None
    files = os.listdir(H3M_DIR)
    low = {f.lower(): f for f in files if f.lower().endswith(".h3m")}
    target = h3m_field.lower()
    if target in low:
        return os.path.join(H3M_DIR, low[target])
    # 去空白/括号/标点兜底
    norm = lambda s: re.sub(r"[^a-z0-9]", "", s)
    tn = norm(target)
    cands = [f for f in low if norm(low[f]) == tn]
    if len(cands) == 1:
        return os.path.join(H3M_DIR, cands[0])
    return None


def has_underground(vmap):
    with zipfile.ZipFile(vmap) as z:
        h = su.load_json(z, "header.json")
        return "underground" in (h.get("mapLevels") or {})


def selfcheck(vmap):
    """三件套: 有地下层 + l!=0 对象存在 + players 非空. 层字段权威读法=su.obj_z (l 优先, 兼容 position/z).
    返回 (ok, detail)."""
    errs = []
    with zipfile.ZipFile(vmap) as z:
        h = su.load_json(z, "header.json")
        objs = su.load_json(z, "objects.json")
        if "underground" not in (h.get("mapLevels") or {}):
            errs.append("mapLevels 无 underground (strip 了?!)")
        n_under = 0
        total = 0
        if isinstance(objs, list):
            for o in objs:
                if isinstance(o, dict):
                    total += 1
                    if su.obj_z(o) != 0:
                        n_under += 1
        if n_under == 0:
            errs.append(f"objects 无 l!=0 对象 (total={total})")
        pl = h.get("players")
        if not isinstance(pl, dict) or not pl:
            errs.append(f"header.players 空 ({pl!r})")
        else:
            for side in ("red", "blue"):
                if side not in pl:
                    errs.append(f"players 缺 {side}")
    return (not errs), ("; ".join(errs) if errs else f"underground OK l!=0对象={n_under}/{total}")


def run_convert(h3m, safe):
    """h3m2vmap 转 1 张, 3 试. 返回 raw 路径或 None."""
    raw = f"{WORK}/{safe}_ug.raw.vmap"
    for i in range(3):
        if os.path.exists(raw):
            os.remove(raw)
        r = subprocess.run([BIN, "--save", h3m, raw, "--no-r1"],
                           cwd=WORKDIR, capture_output=True, text=True, timeout=240)
        ok = (r.returncode == 0 and os.path.exists(raw)
              and os.path.getsize(raw) > 100 and "SAVE OK" in (r.stdout or ""))
        if ok:
            return raw
        print(f"    convert 试{i+1} 失败: {(r.stderr or r.stdout or 'timeout')[-160:]}", flush=True)
        time.sleep(2)
    return None


def main():
    dry = "--dry" in sys.argv
    pb = json.load(open(BATCHES, encoding="utf-8"))
    entries = pb["batch3_underground"]
    print(f"batch3_underground {len(entries)} 张, dry={dry}")
    os.makedirs(WORK, exist_ok=True)
    os.makedirs(POOL, exist_ok=True)

    idx = json.load(open(POOL_INDEX, encoding="utf-8")) if os.path.exists(POOL_INDEX) else {}
    n_ok = n_fail = n_skip = 0
    for e in entries:
        vmap_old = e["vmap"]                 # all_for_one_h3m.vmap (去地下版, 已入池)
        safe = vmap_old.replace("_h3m.vmap", "")
        fn = f"{safe}_ug_h3m.vmap"           # 保留地下版命名
        pool_path = f"{POOL}/{fn}"
        if os.path.exists(pool_path) and idx.get(fn, {}).get("batch") == 3:
            print(f"  [SKIP] {fn} 已在池且 batch=3")
            n_skip += 1
            continue
        h3m = find_h3m(e.get("h3m", ""))
        if not h3m:
            print(f"  [FAIL] {safe} 找不到 h3m 源")
            n_fail += 1
            continue
        print(f"  {safe}: {os.path.basename(h3m)} → {fn}", flush=True)
        raw = run_convert(h3m, safe)
        if not raw:
            print(f"    [FAIL] 转换 3 试全败")
            n_fail += 1
            continue
        # sanitize 玩家痕迹
        try:
            import sanitize_vmap_players_0920 as sv
            ch = sv.sanitize_and_save(raw)
            if ch:
                print(f"    [SANITIZE] {len(ch)} 处玩家痕迹清洗", flush=True)
        except Exception as ex:
            print(f"    [WARN] sanitize 异常(继续): {ex}", flush=True)
        # 自检
        ok, detail = selfcheck(raw)
        if not ok:
            print(f"    [FAIL] 自检: {detail}")
            n_fail += 1
            continue
        if dry:
            print(f"    [DRY-OK] {detail}")
            n_ok += 1
            continue
        # 部署: 池 + 运行时
        shutil.copy(raw, pool_path)
        dst = os.path.join(H3M_DIR, fn)
        shutil.copy(raw, dst)
        # index 标记 (batch=3 未放行, HOMM3_H3M_BATCH<3 时不采出)
        idx[fn] = {
            "blue_ai": "MMAI_RANDOM",
            "layer": "underground",
            "batch": 3,
            "h3m": e.get("h3m", ""),
            "based_on": vmap_old,
            "verify": f"ug-converted {detail}",
            "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        print(f"    [PASS] {detail} → 池+运行时, index batch=3")
        n_ok += 1
        # 每张落盘 index (断点)
        with open(POOL_INDEX, "w", encoding="utf-8") as f:
            json.dump(idx, f, indent=2, ensure_ascii=False)
    print(f"\n==== batch3 地下转换汇总: OK={n_ok} FAIL={n_fail} SKIP={n_skip} (dry={dry}) ====")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
