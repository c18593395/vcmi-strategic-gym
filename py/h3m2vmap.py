#!/usr/bin/env python3
"""
h3m2vmap.py — 官方 H3M 地图 → VMAP 转换工具统一入口 (2026-09-14 整理版)

背景:
  之前 H3M/VMAP 相关工具散落 (tools/h3m2vmap/*.cpp + py/h3m_batch_to_vmap.py +
  py/_check_h3m_header.py + py/hexdump_h3m.py + py/scan_h3m_versions.py +
  py/pick_flat_h3m.py + scripts/h3m_tool.py + py/run_*.sh). 本文件把这些入口
  收敛成一个 CLI, 子命令分派到已实现的组件. 旧脚本已归档到 py/_deprecated_h3m/.

依赖:
  * Windows 侧可直接跑的子命令: header / hexdump / verify / select
  * 需要 WSL + 引擎的: check / convert / batch / reverse (reverse 需 scripts/h3m_tool.py)
    通过 `wsl bash -lc '...'` 调用, 无需常驻进程

子命令一览:
  check     引擎级验证: 调用 tools/h3m2vmap --check-h3m
  convert   单张转换: h3m → vmap (调用 tools/h3m2vmap --save)
  batch     批量转换 (内联实现, 报告落 maps/h3m_to_vmap/_report.json)
  verify    纯 Python 校验 vmap zip: header.json / objects.json / terrain
  header    快速看 h3m header (magic/name/w/h/nPlayers)
  hexdump   gzip 解压后头部 hexdump
  select    官方图选图 (单层/无地下/无需造船): 转发 pick_flat_h3m.py
  reverse   vmap → h3m 反向: 转发 py/vmap2h3m.py

用法示例:
  python py/h3m2vmap.py header "D:\\...\\King of Pain.h3m"
  python py/h3m2vmap.py check "data/Maps/For Sale.h3m"
  python py/h3m2vmap.py convert "data/Maps/For Sale.h3m" out.vmap
  python py/h3m2vmap.py batch --limit 20 --resume
  python py/h3m2vmap.py verify out.vmap
  python py/h3m2vmap.py select --maps-dir /mnt/d/Bigdata/hero3_fresh/vcmi/data/Maps
  python py/h3m2vmap.py reverse in.vmap out.h3m
"""
import argparse
import gzip
import json
import os
import re
import struct
import subprocess
import sys
import time
import zipfile
from datetime import datetime
from pathlib import Path

# ── 默认路径 ──────────────────────────────────────────────────────────────────
ROOT_WIN = Path(r"D:\Bigdata\hero3_fresh")
ROOT_WSL = Path("/mnt/d/Bigdata/hero3_fresh")
ENGINE_BIN = os.environ.get("ENGINE_BIN", "/home/administrator/vcmi-native/rel/bin")
ENGINE_DATA = os.path.join(ENGINE_BIN, "data", "Maps")
CONVERTER = os.environ.get("CONVERTER", "/home/administrator/vcmi-native/tools/h3m2vmap/build/h3m2vmap")
BATCH_OUT = os.environ.get("BATCH_OUT", "/mnt/d/Bigdata/hero3_fresh/maps/h3m_to_vmap")
BATCH_REPORT = os.path.join(BATCH_OUT, "_report.json")
BATCH_LOG = os.path.join(BATCH_OUT, "_batch.log")


# ── WSL 调用封装 ──────────────────────────────────────────────────────────────
def run_wsl(args, timeout=300, cwd=None):
    """args 为 WSL bash 内的命令数组; 用 bash -lc 拼装后交给 wsl.exe"""
    cmd = ["wsl", "bash", "-lc", " ".join(_quote(a) for a in args)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd)
        return r.returncode, r.stdout or "", r.stderr or ""
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"
    except FileNotFoundError:
        return -2, "", "wsl.exe not found"


def _quote(s):
    if not s or any(c in s for c in " \t\n\"'\\"):
        return "'" + s.replace("'", "'\\''") + "'"
    return s


