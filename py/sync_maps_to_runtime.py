#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""maps/training/*.vmap -> 运行时 data/Maps 权威同步工具 (09-14 固化; 两入口软链同一真实目录, 自动去重)

为什么存在:
  连接器实际从 VCMI_BIN_DIR/data/Maps 读图 (chdir 后 userDataPath/Maps)。两个 VCMI 树
  (vcmi-native / vcmi-native-build) 下的 data/Maps 都是符号链接, 指向【同一真实目录】:
    /mnt/d/Bigdata/hero3_fresh/vcmi/data/Maps  (= Windows 仓库 vcmi/data/Maps)
  本脚本按 resolve() 去重后只写一次真实文件, 同时校验两个软链入口存活。
  地图权威源在仓库 maps/training/。两次事故 (09-14) 都是只改源没同步运行时目录:
    ① 4 张 T06 _02 header 缺字段/运行时旧版 -> segfault/Invalid range + 残留 traj 假局
    ② King players=[] / core:dragon / orange 玩家 4 旧版 -> 603s 卡死脏局

铁律: 改任何 maps/training/*.vmap (补丁/重新生成) 后, 必须在 WSL 跑一次:
    /home/administrator/vcmi-workspace/venv/bin/python py/sync_maps_to_runtime.py

同步清单唯一事实源 = train_wsl2_ppo_v2.py 顶层 MAPS (退役图不推, 仅漂移报告)。

用法:
  python sync_maps_to_runtime.py                # 预检 + 同步 + 写后校验
  python sync_maps_to_runtime.py --check        # 只校验不同步, 不一致/不合法 -> 退出码 1 (可接 CI)
  python sync_maps_to_runtime.py --dry-run      # 报告将要做什么, 不写
  python sync_maps_to_runtime.py --strict       # 额外用 VCMI config 注册表查 monster/town identifier
  python sync_maps_to_runtime.py X.vmap Y.vmap  # 只同步指定图 (仍须在 MAPS 清单内)
  python sync_maps_to_runtime.py --purge        # 删除运行时副本中不在 MAPS 的 .vmap (默认只报告不删)

退出码: 0 全部一致且校验通过; 1 存在失败项 (--check 不一致也算)
"""
import ast
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

# ---------- 路径 (WSL 为训练环境; Windows 直跑只支持 --check 源侧并给出提示) ----------
HERE = Path(__file__).resolve()
ROOT = HERE.parent.parent                      # d:\Bigdata\hero3_fresh
SRC_DIR = ROOT / "maps" / "training"
TRAIN_PY = ROOT / "train_wsl2_ppo_v2.py"
TARGETS = [
    Path("/home/administrator/vcmi-native/rel/bin/data/Maps"),
    Path("/home/administrator/vcmi-native-build/rel/bin/data/Maps"),
]
VCMI_CONFIG = Path("/home/administrator/vcmi-native/config")
VMAP_ENTRIES = {"header.json", "surface_terrain.json", "objects.json"}
LEGAL_OWNERS = {None, "red", "blue"}          # orange 等非法玩家槽 -> player 4 SIGSEGV 教训


def log(level, msg):
    mark = {"ok": "[ OK ]", "skip": "[SKIP]", "warn": "[WARN]", "fail": "[FAIL]",
            "info": "[INFO]", "sync": "[SYNC]"}[level]
    print(f"{mark} {msg}", flush=True)


# ---------- MAPS 清单解析 (只取顶层第一个 MAPS 赋值, 不被 walk 顺序影响) ----------
def parse_maps_list():
    tree = ast.parse(TRAIN_PY.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "MAPS" for t in node.targets
        ):
            val = ast.literal_eval(node.value)
            assert isinstance(val, list) and all(isinstance(x, str) for x in val)
            return val
    raise RuntimeError("train_wsl2_ppo_v2.py 中未找到顶层 MAPS 列表")


# ---------- JSONC 清洗 (VCMI config 带 // /* */ 注释) ----------
def strip_jsonc(text):
    out, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if c in '"\'':
            q = c
            out.append(c)
            i += 1
            while i < n:
                out.append(text[i])
                if text[i] == "\\" and i + 1 < n:
                    out.append(text[i + 1])
                    i += 2
                    continue
                if text[i] == q:
                    i += 1
                    break
                i += 1
        elif c == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                i += 1
        elif c == "/" and i + 1 < n and text[i + 1] == "*":
            i += 2
            while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


