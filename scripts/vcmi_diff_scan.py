#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vcmi (smanolloff fork + fix_action_mapping)  vs  vcmi-official-20260829  三向差异扫描

用法:
  python scripts/vcmi_diff_scan.py [--out docs/vcmi_diff_report.md]

以 merge-base 为基准，分别统计官方侧 / 本地侧对 server、lib、AI 的改动，
输出:
  1) 双方都改的文件(潜在冲突)及各自改动量
  2) 仅官方改的文件(可直接移植候选)
  3) 仅本地改的文件(自研资产，勿动)
"""
import os
import subprocess
import sys
from collections import OrderedDict

ROOT = r"D:\Bigdata\hero3_fresh"
LOCAL = os.path.join(ROOT, "vcmi")
OFFICIAL = os.path.join(ROOT, "vcmi-official-20260829")
ALTERNATES = os.path.join(OFFICIAL, ".git", "objects")

MB = "5dac4318fb06feae442edd7ffb5215e1920ca3e7"   # merge-base
OFF = "8229b27486558a6969304376dc8035dca33dc5d4"  # official HEAD @2026-08-28

SCOPES = ["server", "lib", "AI"]


def git(*args):
    env = dict(os.environ)
    env["GIT_ALTERNATE_OBJECT_DIRECTORIES"] = ALTERNATES
    cmd = ["git", "-C", LOCAL] + list(args)
    r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=env)
    if r.returncode != 0:
        sys.stderr.write("GIT FAIL: %s\n%s\n" % (" ".join(args), r.stderr[:500]))
    return r.stdout


def numstat(a, b):
    """返回 {path: (add, del)}"""
    out = git("diff", "--numstat", a, b, "--", *SCOPES)
    res = OrderedDict()
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        try:
            add = int(parts[0])
        except ValueError:
            add = 0
        try:
            dele = int(parts[1])
        except ValueError:
            dele = 0
        res[parts[2]] = (add, dele)
    return res


def main():
    off = numstat(MB, OFF)
    loc = numstat(MB, "HEAD")

    both = [p for p in off if p in loc]
    off_only = [p for p in off if p not in loc]
    loc_only = [p for p in loc if p not in off]

    both.sort(key=lambda p: -(off[p][0] + off[p][1]))
    off_only.sort(key=lambda p: -(off[p][0] + off[p][1]))
    loc_only.sort(key=lambda p: -(loc[p][0] + loc[p][1]))

    lines = []
    A = lines.append
    A("# VCMI 本地 fork vs 官方 8229b274 差异扫描报告")
    A("")
    A("- 本地仓库：`%s`（分支 fix_action_mapping, HEAD 见下）" % LOCAL)
    A("- 官方仓库：`%s`" % OFFICIAL)
    A("- merge-base：`%s`" % MB)
    A("- 官方 HEAD：`%s`" % OFF)
    A("- 扫描范围：`%s`" % ", ".join(SCOPES))
    A("")
    head = git("log", "-1", "--format=%H %ad %s", "HEAD").strip()
    A("- 本地 HEAD：%s" % head)
    A("")
    A("## 0. 提交数")
    A("")
    A("| 方向 | 提交数 |")
    A("|---|---|")
    A("| 本地落后官方（官方有、本地无） | %s |" % git("rev-list", "--count", "HEAD.." + OFF).strip())
    A("| 本地领先官方（本地有、官方无） | %s |" % git("rev-list", "--count", OFF + "..HEAD").strip())
    A("")
    A("## 1. 总量")
    A("")
    A("| 侧 | 改动文件数 | 新增行 | 删除行 |")
    A("|---|---|---|---|")
    A("| 官方(5dac4318→8229b274) | %d | %d | %d |" % (len(off), sum(v[0] for v in off.values()), sum(v[1] for v in off.values())))
    A("| 本地(5dac4318→HEAD) | %d | %d | %d |" % (len(loc), sum(v[0] for v in loc.values()), sum(v[1] for v in loc.values())))
    A("")
    A("- 双方都改：%d 个文件" % len(both))
    A("- 仅官方改：%d 个文件" % len(off_only))
    A("- 仅本地改：%d 个文件" % len(loc_only))
    A("")

    A("## 2. 双方都改 = 潜在冲突文件（按官方改动量降序）")
    A("")
    A("| # | 文件 | 官方 +/- | 本地 +/- | 判读 |")
    A("|---|---|---|---|---|")
    for i, p in enumerate(both, 1):
        oa, ob = off[p]
        la, lb = loc[p]
        if la + lb == 0:
            verdict = "本地几乎未动 → 可直接取官方"
        elif oa + ob <= 4 and (la + lb) >= 8:
            verdict = "官方微改 → 手工合入"
        elif (oa + ob) >= 40:
            verdict = "官方大改 → 重点评审"
        else:
            verdict = "双方均有实质改动 → 逐hunk评审"
        A("| %d | `%s` | +%d/-%d | +%d/-%d | %s |" % (i, p, oa, ob, la, lb, verdict))
    A("")

    A("## 3. 仅官方改 = 可移植候选 Top60（本地未触碰，合入零冲突）")
    A("")
    A("| # | 文件 | 新增 | 删除 |")
    A("|---|---|---|---|")
    for i, p in enumerate(off_only[:60], 1):
        A("| %d | `%s` | +%d | -%d |" % (i, p, off[p][0], off[p][1]))
    A("")

    A("## 4. 仅本地改 = 自研资产 Top40（官方无此文件/未改，勿覆盖）")
    A("")
    A("| # | 文件 | 新增 | 删除 |")
    A("|---|---|---|---|")
    for i, p in enumerate(loc_only[:40], 1):
        A("| %d | `%s` | +%d | -%d |" % (i, p, loc[p][0], loc[p][1]))
    A("")

    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None
    text = "\n".join(lines)
    if out:
        path = os.path.join(ROOT, out)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        print("WROTE %s (%d bytes)" % (path, os.path.getsize(path)))
    else:
        print(text)


if __name__ == "__main__":
    main()