# ── 共用校验函数 (verify) ──────────────────────────────────────────────────────
def _strip_c_comments(text):
    """VCMI saveMap 输出 vmap JSON 带 `// game` 标记, 非合法 JSON"""
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


def _loads_permissive(s):
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return json.loads(_strip_c_comments(s))


def verify_vmap(path):
    """返回 dict, 有 error 键即失败"""
    info = {"path": str(path), "verified_at": datetime.now().isoformat(timespec="seconds")}
    if not os.path.isfile(path):
        info["error"] = "file not found"
        return info
    info["file_size"] = os.path.getsize(path)
    if info["file_size"] < 100:
        info["error"] = "empty output file"
        return info
    try:
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            info["zip_entries"] = sorted(names)
            required = ["header.json", "objects.json"]
            for r in required:
                if r not in names:
                    info["error"] = f"missing {r}"
                    return info
            h = _loads_permissive(z.read("header.json").decode())
            info["name"] = h.get("name")
            info["has_underground"] = "underground" in (h.get("mapLevels") or {})
            info["players"] = list((h.get("players") or {}).keys())
            mp = ((h.get("mapLevels") or {}).get("surface") or {})
            info["width"] = mp.get("width")
            info["height"] = mp.get("height")
            if "players" in h:
                # players 是 dict 时 keys 是颜色; 检查 owner/identifier
                pl = h["players"]
                if isinstance(pl, dict):
                    info["players_owner"] = {k: (v.get("owner") if isinstance(v, dict) else None)
                                             for k, v in list(pl.items())[:8]}
                else:
                    info["players_count"] = len(pl)
            objs = _loads_permissive(z.read("objects.json").decode())
            info["objects"] = len(objs) if hasattr(objs, "__len__") else "n/a"
            terrain_files = [n for n in names if re.match(r"surface_?terrain.*\.json", n)
                             or n.startswith("terrain_")]
            info["terrain_files"] = terrain_files
            if not terrain_files:
                info["error"] = "no terrain_*.json"
                return info
    except Exception as e:
        info["error"] = f"validate_exception: {e}"
        return info
    return info


# ── header / hexdump (纯 Python, Windows 原生) ────────────────────────────────
def cmd_header(args):
    p = Path(args.file)
    if not p.exists():
        print(f"ERROR: not found: {p}", file=sys.stderr)
        return 2
    data = p.read_bytes()
    if data[:1] != b"H":
        print(f"ERROR: not H3M magic (first byte={data[:1]!r}), 需要 'H'=0x48", file=sys.stderr)
        return 2
    name = data[1:25].rstrip(b"\x00").decode("latin-1", "replace")
    desc = data[25:85].rstrip(b"\x00").decode("latin-1", "replace")
    md = data[85:145].rstrip(b"\x00").decode("latin-1", "replace")
    w, h, d, npl = struct.unpack("<HHHH", data[145:153])
    print(f"file   : {p}")
    print(f"size   : {len(data)} B")
    print(f"name   : {name}")
    print(f"desc   : {desc}")
    print(f"mapDesc: {md}")
    print(f"w={w} h={h} d={d} nPlayers={npl}")
    if args.players and npl > 0 and npl <= 8:
        offs = 153
        for i in range(npl):
            entry = data[offs:offs + 12]
            offs += 12
            print(f"player[{i}]: {entry.hex()} = {list(entry)}")
    return 0


def cmd_hexdump(args):
    p = Path(args.file)
    if not p.exists():
        print(f"ERROR: not found: {p}", file=sys.stderr)
        return 2
    raw = gzip.decompress(p.read_bytes())
    print(f"raw len: {len(raw)}")
    limit = min(args.bytes, len(raw))
    for off in range(0, limit, 16):
        seg = raw[off:off + 16]
        hexs = " ".join(f"{b:02x}" for b in seg)
        asc = "".join(chr(b) if 32 <= b < 127 else "." for b in seg)
        print(f"{off:4d}: {hexs:<48s} {asc}")
    return 0


