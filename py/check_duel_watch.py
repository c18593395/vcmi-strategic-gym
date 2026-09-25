#!/usr/bin/env python3
"""duel/1v3 观察窗统计 (09-06 建, 09-08 升级战斗质量三指标): 自发经济 / 200 步局占比 / r 与步数分布,
T05 同口径对照 + 1v3 结案面板 (30 局判据 + 战斗质量三指标)

口径:
- 数据源① = train_loop.log: ep_steps= 行 (含 act/obs_nz/map) + 转储事件行
  (转储时序: 事件行先于所属局的 ep_steps= 行 → pending 累积, 遇 ep 行归并)
- 数据源② = battle_quality_events.log: [BHERO_KILL] 蓝英雄击杀事件 (ep_runner 观测埋点追加写,
  09-08 上线, 之前的局无此数据)
- 自发经济 = act 序列中 index>=24 (economy_force 24 步强制窗外) 的 16-21 动作
- 200 步局 = ep_steps=200 (truncation)
- 战斗质量三指标 (1v3 结案采集口径升级):
  ①蓝英雄击杀事件 [BHERO_KILL] (per-map 总数, 事件文件源)
  ②[GUARD] 守卫胜闭环率趋势 = 有 [GUARD] 的局占比, 前 1/3 vs 后 1/3 (duel 基线 96.9%)
  ③蓝英雄 roaming 交战频率 = ([TOWNSTALL]+[TOWN_BLOCKED]) 次数/局 (1v3 vs duel 对比)
"""
import os
import re, sys, os
from collections import defaultdict

LOG = os.environ.get("LOG", "/mnt/d/Bigdata/hero3_fresh/train_loop.log")
KILL_LOG = os.environ.get("KILL_LOG", "/mnt/d/Bigdata/hero3_fresh/battle_quality_events.log")
WINDOW = int(sys.argv[1]) if len(sys.argv) > 1 else 200  # 最近 N 个 ep 行

pat = re.compile(
    r"ep_steps=(\d+) r=(-?[\d.]+) act=\[([0-9, ]+)\] obs_nz=(\d+) map=(\S+)"
)
# 主日志白名单事件 → 归并进所属局的标签名
EV_TAGS = {
    "[GUARD]": "guard", "[GUARD_DONE]": "guard_done",
    "[TOWNSTALL]": "townstall", "[TOWN_BLOCKED]": "town_blocked",
    "[ZOMBIE]": "zombie", "[MINE]": "mine", "[TOWN]": "town",
    "[TOWN_CAPTURE]": "town_capture", "[BHERO_KILL]": "bhero_kill",
    "[START_HOME]": "start_home", "[RECRUITED]": "recruited",
}

stats = defaultdict(lambda: {
    "n": 0, "r": [], "steps": [], "spont_eps": 0, "spont_total": 0,
    "obs_nz": set(),
    "ev": defaultdict(int),          # 标签名 → 事件次数
    "ev_eps": defaultdict(int),      # 标签名 → 出现该事件的局数
})

# --- 数据源①: 主日志顺序扫描, pending 事件归并到紧随的 ep 行 ---
rows = []   # (map, steps, r, acts, nz, pending_events)
pending = defaultdict(int)
with open(LOG, errors="replace") as f:
    for line in f:
        if "ep_steps=" in line and "map=" in line:
            m = pat.search(line)
            if not m:
                continue
            steps, r, acts, nz, mp = m.groups()
            rows.append((mp, int(steps), float(r),
                         [int(x) for x in acts.split(",") if x.strip()],
                         nz, dict(pending)))
            pending.clear()
        else:
            for tag, name in EV_TAGS.items():
                if tag in line:
                    pending[name] += 1

def accum(s, steps, r, acts, nz, evs):
    s["n"] += 1
    s["r"].append(r)
    s["steps"].append(steps)
    s["obs_nz"].add(nz)
    spont = sum(1 for i, a in enumerate(acts) if i >= 24 and 16 <= a <= 21)
    s["spont_total"] += spont
    if spont > 0:
        s["spont_eps"] += 1
    for k, v in evs.items():
        s["ev"][k] += v
        s["ev_eps"][k] += 1

for mp, steps, r, acts, nz, evs in rows[-WINDOW:]:
    accum(stats[mp], steps, r, acts, nz, evs)

# --- 数据源②: 事件文件 (battle_quality_events.log; 09-08 上线前的局无数据) ---
# kills = [BHERO_KILL] 蓝英雄击杀; caps = [TOWN_CAPTURE] 占城 (09-08 起带奖励, ep_runner 旁路写入,
# 主日志白名单未含 → 数据源③旁路口径)
kills = defaultdict(int)
caps = defaultdict(int)
if os.path.exists(KILL_LOG):
    kpat = re.compile(r"\[BHERO_KILL\] map=(\S+) .*live_slots=(\d+)")
    cpat = re.compile(r"\[TOWN_CAPTURE\] map=(\S+)")
    with open(KILL_LOG, errors="replace") as f:
        for line in f:
            m = kpat.search(line)
            if m and int(m.group(2)) > 0:  # live_slots=0 = heroes 段空拍误报 (0908 甄别), 不计
                kills[m.group(1)] += 1
            m = cpat.search(line)
            if m:
                caps[m.group(1)] += 1

total = sum(s["n"] for s in stats.values())
print(f"=== 最近 {total} ep (train_loop.log 尾窗 {WINDOW}) ===\n")
hdr = (f"{'map':<36}{'局数':>4}{'avg_r':>8}{'r范围':>16}{'200步局':>9}"
       f"{'自发局':>6}{'自发次':>7}{'守卫局':>7}{'堵路次':>7}{'击杀':>5}{'占城':>5}  obs_nz")
