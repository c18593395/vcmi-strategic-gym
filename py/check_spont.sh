#!/bin/bash
# 判据② 自发经济精确判定: 解析最近 ep act 序列, 统计强制窗外 16-21
python3 - <<'EOF'
import re

lines = open('/mnt/d/Bigdata/hero3_fresh/train_loop.log', errors='ignore').readlines()
eps = []
for l in lines:
    m = re.search(r'ep_steps=(\d+) r=([0-9.-]+) act=\[([0-9, ]+)\] obs_nz=\d+ map=([^\s]+)', l)
    if m:
        eps.append((int(m.group(1)), float(m.group(2)), [int(x) for x in m.group(3).split(',')], m.group(4)))

# 最近 40 ep: 强制窗重建
# econ_force 24: step<24 全强制 16-21; 周期窗: (step-24)%40 < 4 强制
# visit 窗/START_HOME 序列无法精确重建 — 用保守口径: start_home 段(前8步)+econ24+周期窗 全算强制
def forced(step):
    if step < 8:   return True   # start_home 序列
    if step < 24:  return True   # econ_force 初始窗
    if (step - 24) % 40 < 4: return True  # 周期提醒窗
    return False

total_spont = 0
eps_with_spont = 0
detail = []
for steps, r, acts, m in eps[-40:]:
    s = 0
    for i, a in enumerate(acts[:steps]):
        if a in (16, 17, 18, 19, 20, 21) and not forced(i):
            s += 1
    total_spont += s
    if s > 0:
        eps_with_spont += 1
        detail.append((m.split('_adventure')[0] + m.split('.vmap')[0][-9:], steps, s, r))

print(f"最近 {min(40,len(eps))} ep: 自发经济动作总数 = {total_spont}, 有自发动作的 ep = {eps_with_spont}")
print("自发 >0 的局 (图尾/步数/自发次数/r):")
for d in detail[:15]:
    print(" ", d)
EOF
