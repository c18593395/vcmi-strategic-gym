#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按内容标记把一个 unified diff 拆成两组 hunk，用于把工作区改动分成两个 commit 入库。

背景：`~/vcmi-native` 工作区里「上游同步」与「ML 集成」两类改动在同一批文件里交织，
直接 `git add -A` 会混成一个不可读的提交。本工具按标记把 hunk 分成两组：

    A 组 = 含 ML 标记的 hunk（ML 集成 / 打点 / fork 特性）
    B 组 = 其余 hunk（上游 API 同步等）

用法：
    python split_diff_hunks.py <输入.diff> --out-a a.patch --out-b b.patch \
        [--markers <正则>] [--stats]

输出的两个 patch 可直接 `git apply --cached <patch>` 分两次入库。
"""
import argparse
import re
import sys

DEFAULT_MARKERS = (
    r"ML-stk|ML-upg|ML-fix|ML fix|ML:|_mlUpgLoop|onNetworkThread|max_allowed_parallelism|"
    r"a1ea3f4d2d|strategic_state|ENABLE_ML|\[THREAD\]|\[DBG|\[BTL-DBG\]|\[SRV-DIAG\]|"
    r"tbb::global_control|g_adventure_allied_ai|ENGINE\b"
)


def parse_diff(text):
    """返回 [(file_header_lines, [hunk_lines, ...]), ...]"""
    files = []
    header, hunks, cur = [], [], None
    for line in text.splitlines(keepends=True):
        if line.startswith("diff --git "):
            if cur is not None:          # 收尾上一个文件的最后一个 hunk（否则会被静默丢弃）
                hunks.append(cur)
                cur = None
            if header:
                files.append((header, hunks))
            header, hunks, cur = [line], [], None
        elif line.startswith("@@"):
            if cur is not None:
                hunks.append(cur)
            cur = [line]
        elif cur is not None:
            cur.append(line)
        else:
            header.append(line)
    if cur is not None:
        hunks.append(cur)
    if header:
        files.append((header, hunks))
    return files


def main():
    ap = argparse.ArgumentParser(description="按标记拆分 unified diff 的 hunk")
    ap.add_argument("diff_file")
    ap.add_argument("--out-a", required=True, help="含标记的 hunk（ML 集成）")
    ap.add_argument("--out-b", required=True, help="其余 hunk（上游同步）")
    ap.add_argument("--markers", default=DEFAULT_MARKERS)
    ap.add_argument("--stats", action="store_true")
    args = ap.parse_args()

    rx = re.compile(args.markers)
    text = open(args.diff_file, encoding="utf-8", errors="ignore").read()
    files = parse_diff(text)

    a_files, b_files = [], []
    a_n = b_n = 0
    detail = []
    for header, hunks in files:
        a_h, b_h = [], []
        for h in hunks:
            body = "".join(l for l in h[1:] if l[:1] in "+-")
            (a_h if rx.search(body) else b_h).append(h)
        if a_h:
            a_files.append((header, a_h))
            a_n += len(a_h)
        if b_h:
            b_files.append((header, b_h))
            b_n += len(b_h)
        detail.append((header[0].split(" b/")[-1].strip(), len(a_h), len(b_h)))

    for path, group in ((args.out_a, a_files), (args.out_b, b_files)):
        with open(path, "w", encoding="utf-8") as fh:
            for header, hunks in group:
                fh.writelines(header)
                for h in hunks:
                    fh.writelines(h)

    if args.stats:
        print("%-52s %6s %6s" % ("file", "ML", "上游"))
        print("-" * 68)
        for name, na, nb in detail:
            print("%-52s %6d %6d" % (name, na, nb))
        print("-" * 68)
        print("A 组(ML 集成) hunk=%d  B 组(上游同步) hunk=%d" % (a_n, b_n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