print(hdr)
for mp, s in sorted(stats.items()):
    n = s["n"]
    t200 = sum(1 for x in s["steps"] if x >= 200)
    avg = sum(s["r"]) / n
    g_eps = s["ev_eps"].get("guard", 0)
    roam = s["ev"].get("townstall", 0) + s["ev"].get("town_blocked", 0)
    print(f"{mp:<36}{n:>4}{avg:>8.1f}{min(s['r']):>8.1f}~{max(s['r']):<7.1f}"
          f"{t200:>6}({t200*100//n}%){s['spont_eps']:>6}{s['spont_total']:>7}"
          f"{g_eps:>4}({g_eps*100//max(n,1)}%){roam:>7}{kills.get(mp,0):>5}{caps.get(mp,0):>5}  {sorted(s['obs_nz'])}")

# --- 分组对照: 1v3 原版 vs duel vs 其他 ---
def group_of(mp):
    if mp.startswith("T06_adventure_72X72_01.vmap"):
        return "1v3"
    if "duel" in mp:
        return "duel"
    return "other"

groups = defaultdict(list)
for row in rows[-WINDOW:]:
    groups[group_of(row[0])].append(row)

print(f"\n=== 1v3 vs duel 对照 (同窗口) ===")
print(f"{'组':<8}{'局数':>5}{'avg_r':>8}{'200步局':>9}{'自发率':>8}{'守卫胜闭环':>11}"
      f"{'守卫胜前/后1/3':>14}{'堵路次/局':>10}{'击杀':>5}{'占城':>5}")
for g in ("1v3", "duel", "other"):
    rs = groups.get(g, [])
    if not rs:
        continue
    n = len(rs)
    avg = sum(r for _, _, r, *_ in rs) / n
    t200 = sum(1 for _, st, *_ in rs if st >= 200)
    sp = sum(1 for _, _, _, acts, *_ in rs
             if any(i >= 24 and 16 <= a <= 21 for i, a in enumerate(acts)))
    g_eps = sum(1 for *_, evs in rs if evs.get("guard"))
    # 守卫胜闭环趋势: 前 1/3 局 vs 后 1/3 局的 guard 局占比
    k = max(n // 3, 1)
    g_front = sum(1 for *_, evs in rs[:k] if evs.get("guard"))
    g_back = sum(1 for *_, evs in rs[-k:] if evs.get("guard"))
    roam = sum(evs.get("townstall", 0) + evs.get("town_blocked", 0) for *_, evs in rs)
    mmap = {"1v3": ("T06_adventure_72X72_01.vmap",), "duel": None, "other": None}
    kk = cc = 0
    if g == "1v3":
        kk = sum(kills[m] for m in mmap["1v3"])
        cc = sum(caps[m] for m in mmap["1v3"])
    elif g == "duel":
        kk = sum(v for m, v in kills.items() if "duel" in m)
        cc = sum(v for m, v in caps.items() if "duel" in m)
    print(f"{g:<8}{n:>5}{avg:>8.1f}{t200:>6}({t200*100//n}%){sp*100//n:>6}%"
          f"{g_eps:>5}({g_eps*100//n}%){g_front*100//k:>5}%/{g_back*100//k}%"
          f"{roam/n:>10.2f}{kk:>5}{cc:>5}")

# --- 1v3 结案面板 (30 局判据) ---
rs = groups.get("1v3", [])
print(f"\n=== 1v3 结案面板 ===")
if not rs:
    print("尾窗无 1v3 局 (调大 WINDOW 或等轮换)")
else:
    n = len(rs)
    k = max(n // 3, 1)
    avg_f = sum(r for _, _, r, *_ in rs[:k]) / k
    avg_b = sum(r for _, _, r, *_ in rs[-k:]) / k
    t200 = sum(1 for _, st, *_ in rs if st >= 200)
    sp = sum(1 for _, _, _, acts, *_ in rs
             if any(i >= 24 and 16 <= a <= 21 for i, a in enumerate(acts)))
    g_eps = sum(1 for *_, evs in rs if evs.get("guard"))
    zom = sum(evs.get("zombie", 0) for *_, evs in rs)
    cc = sum(caps[m] for m in ("T06_adventure_72X72_01.vmap",))
    print(f"1v3 全局累计: {sum(1 for row in rows if group_of(row[0])=='1v3')} 局 (结案线 30)")
    print(f"尾窗 {n} 局: avg_r={sum(r for _,_,r,*_ in rs)/n:.1f} (前1/3 {avg_f:.1f} → 后1/3 {avg_b:.1f},"
          f" 比值 {avg_b/max(avg_f,0.01):.2f} 判据≥0.8)")
    print(f"200步局: {t200} ({t200*100/n:.0f}%, 判据≤20%)  自发经济: {sp}/{n} 局 ({sp*100//n}%, 判据≥80%)")
    print(f"守卫胜闭环: {g_eps}/{n} ({g_eps*100/n:.0f}%, duel 基线 96.9%)  ZOMBIE: {zom}")
    print(f"占城: {cc} 次 (旁路口径, 09-08 capture +100 奖励生效后统计)"
          f"  duel 组占城: {sum(v for m, v in caps.items() if 'duel' in m)}")
    print(f"战斗质量三指标: ①蓝英雄击杀 {kills.get('T06_adventure_72X72_01.vmap',0)} 次"
          f" (埋点 09-08 上线, 之前局无数据)  ②守卫胜闭环趋势见上  ③堵路 {roam/n:.2f} 次/局")