def load_core_registry():
    """返回 (creature_ids, town_ids); config 缺失则返回 (None, None) 跳过该校验"""
    cdir, tdir = VCMI_CONFIG / "creatures", VCMI_CONFIG / "towns"
    if not cdir.is_dir():
        return None, None
    creatures, towns = set(), set()
    for f in cdir.glob("*.json"):
        try:
            d = json.loads(strip_jsonc(f.read_text(encoding="utf-8")))
            creatures.update(k for k, v in d.items() if isinstance(v, dict))
        except Exception as e:
            log("warn", f"注册表解析失败 {f.name}: {e}")
    if tdir.is_dir():
        towns = {p.stem for p in tdir.glob("*.json")}
    return {"core:" + c for c in creatures}, {"core:" + t for t in towns}


# ---------- 单图预检 ----------
def inspect_vmap(path, strict_registry):
    """返回 (errors[], warnings[], info{})"""
    errs, warns = [], []
    if not path.is_file():
        return [f"源文件不存在: {path}"], [], {}
    try:
        zf = zipfile.ZipFile(path)
    except Exception as e:
        return [f"zip 无法打开: {e}"], [], {}
    with zf:
        bad = zf.testzip()
        if bad:
            errs.append(f"zip CRC 损坏条目: {bad}")
        names = set(zf.namelist())
        missing = VMAP_ENTRIES - names
        if missing:
            errs.append(f"zip 缺条目: {sorted(missing)}")
            return errs, warns, {}
        header = json.loads(zf.read("header.json").decode("utf-8", "replace"))
        objs = json.loads(zf.read("objects.json").decode("utf-8", "replace"))
    items = objs if isinstance(objs, dict) else {}

    # ① players 必须是非空 dict 且含 red/blue (King players=[] 教训)
    players = header.get("players")
    if not isinstance(players, dict) or not players:
        errs.append(f"header.players 为空或非 dict: {players!r}")
    else:
        for side in ("red", "blue"):
            if side not in players:
                errs.append(f"header.players 缺 {side} 方")
    if isinstance(header.get("mods"), list):
        warns.append("header.mods 是 list (历史旧版, 09-13 已规范为 {} )")

    # ② owner 合法性 + 双方至少各有 1 城 1 英雄 (red 无城无英雄 -> no_own_town 脏局)
    owner_town = {"red": 0, "blue": 0}
    owner_hero = {"red": 0, "blue": 0}
    n_mon = 0
    for key, o in items.items():
        t = o.get("type")
        opts = o.get("options", {}) if isinstance(o.get("options"), dict) else {}
        owner = opts.get("owner", None)
        if owner not in LEGAL_OWNERS:
            errs.append(f"{key} ({t} @{o.get('x')},{o.get('y')}) 非法 owner={owner!r}")
        if t == "town" and owner in owner_town:
            owner_town[owner] += 1
        if t == "hero":
            if owner in owner_hero:
                owner_hero[owner] += 1
            htype = opts.get("type")
            if owner in ("red", "blue") and not htype:
                errs.append(f"{key} 英雄 owner={owner} 但 options.type 缺失")
        # ③ strict: identifier 注册表
        if strict_registry[0] and t == "monster":
            n_mon += 1
            sub = o.get("subtype")
            if isinstance(sub, str) and sub.startswith("core:") and sub not in strict_registry[0]:
                errs.append(f"{key} 怪物 identifier 未注册: {sub} (core:dragon 教训)")
        if strict_registry[1] and t == "town":
            sub = o.get("subtype")
            if isinstance(sub, str) and sub.startswith("core:") and sub not in strict_registry[1]:
                errs.append(f"{key} 城镇 identifier 未注册: {sub}")
    for side in ("red", "blue"):
        if owner_town[side] == 0:
            errs.append(f"{side} 方无城镇 (no_own_town 脏局风险)")
        if owner_hero[side] == 0:
            warns.append(f"{side} 方无英雄对象")
    info = {"towns": owner_town, "heroes": owner_hero, "monsters": n_mon,
            "keys": len(header)}
    return errs, warns, info


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def atomic_install(src, dst):
    tmp = dst.with_name("." + dst.name + ".sync.tmp")
    data = src.read_bytes()
    with open(tmp, "wb") as f:
        f.write(data)
        f.flush()
        import os
        os.fsync(f.fileno())
    os.replace(tmp, dst)
    return hashlib.sha256(data).hexdigest()


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    check_only = "--check" in flags
    dry_run = "--dry-run" in flags
    strict = "--strict" in flags
    purge = "--purge" in flags

    if check_only and dry_run:
        log("fail", "--check 与 --dry-run 互斥")
        return 1

    maps = parse_maps_list()
    only = set(args)
    selected = [m for m in maps if not only or m in only]
    if only:
        unknown = only - set(maps)
        if unknown:
            log("fail", f"指定图不在 MAPS 清单: {sorted(unknown)}")
            return 1
    registry = load_core_registry() if strict else (None, None)
    if strict and registry[0] is None:
        log("warn", "未找到 VCMI config/creatures, strict identifier 校验跳过 (需在 WSL 运行)")

    log("info", f"权威清单 MAPS={len(maps)} 张, 本次处理 {len(selected)} 张"
                f"{'  [CHECK]' if check_only else ''}{'  [DRY-RUN]' if dry_run else ''}{'  [STRICT]' if strict else ''}")
    if SRC_DIR.is_dir():
        log("info", f"源目录 {SRC_DIR}")
    else:
        log("fail", f"源目录不存在: {SRC_DIR}")
        return 1
    # ---- 运行时入口 -> resolve() 真实目录 (两入口是指向同一目录的软链, 必须去重) ----
    real_dirs = {}   # Path(真实目录) -> [(入口标签, 入口路径)]
    broken = []
    for t in TARGETS:
        label = "native-build" if "vcmi-native-build" in t.parts else "native"
        if not t.is_dir():
            broken.append(t)
            continue
        real_dirs.setdefault(t.resolve(), []).append((label, t))
    for d in broken:
        log("fail", f"运行时 Maps 入口缺失或断链: {d}")
    if broken and not (check_only or dry_run):
        return 1
    if not real_dirs:
        log("fail", "无可用运行时 Maps 目录 (请在 WSL 执行)")
        return 1
    for real, links in real_dirs.items():
        log("info", f"运行时真实目录 {real}  (入口软链: {'+'.join(l for l, _ in links)})")

    n_fail = n_sync = n_skip = 0
    for name in selected:
        src = SRC_DIR / name
        errs, warns, info = inspect_vmap(src, registry)
        tag = name
        if info:
            tag += f"  (header={info['keys']}keys town={info['towns']} hero={info['heroes']} mon={info['monsters']})"
        if errs:
            n_fail += 1
            log("fail", f"{name} 源侧预检不通过, 拒绝同步:")
            for e in errs:
                log("fail", f"    - {e}")
            for w in warns:
                log("warn", f"    - {w}")
            continue
        for w in warns:
            log("warn", f"{name}: {w}")
        src_hash = sha256(src)
        for real, links in real_dirs.items():
            via = "+".join(l for l, _ in links)
            dst = real / name
            if dst.exists() and sha256(dst) == src_hash:
                n_skip += 1
                log("skip", f"{name} == {via}")
                continue
            if check_only:
                log("fail", f"{name} 与运行时不一致 (入口 {via}, {real}) (--check 模式不同步)")
                n_fail += 1
                continue
            if dry_run:
                log("sync", f"(dry-run) 将安装 {name} -> {real} (入口 {via})")
                continue
            old = sha256(dst)[:12] if dst.exists() else "无"
            new = atomic_install(src, dst)
            if sha256(dst) != src_hash:
                log("fail", f"{name} 写后复验失败: {real}")
                n_fail += 1
            else:
                log("sync", f"{name} {old} -> {new[:12]}  (入口 {via})")
                n_sync += 1

    # 漂移报告: 运行时里不在 MAPS 的 .vmap (退役/临时图); 按真实目录去重
    for real, links in real_dirs.items():
        via = "+".join(l for l, _ in links)
        extras = sorted(p.name for p in real.glob("*.vmap") if p.name not in maps)
        tmp_left = sorted(p.name for p in real.glob(".*.sync.tmp"))
        if tmp_left:
            log("warn", f"{real} 残留临时文件: {tmp_left}")
            n_fail += 1
        if extras:
            log("info", f"{via}: {len(extras)} 张非 MAPS 图 (退役图, 不同步不影响)")
            if purge and not check_only and not dry_run:
                for e in extras:
                    (real / e).unlink()
                    log("sync", f"purge 删除 {via}/{e}")
            elif purge and dry_run:
                log("info", f"(dry-run) 将 purge {len(extras)} 张 (入口 {via})")
            elif "--verbose" in flags:
                for e in extras:
                    log("info", f"    漂移[{via}]: {e}")

    print("-" * 70)
    log("info", f"汇总: 同步 {n_sync} 项, 已一致跳过 {n_skip} 项, 失败/不一致 {n_fail} 项")
    if n_fail:
        log("fail", "存在失败项 — 禁止启动/重启训练, 先修图再跑本脚本")
        return 1
    log("ok", "运行时地图目录与权威源一致, 可以训练 (原子替换不影响运行中 ep, 新局自动加载新版)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