# ── check / convert / batch (WSL + 引擎) ──────────────────────────────────────
def _check_converter_exists():
    rc, out, _ = run_wsl(["test", "-x", CONVERTER, "&&", "echo", "OK"], timeout=15)
    return rc == 0 and "OK" in out


def cmd_check(args):
    if not _check_converter_exists():
        print(f"ERROR: converter not found: {CONVERTER} (先跑 run_save_h3m_to_vmap.sh 或手动 build)", file=sys.stderr)
        return 2
    rc, out, err = run_wsl([CONVERTER, "--check-h3m", args.file], timeout=args.timeout)
    if out:
        print(out, end="" if out.endswith("\n") else "\n")
    if err:
        print("[stderr]", err, file=sys.stderr)
    return rc


def cmd_convert(args):
    if not _check_converter_exists():
        print(f"ERROR: converter not found: {CONVERTER}", file=sys.stderr)
        return 2
    rc, out, err = run_wsl([CONVERTER, "--save", args.in_h3m, args.out_vmap], timeout=args.timeout)
    if out:
        print(out, end="" if out.endswith("\n") else "\n")
    if err:
        print("[stderr]", err, file=sys.stderr)
    return rc


def _discover_h3m():
    rc, out, _ = run_wsl(["bash", "-lc", f"ls -1 {ENGINE_DATA}/*.h3m"], timeout=30)
    if rc != 0:
        return []
    return [ln for ln in out.splitlines() if ln.endswith(".h3m")]


