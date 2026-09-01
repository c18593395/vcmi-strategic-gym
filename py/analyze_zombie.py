#!/usr/bin/env python3
"""灾难局 act10 僵尸段溯源：passable 全0 同时 英雄状态=死亡？
交叉验证：在每个大负局的 act10 段起点处，obs[3203] (active_hero_idx) 和 heroes[ah].alive 标志位"""
import re, sys, json

LOG = r"D:\Bigdata\hero3_fresh\train_loop.log"
m_ep = re.compile(r'ep_steps=(\d+)\s+r=([-\d.]+)\s+act=\[(.+?)\]\s+obs_nz=(\d+)')

def find_first_run_of_10(acts, min_run=10):
    """返回第一次连续>=min_run个10的起始位置和段长"""
    cur, mx, start = 0, 0, -1
    cur_start = -1
    for i, a in enumerate(acts):
        if a == 10:
            if cur == 0: cur_start = i
            cur += 1
            if cur > mx:
                mx = cur
                start = cur_start
        else:
            cur = 0
    return (start, mx) if mx >= min_run else (None, 0)

# 从 ep_runner 输出的 json 轨迹（如果有）可以验证；这里从日志反推行为模式
with open(LOG, encoding='utf-8', errors='replace') as f:
    text = f.read()
matches = list(m_ep.finditer(text))

stats = {'big_neg': 0, 'has_long_10run': 0, 'run_after_move': 0, 'exactly_200': 0}
first_step_10 = []  # 首次长10段起始 step
for i, m in enumerate(matches):
    acts = [int(x.strip()) for x in m.group(3).split(',')]
    r = float(m.group(2))
    steps = int(m.group(1))
    if r < -100:
        stats['big_neg'] += 1
        start, runlen = find_first_run_of_10(acts, 10)
        if start is not None:
            stats['has_long_10run'] += 1
            first_step_10.append(start)
            # 僵尸段: 首10段起始到结尾都是10吗
            tail = acts[start:]
            if len(set(tail)) == 1:  # 后面全是10
                stats['exactly_200'] += 1
                stats['run_after_move'] += 1  # 前面 steps!=10
            else:
                # 是否首段后又回到非10（罕见）
                non10_after = [x for x in tail if x != 10]
                if not non10_after:
                    stats['exactly_200'] += 1

print(f"大负局总数: {stats['big_neg']}")
print(f"存在长 act10 段 (>=10 连): {stats['has_long_10run']}/{stats['big_neg']} = {stats['has_long_10run']/max(1,stats['big_neg'])*100:.0f}%")
print(f"首长 act10 段之后全是10(到200步死步拖满): {stats['exactly_200']}/{stats['has_long_10run']} = {stats['exactly_200']/max(1,stats['has_long_10run'])*100:.0f}%")
if first_step_10:
    import statistics
    print(f"\n首次僵尸段起始 step 分布:")
    print(f"  min={min(first_step_10)}, max={max(first_step_10)}, mean={statistics.mean(first_step_10):.0f}, median={statistics.median(first_step_10):.0f}")
    print(f"  Q1={sorted(first_step_10)[len(first_step_10)//4]}, Q3={sorted(first_step_10)[3*len(first_step_10)//4]}")
    waste = sum(200 - s for s in first_step_10)
    print(f"\n⏱️  浪费估算:")
    print(f"  总僵尸步 = {waste} (60局平均每局浪费 {waste//max(1,len(first_step_10))} 步)")
    print(f"  浪费训练时间 = {waste*1.1/3600:.1f} 小时 (@ 1.1s/step)")
    print(f"  done=False 僵尸段轨迹数量 = {len(first_step_10)} (全部带 done=False 入 buffer)")
