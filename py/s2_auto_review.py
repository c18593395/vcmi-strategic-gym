#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S2 撤梯子自动收口监控 (Windows 侧后台, 不受 WSL 重启影响):
每 5 分钟检查 S2 窗完成局数, >=40 局自动执行收口复查 (4 判据 + S2 判据),
报告写 D:/Bigdata/hero3_fresh/s2_review_report.txt, FAIL 则继续攒局 (上限 80 局二次复查)。
启动: Start-Process python -ArgumentList "D:/Bigdata/hero3_fresh/py/s2_auto_review.py" -WindowStyle Hidden
"""
import re
import statistics
import time

LOG = r"D:\Bigdata\hero3_fresh\train_loop.log"
REPORT = r"D:\Bigdata\hero3_fresh\s2_review_report.txt"
S1 = {"r_mean": 10.8, "recruited_per_ep": 17.5, "build2_per_ep": 0.8}  # 恢复窗 66 局基线
THRESH_EP, MAX_EP = 40, 80
CHECK_INTERVAL = 300


def window_lines():
    lines = open(LOG, errors="replace").readlines()
    start = max(i for i, l in enumerate(lines, 1) if "WIN1_BATCH" in l)
    return lines[start:], start


def review():
    seg, start = window_lines()
    j = "".join(seg)
    eps = re.findall(r"\[EP_TIME\] map=(\S+) steps=(\d+) secs=(\d+) r=(-?[\d.]+) err=(\w+)", j)
    n_ep = len(eps)
    rep = [f"S2 收口复查报告  (生成于 {time.strftime('%m-%d %H:%M')}, 窗起点 L{start})",
           f"完成局数: {n_ep} (触发阈值 {THRESH_EP})"]
    if n_ep < THRESH_EP:
        return None, "\n".join(rep + [f"局数不足, 继续攒局..."])
    rs_all = [float(e[3]) for e in eps]
    nd = [e for e in eps if not e[0].endswith("_duel.vmap")]
    rs_nd = [float(e[3]) for e in nd]
    err_eps = [e for e in eps if e[4] != "no"]
    slain = len(re.findall(r"\[BHERO_SLAIN\]|slain=\[[1-9]", j))
    n_recruited = len(re.findall(r"\[RECRUITED\]", j))
    n_build2 = len(re.findall(r"\[ECON\] build2 \(act20\)", j)) + len(re.findall(r"first BUILD_2", j))
    recruited_pe = n_recruited / max(1, n_ep)
    build2_pe = n_build2 / max(1, n_ep)
    r_nd_mean = statistics.mean(rs_nd) if rs_nd else 0.0
    dead_nd = sum(1 for r in rs_nd if r <= -100)

    checks = []
    c1 = len(err_eps) == 0
    checks.append(("① 新口径不炸 (err局=0)", c1, f"err局 {len(err_eps)}/{n_ep}"))
    c2 = slain > 0 or any(e[0].endswith(".vmap") and "hero" in j.lower() for e in []) or slain > 0
    c2 = slain > 0
    checks.append(("② 真实战斗/击杀记账 (slain非零)", c2, f"slain证据 {slain}"))
    c4_nd = dead_nd == 0
    checks.append(("④ 非duel死亡局=0", c4_nd, f"非duel死亡局 {dead_nd}/{len(rs_nd)}"))

    r_pass = r_nd_mean >= S1["r_mean"] * 0.8
    checks.append(("S2-a 非duel avg_r 跌<20%", r_pass, f"非duel mean {r_nd_mean:.1f} vs S1 {S1['r_mean']}"))
    rec_pass = recruited_pe >= S1["recruited_per_ep"] * 0.8
    checks.append(("S2-b 招兵频率不塌(>=0.8x)", rec_pass, f"{recruited_pe:.1f}/局 vs S1 {S1['recruited_per_ep']}/局"))
    bld_pass = build2_pe >= S1["build2_per_ep"] * 0.8
    checks.append(("S2-c 建设频率不塌(>=0.8x)", bld_pass, f"{build2_pe:.2f}/局 vs S1 {S1['build2_per_ep']}/局"))

    all_pass = all(v for _, v, _ in checks)
    rep.append("")
    rep.append("判据明细:")
    for name, ok, detail in checks:
        rep.append(f"  {'PASS' if ok else 'FAIL'}  {name}  ({detail})")
    rep.append("")
    rep.append(f"==> S2 收口判定: {'✅ 全部 PASS, 可收口' if all_pass else '❌ 存在 FAIL, 继续攒局或人工分析'}")
    rep.append(f"duel 局 {n_ep - len(nd)} 局已剔除底噪口径; duel r 列表: "
               f"{[float(e[3]) for e in eps if e[0].endswith('_duel.vmap')]}")
    return all_pass, "\n".join(rep)


def main():
    reviewed = False
    while True:
        n_ep_line = ""
        try:
            seg, _ = window_lines()
            n_ep = sum(1 for l in seg if "[EP_TIME]" in l)
            n_ep_line = f"局数 {n_ep}"
        except Exception as e:
            n_ep_line = f"读日志异常 {e}"
        if not reviewed and n_ep >= THRESH_EP:
            ok, rep = review()
            with open(REPORT, "w", encoding="utf-8") as f:
                f.write(rep + "\n")
            reviewed = True
            if ok:
                break  # 收口达成, 监控结束
            # FAIL → 等到 MAX_EP 再复查一次
        if not reviewed and n_ep >= MAX_EP:
            ok, rep = review()
            with open(REPORT, "w", encoding="utf-8") as f:
                f.write(rep + "\n(达 MAX_EP 上限, 监控结束)\n")
            break
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
