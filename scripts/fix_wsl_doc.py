# -*- coding: utf-8 -*-
"""WSL踩坑点.md 止血脚本 (Plan A 第1、2步) — 带前置校验, 防误删
步骤1: 删除 1056-1088 行 —— 损坏的 #80 重复副本(行内代码被剥空, 与 1089+ 完好副本重复)
步骤2: 在 525 行(#57 MMAI_USER battle hang)前插入【内容损坏待补】注释
       (#57-#62 行内代码在历次脚本回写中被剥除, git 历史自 8c94d58 起即空, 无副本可恢复)
前置校验: 行数=1409, 1056/1089 均为 #80 头, 525 为 #57; 不符则中止不改动。
"""
import os, shutil, datetime

PATH = r"D:\Bigdata\hero3_fresh\docs\WSL踩坑点.md"
BACKUP = r"D:\Bigdata\hero3_fresh\backups\WSL踩坑点.md.bak_20260831_pre_bleed"

with open(PATH, "r", encoding="utf-8") as f:
    lines = f.readlines()

# ---- 前置校验 ----
errs = []
if len(lines) != 1409:
    errs.append(f"行数={len(lines)} 期望 1409 (疑似文件失同步, 中止)")
if not lines[1055].startswith("## 踩坑 #80"):
    errs.append(f"第1056行非 #80 头: {lines[1055][:40]!r}")
if not lines[1088].startswith("## 踩坑 #80"):
    errs.append(f"第1089行非 #80 头(完好副本): {lines[1088][:40]!r}")
if lines[524].strip() != "### 57. MMAI_USER battle hang — env 无 battle step 回调":
    errs.append(f"第525行非 #57 battle hang: {lines[524][:40]!r}")
# 损坏副本应有剥空行内代码(空反引号), 完好副本应有 build/bin/libmlclient.so
if "build/bin/libmlclient.so" in lines[1055]:
    errs.append("第1056行已是完好副本(未剥空), 删除风险!")
if "build/bin/libmlclient.so" not in lines[1088]:
    errs.append("第1089行非完好副本, 删除风险!")
if errs:
    print("❌ 校验失败, 未改动文件:")
    for e in errs:
        print("  -", e)
    raise SystemExit(1)

# ---- 行尾检测 ----
eol = "\r\n" if lines[0].endswith("\r\n") else "\n"

# ---- 备份 ----
os.makedirs(os.path.dirname(BACKUP), exist_ok=True)
shutil.copy2(PATH, BACKUP)
print(f"✅ 备份已写: {BACKUP}")

# ---- 步骤2 注释 ----
annotation = (
    "> \u26a0\ufe0f \u3010\u5185\u5bb9\u635f\u574f\u5f85\u8865\u3011\uff1a"
    "\u672c\u6761\u53ca\u4ee5\u4e0b #57\u2013#62 \u7684\u884c\u5185\u4ee3\u7801\u5728\u5386\u6b21\u811a\u672c\u56de\u5199\u4e2d\u88ab\u5250\u9664\uff0c"
    "git \u5386\u53f2\u81ea\u5f15\u5165\u63d0\u4ea4 8c94d58\uff082026-07-29\uff09\u8d77\u5373\u4e3a\u7a7a\uff0c\u4e14\u65e0\u5176\u4ed6\u526f\u672c\u53ef\u6062\u590d\u3002"
    "\u5177\u4f53\u7b26\u53f7\u7f3a\u5931\uff0c\u4ec5\u73b0\u8c61/\u6839\u56e0/\u7ed3\u8bba\u53ef\u8bfb\uff1b"
    "\u5982\u9700\u5b8c\u6574\u5f15\u7528\u8bf7\u6309\u8bb0\u5fc6\u6216\u6e90\u7801\u91cd\u65b0\u8865\u5f55\u3002"
    + eol
)

# ---- 执行 ----
out = []
for i, line in enumerate(lines, start=1):
    if 1056 <= i <= 1088:
        continue  # 步骤1: 跳过损坏副本
    if i == 525:
        out.append(annotation)  # 步骤2: 损坏区前置注释
    out.append(line)

with open(PATH, "w", encoding="utf-8") as f:
    f.writelines(out)

print(f"✅ 完成: 原行数={len(lines)} 新行数={len(out)} 删除={len(lines)-len(out)}")