def _log(msg):
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    try:
        os.makedirs(BATCH_OUT, exist_ok=True)
        with open(BATCH_LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def cmd_batch(args):
    """内联批量转换, 报告落 maps/h3m_to_vmap/_report.json"""
    if not _check_converter_exists():
        print(f"ERROR: converter not found: {CONVERTER}", file=sys.stderr)
        return 2

    os.makedirs(BATCH_OUT, exist_ok=True)
    existing = {}
    if os.path.isfile(BATCH_REPORT):
        try:
            with open(BATCH_REPORT, encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = {}

    files = _discover_h3m()
    if args.only:
        files = [f for f in files if args.only.lower() in os.path.basename(f).lower()]
    if args.limit:
        files = files[:args.limit]

    _log(f"=== 发现 {len(files)} 张 H3M (共 {len(_discover_h3m())} 张) ===")
    _log(f"输出: {BATCH_OUT}  报告: {BATCH_REPORT}")

    stats = {"ok": 0, "fail": 0, "skip": 0, "warn": 0}
    fails = []
    total = len(files)
    for i, src in enumerate(files, 1):
        base = os.path.basename(src)
        out_name = base[:-4] + ".vmap"
        out_vmap = os.path.join(BATCH_OUT, out_name)

        if args.resume and os.path.isfile(out_vmap) and os.path.getsize(out_vmap) > 100:
            prev = existing.get(base, {})
            if prev.get("status") in ("ok", "warn_mismatch"):
                stats["skip"] += 1
                _log(f"[{i}/{total}] SKIP (resume) {base} (prev={prev.get('status')})")
                continue

        t0 = time.time()
        rc, out, err = run_wsl([CONVERTER, "--save", src, out_vmap], timeout=args.timeout)
        dt = time.time() - t0

        entry = {"input": base, "output": out_name, "exit_code": rc,
                 "duration_s": round(dt, 2)}

        if rc == 0 and os.path.isfile(out_vmap) and os.path.getsize(out_vmap) > 100:
            info = verify_vmap(out_vmap)
            entry.update({k: v for k, v in info.items() if k != "path"})
            # roundtrip 从 C++ stdout 里解析
            if "ROUNDTRIP OK" in out:
                rt = "ok"
            elif "ROUNDTRIP MISMATCH" in out:
                m = re.search(r"in=(\d+) out=(\d+)", out)
                rt = f"mismatch(in={m.group(1)} out={m.group(2)})" if m else "mismatch"
            else:
                rt = "unknown"
            entry["roundtrip"] = rt
            if "error" in info:
                entry["status"] = "validated_fail"
                fails.append((base, info["error"]))
                stats["fail"] += 1
                _log(f"[{i}/{total}] FAIL validate {base} ({dt:.1f}s): {info['error']}")
            elif rt == "ok":
                entry["status"] = "ok"
                stats["ok"] += 1
                _log(f"[{i}/{total}] OK {base} → {out_name} "
                     f"({entry.get('width')}x{entry.get('height')}, "
                     f"obj={entry.get('objects')}, players={entry.get('players')}, "
                     f"{dt:.1f}s)")
            else:
                entry["status"] = "warn_mismatch"
                stats["warn"] += 1
                _log(f"[{i}/{total}] WARN {base} → {out_name} "
                     f"({entry.get('width')}x{entry.get('height')}, roundtrip={rt}, {dt:.1f}s)")
        else:
            entry["status"] = "convert_fail"
            entry["stderr_tail"] = err[-300:]
            fails.append((base, err[-200:]))
            stats["fail"] += 1
            _log(f"[{i}/{total}] FAIL convert {base} rc={rc} ({dt:.1f}s): {err[-150:]}")

        existing[base] = entry
        with open(BATCH_REPORT, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)

    _log(f"=== 完成 ok={stats['ok']} fail={stats['fail']} skip={stats['skip']} warn={stats['warn']} ===")
    if fails:
        _log(f"=== 失败清单 ({len(fails)}) ===")
        for n, w in fails:
            _log(f"  - {n}: {w[:200]}")
    return 0 if not fails else 1


# ── verify ─────────────────────────────────────────────────────────────────────
def cmd_verify(args):
    info = verify_vmap(args.vmap)
    if args.json:
        print(json.dumps(info, indent=2, ensure_ascii=False))
        return 0 if "error" not in info else 1
    print(f"path   : {info['path']}")
    print(f"size   : {info.get('file_size', 0)} B")
    print(f"name   : {info.get('name')}")
    print(f"dims   : {info.get('width')} x {info.get('height')}")
    print(f"players: {info.get('players')}")
    if info.get("players_owner"):
        for k, v in info["players_owner"].items():
            print(f"    {k}: owner={v}")
    print(f"obj    : {info.get('objects')}")
    print(f"under  : {info.get('has_underground')}")
    print(f"terrain: {info.get('terrain_files')}")
    if "error" in info:
        print(f"ERROR  : {info['error']}", file=sys.stderr)
        return 1
    print("OK")
    return 0


# ── select / reverse 转发 ──────────────────────────────────────────────────────
def _win_to_wsl(p):
    """D:\\... → /mnt/d/..."""
    p = os.path.abspath(p)
    m = re.match(r"([A-Za-z]):[\\/](.*)", p)
    if m:
        return f"/mnt/{m.group(1).lower()}/{m.group(2).replace(chr(92), '/')}"
    return p


def cmd_select(args):
    """转发 py/pick_flat_h3m.py"""
    script = str(ROOT_WIN / "py" / "pick_flat_h3m.py")
    if not os.path.isfile(script):
        print(f"ERROR: script not found: {script}", file=sys.stderr)
        return 2
    maps_dir = args.maps_dir or ENGINE_DATA
    maps_dir = _win_to_wsl(maps_dir)
    r = subprocess.run(["python3", "/mnt/d/Bigdata/hero3_fresh/py/pick_flat_h3m.py", maps_dir],
                       capture_output=True, text=True,
                       stdin=subprocess.DEVNULL,
                       timeout=args.timeout)
    # 直接转发 stdout/stderr
    if r.stdout:
        print(r.stdout, end="")
    if r.stderr:
        print(r.stderr, end="", file=sys.stderr)
    return r.returncode


def cmd_reverse(args):
    """转发 py/vmap2h3m.py"""
    script = "/mnt/d/Bigdata/hero3_fresh/py/vmap2h3m.py"
    cmd = ["python3", script, args.in_vmap, args.out_h3m]
    if args.engine_root:
        cmd += ["--engine-root", _win_to_wsl(args.engine_root)]
    if args.name:
        cmd += ["--name", args.name]
    if args.desc:
        cmd += ["--desc", args.desc]
    if args.report:
        cmd += ["--report", _win_to_wsl(args.report)]
    for d in (args.donor or []):
        cmd += ["--donor", _win_to_wsl(d)]
    return _run_wsl_print(cmd, args.timeout)


def _run_wsl_print(cmd_list, timeout):
    """通用: 调 WSL 命令, 打印 stdout/stderr, 返回 rc"""
    rc, out, err = run_wsl(cmd_list, timeout=timeout)
    if out:
        print(out, end="" if out.endswith("\n") else "\n")
    if err:
        print("[stderr]", err, file=sys.stderr)
    return rc


# ── main ───────────────────────────────────────────────────────────────────────
def build_parser():
    p = argparse.ArgumentParser(
        prog="h3m2vmap.py",
        description="官方 H3M 地图 → VMAP 转换工具统一入口 (2026-09-14 整理版)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = p.add_subparsers(dest="cmd", required=True, metavar="<subcommand>")

    c = sub.add_parser("check", help="引擎级验证 h3m (调 tools/h3m2vmap --check-h3m)")
    c.add_argument("file", help="h3m 文件路径 (WSL 视角)")
    c.add_argument("--timeout", type=int, default=120)
    c.set_defaults(func=cmd_check)

    c = sub.add_parser("convert", help="单张转换 h3m → vmap (调 tools/h3m2vmap --save)")
    c.add_argument("in_h3m", help="输入 h3m (WSL 视角)")
    c.add_argument("out_vmap", help="输出 vmap (WSL 视角)")
    c.add_argument("--timeout", type=int, default=180)
    c.set_defaults(func=cmd_convert)

    c = sub.add_parser("batch", help="批量转换 + 报告")
    c.add_argument("--limit", type=int, default=0, help="只处理前 N 张 (0=全部)")
    c.add_argument("--resume", action="store_true", help="跳过已成功转换的")
    c.add_argument("--only", type=str, default="", help="只处理名称包含该关键词的图")
    c.add_argument("--timeout", type=int, default=300, help="单张超时秒")
    c.set_defaults(func=cmd_batch)

    c = sub.add_parser("verify", help="校验 vmap zip 结构 (纯 Python)")
    c.add_argument("vmap", help="vmap 文件 (Windows 或 WSL 路径均可)")
    c.add_argument("--json", action="store_true", help="JSON 输出")
    c.set_defaults(func=cmd_verify)

    c = sub.add_parser("header", help="快速看 h3m header (纯 Python)")
    c.add_argument("file", help="h3m 文件")
    c.add_argument("--players", action="store_true", help="同时输出前 12 字节/玩家段")
    c.set_defaults(func=cmd_header)

    c = sub.add_parser("hexdump", help="gzip 解压后 hexdump (纯 Python)")
    c.add_argument("file", help="h3m 文件")
    c.add_argument("--bytes", type=int, default=96, help="前多少字节 (默认 96)")
    c.set_defaults(func=cmd_hexdump)

    c = sub.add_parser("select", help="选图 (单层/无地下/无需造船), 转发 pick_flat_h3m.py")
    c.add_argument("--maps-dir", default="", help="地图目录 (默认 ENGINE_DATA)")
    c.add_argument("--timeout", type=int, default=600)
    c.set_defaults(func=cmd_select)

    c = sub.add_parser("reverse", help="反向: vmap → h3m (转发 py/vmap2h3m.py)")
    c.add_argument("in_vmap", help="输入 vmap")
    c.add_argument("out_h3m", help="输出 h3m")
    c.add_argument("--engine-root", default="", help="引擎根 (含 mods/ 目录)")
    c.add_argument("--donor", action="append", help="donor h3m (可多次)")
    c.add_argument("--name", default="", help="输出图名")
    c.add_argument("--desc", default="", help="输出图描述")
    c.add_argument("--report", default="", help="审计报告 json 路径")
    c.add_argument("--timeout", type=int, default=600)
    c.set_defaults(func=cmd_reverse)

    return p


def main(argv=None):
    ap = build_parser()
    args = ap.parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
