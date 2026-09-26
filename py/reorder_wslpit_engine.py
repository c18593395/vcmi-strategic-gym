#!/usr/bin/env python3
"""重排 WSL踩坑点-引擎-VCMI-API.md：条目按编号升序 + 格式统一 + 空行压缩"""
import re
from pathlib import Path
from collections import Counter

SRC = Path(r"d:\Bigdata\hero3_fresh\docs\WSL踩坑点-引擎-VCMI-API.md")

text = SRC.read_text(encoding="utf-8")
lines = text.split("\n")

# ========== 识别条目起始行 ==========
def get_entry_key(line):
    """返回排序键 (int)，非条目返回 None"""
    ls = line.strip()
    # ### 修复链
    if ls == "### 修复链":
        return 0
    # ### 当前工作组合 / ### 已知剩余问题 → 作为修复链附属，key=0
    if ls.startswith("### 当前工作组合") or ls.startswith("### 已知剩余问题"):
        return 0
    # ### 待归档新增 → 节标题，key=0
    if ls.startswith("### 待归档新增"):
        return 0
    # ### N. xxx
    m = re.match(r"^###\s+(\d+)\.", ls)
    if m:
        return int(m.group(1))
    # ## 踩坑 #N:
    m = re.match(r"^##\s+踩坑\s+#(\d+):", ls)
    if m:
        return int(m.group(1))
    # ### #N:
    m = re.match(r"^###\s+#(\d+):", ls)
    if m:
        return int(m.group(1))
    # #### #N / #### ~~#N~~
    m = re.match(r"^####\s+(~~)?#(\d+)", ls)
    if m:
        return int(m.group(2))
    return None

# 找到所有条目起始行
entry_starts = []
i = 0
while i < len(lines):
    k = get_entry_key(lines[i])
    if k is not None:
        entry_starts.append(i)
        # 跳过整个条目块（到下一个条目起始）
        j = i + 1
        while j < len(lines):
            if get_entry_key(lines[j]) is not None:
                break
            j += 1
        i = j
    else:
        i += 1

first_entry = entry_starts[0]
header = lines[:first_entry]
while header and header[-1].strip() == "":
    header.pop()

# 提取块
blocks = []
for idx, s in enumerate(entry_starts):
    e = entry_starts[idx + 1] if idx + 1 < len(entry_starts) else len(lines)
    blocks.append([s, e, None, idx])

# 为"修复链附属"行（当前工作组合、已知剩余问题）合并到修复链块
# 处理：这些行属于 key=0 块，已经在 entry_starts 中作为独立条目
# 但逻辑上它们是"修复链"的附属子节，排序后应紧跟"修复链"
# 由于都是 key=0，稳定排序会保持原顺序，所以没问题

for i in range(len(blocks)):
    blocks[i][2] = get_entry_key(lines[blocks[i][0]])

# 稳定排序：key 升序，同 key 保持文件原顺序
blocks.sort(key=lambda x: (x[2], x[3]))

# 各编号出现次数（仅计 key>=1 的条目）
key_counts = Counter(b[2] for b in blocks if b[2] >= 1)
key_occurrence = {}

def display_num(key, occ):
    if key_counts[key] > 1:
        suffixes = ["", "b", "c", "d", "e", "f", "g"]
        return f"{key}{suffixes[occ]}"
    return str(key)

out_parts = ["\n".join(header)]

for s, e, key, _order in blocks:
    block_lines = lines[s:e]
    # 压缩内部连续空行
    compressed = []
    prev_blank = False
    for ln in block_lines:
        blank = ln.strip() == ""
        if blank and prev_blank:
            continue
        compressed.append(ln)
        prev_blank = blank
    while compressed and compressed[-1].strip() == "":
        compressed.pop()

    title = compressed[0].strip()
    body = compressed[1:]

    if key == 0:
        # 非编号条目，保持原样
        new_title = title
    else:
        occ = key_occurrence.get(key, 0)
        key_occurrence[key] = occ + 1
        dn = display_num(key, occ)

        if "~~" in title and title.startswith("####"):
            # #### ~~#300~~ xxx → ### 300. (已证伪) xxx（保留删除线）
            rest = re.sub(r"^####\s+~~#?\d+~~\s*", "", title)
            new_title = f"### {dn}. (已证伪) ~~{rest.strip()}~~"
        elif title.startswith("## 踩坑"):
            rest = re.sub(r"^##\s+踩坑\s+#\d+:\s*", "", title)
            new_title = f"### {dn}. {rest}"
        elif re.match(r"^###\s+#\d+:", title):
            rest = re.match(r"^###\s+#\d+:\s*(.*)$", title).group(1)
            new_title = f"### {dn}. {rest}"
        elif re.match(r"^####\s+#\d+", title):
            rest = re.match(r"^####\s+#\d+\s*(.*)$", title).group(1)
            new_title = f"### {dn}. {rest}"
        else:
            # ### N. xxx — 去掉原有编号+点
            m2 = re.match(r"^###\s+\d+(?!\d)\.?\s*(.*)$", title)
            rest = m2.group(1).strip() if m2 else title
            new_title = f"### {dn}. {rest}"

    out_parts.append(new_title + ("\n" + "\n".join(body) if body else ""))

out = "\n\n".join(out_parts)
out = re.sub(r"\n{3,}", "\n\n", out)
out = out.rstrip() + "\n"

SRC.write_text(out, encoding="utf-8")
print(f"写入完成: {SRC}, 共 {len(out.splitlines())} 行")
print(f"共 {len(blocks)} 个条目")

# 打印新标题列表
for ln in out.splitlines():
    if re.match(r"^###\s", ln):
        print(" ", ln[:100])
