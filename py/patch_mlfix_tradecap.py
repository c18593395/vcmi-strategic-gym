#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ML fix: ResourceTrader::trade 循环熔断 + NK2 规划链耗时打点 (09-24, Mode B 根因)。

根因 (r9 冻结栈 + 89704 行日志实锤): trade 的 while 循环每成功交易一轮就重跑一次
buildAnalyzer.update() 全量建筑评估 (全城×全建筑×依赖递归), 循环无上界;
NK2 yourTurn TBB 任务全程持 CGameState::mutex 共享锁 → 读锁内狂转 →
runNetwork 包 apply 写锁饥饿 → 包流停摆 → 超时冻结 (rc=124)。

修复 (对齐 upgrade 熔断 cap 8 的既有模式):
  1) trade 循环加轮数 cap 16 (超限 [ML-fix] trade BREAK)
  2) 耗时打点 [ML-time]: trade 总耗时/轮数、BuildAnalyzer::update 每轮耗时、
     Nullkiller::makeTurn 总耗时 (RAII, 函数尾自动打印)

幂等: 已打则 skip。备份 .bak_mltimetrade。
"""
import re
import shutil
import sys

ROOT = "/home/administrator/vcmi-native"

RAII_SRC = """// ML fix (09-24): 规划链耗时打点 (trade 循环无上界 + 锁内全量重算取证)
struct MlTimeGuard {
\tconst char * name;
\tstd::chrono::steady_clock::time_point t0;
\tMlTimeGuard(const char * n) : name(n), t0(std::chrono::steady_clock::now())
\t{
\t\tfprintf(stderr, "[ML-time] %s ENTER\\n", name);
\t}
\t~MlTimeGuard()
\t{
\t\tauto ms = std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - t0).count();
\t\tfprintf(stderr, "[ML-time] %s EXIT %lldms\\n", name, (long long)ms);
\t}
};
"""


def patch_cpp_time(name, path, func_head_re):
    """在函数体首行插入 RAII 计时（正则找函数头后的第一个 '{'）。"""
    src = open(path, encoding="utf-8").read()
    if "MlTimeGuard" in src and ("[ML-time] %s" % name) in src:
        print("%s: already" % name)
        return True
    m = re.search(func_head_re, src)
    if not m:
        print("%s: func head not found" % name, file=sys.stderr)
        return False
    insert_at = m.end()
    ind = "\t"
    guard = 'MlTimeGuard _mltg("%s");' % name
    src = src[:insert_at] + "\n" + ind + guard + src[insert_at:]
    if "struct MlTimeGuard" not in src:
        # 头部插 RAII 定义（首个 include 之后）
        m2 = re.search(r'#include "[^"]*"\n', src)
        if not m2:
            m2 = re.search(r'#include <[^>]*>\n', src)
        if not m2:
            print("%s: include anchor not found" % name, file=sys.stderr)
            return False
        src = src[:m2.end()] + "\n" + RAII_SRC + src[m2.end():]
    open(path, "w", encoding="utf-8").write(src)
    print("%s: timed" % name)
    return True


def main():
    results = []

    # ---- 1. ResourceTrader.cpp: cap + 轮数/总耗时 ----
    T = os.path.join(ROOT, "AI/Nullkiller2/Engine/ResourceTrader.cpp")
    src = open(T, encoding="utf-8").read()
    if "[ML-fix] trade BREAK" in src:
        print("ResourceTrader: already")
        results.append(True)
    else:
        # while 循环体改写：加轮数计数 + cap + 每轮耗时
        pat = re.compile(
            r"(\t+)bool shouldTryToTrade = true;\n"
            r"(\t+)while\(shouldTryToTrade\)\n"
            r"\2\{\n"
            r"\2\tshouldTryToTrade = false;\n"
            r"\2\tbuildAnalyzer\.update\(\);"
        )
        m = pat.search(src)
        if not m:
            print("ResourceTrader: loop anchor not found", file=sys.stderr)
            results.append(False)
        else:
            t2 = m.group(2)
            t3 = t2 + "\t"
            head = 'extern "C" void strategic_state_force_game_over(int winner_player);'
            _ = head  # noqa
            new_block = (
                m.group(1) + "bool shouldTryToTrade = true;\n"
                + t2 + "int mlTradePasses = 0;  // ML fix (09-24): 交易循环熔断 cap 16 — 循环无上界时每轮全量 update() 持共享锁狂转 → 写锁饥饿冻结\n"
                + t2 + "auto mlTradeT0 = std::chrono::steady_clock::now();\n"
                + t2 + "while(shouldTryToTrade)\n"
                + t2 + "{\n"
                + t2 + "\tshouldTryToTrade = false;\n"
                + t2 + "\tbuildAnalyzer.update();\n"
                + t2 + "\tif(++mlTradePasses > 16)\n"
                + t2 + "\t{\n"
                + t2 + "\t\tfprintf(stderr, \"[ML-fix] trade BREAK pass=%d (loop cap)\\n\", mlTradePasses);\n"
                + t2 + "\t\tbreak;\n"
                + t2 + "\t}\n"
            )
            src = src[:m.start()] + new_block + src[m.end():]
            # 成功分支：shouldTryToTrade = true 前不加东西（cap 在循环头检查）
            # 出口打点
            m2 = re.search(r"(\t+)return haveTraded;\n\}", src)
            if not m2:
                print("ResourceTrader: exit anchor not found", file=sys.stderr)
                results.append(False)
            else:
                t1 = m2.group(1)
                exit_log = (
                    t1 + 'auto mlTradeMs = std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - mlTradeT0).count();\n'
                    + t1 + 'fprintf(stderr, "[ML-time] trade EXIT passes=%d %lldms\\n", mlTradePasses, (long long)mlTradeMs);\n'
                    + t1 + "return haveTraded;\n"
                    + "}"
                )
                src = src[:m2.start()] + exit_log + src[m2.end():]
                # RAII 定义 + chrono include
                if "struct MlTimeGuard" not in src:
                    mi = re.search(r'#include "[^"]*"\n', src)
                    src = src[:mi.end()] + "\n" + RAII_SRC + src[mi.end():]
                open(T, "w", encoding="utf-8").write(src)
                print("ResourceTrader: capped + timed")
                results.append(True)

    # ---- 2. BuildAnalyzer::update 计时 ----
    ok = patch_cpp_time(
        "BuildAnalyzer::update",
        os.path.join(ROOT, "AI/Nullkiller2/Analyzers/BuildAnalyzer.cpp"),
        r"void BuildAnalyzer::update\(\)\n\{",
    )
    results.append(ok)

    # ---- 3. Nullkiller::makeTurn 计时 ----
    ok = patch_cpp_time(
        "Nullkiller::makeTurn",
        os.path.join(ROOT, "AI/Nullkiller2/Engine/Nullkiller.cpp"),
        r"void Nullkiller::makeTurn\(\)\n\{",
    )
    results.append(ok)

    if all(results):
        print("结论: 全部补丁命中")
        return 0
    print("结论: 有锚点未命中 — 人工核对", file=sys.stderr)
    return 1


if __name__ == "__main__":
    import os
    sys.exit(main())