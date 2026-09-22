# -*- coding: utf-8 -*-
"""训练日志全段分析: 进度/吞吐/分图/截断/胜负/熵与KL健康度/异常事件 (250步口径)"""
import re, io, sys
from collections import defaultdict

LOG = '/mnt/d/Bigdata/hero3_fresh/train_loop.log'
WIN_R, WIN_S = 80, 60          # 首胜代理口径
CAPS = [200, 250]              # 历史/当前步上限

re_ep  = re.compile(r'ep_steps=(\d+)\s+r=([-\d.]+)\s+act=\[(.+?)\]\s+obs_nz=(\d+)\s+map=(\S+)')
re_ept = re.compile(r'\[EP_TIME\] map=(\S+) steps=(\d+) secs=(\d+) r=([-\d.]+) err=(\S+)')
re_upd = re.compile(r'step(\d+)\s+avg_r=([-\d.]+)\s+vloss=([-\d.]+)\s+loss=([-\d.]+)\s+'
                    r'kl=([-\d.]+)\s+klc=([-\d.]+)\s+ep=(\d+)\s+time=(\d+)s'
                    r'(?:\s+entc=([-\d.]+)\s+ent=([-\d.]+))?')
re_ecnt = re.compile(r'step(\d+)\s+avg_r=([-\d.]+)\s+ep=(\d+)\s+time=(\d+)s')

eps, epts, upds, ecnts = [], [], [], []
events = defaultdict(list)
resumes = []
with io.open(LOG, encoding='utf-8', errors='replace') as f:
    for ln, line in enumerate(f, 1):
        m = re_ep.search(line)
        if m:
            acts = [int(x) for x in m.group(3).split(',') if x.strip()]
            eps.append(dict(ln=ln, steps=int(m.group(1)), r=float(m.group(2)),
                            acts=acts, nz=int(m.group(4)), mp=m.group(5)))
        m = re_ept.search(line)
        if m:
            epts.append(dict(ln=ln, mp=m.group(1), steps=int(m.group(2)),
                             secs=int(m.group(3)), r=float(m.group(4)), err=m.group(5)))
        m = re_upd.search(line)
        if m:
            upds.append(dict(step=int(m.group(1)), avg=float(m.group(2)), vl=float(m.group(3)),
                             loss=float(m.group(4)), kl=float(m.group(5)), klc=float(m.group(6)),
                             ep=int(m.group(7)), t=int(m.group(8)),
                             entc=float(m.group(9)) if m.group(9) else None,
                             ent=float(m.group(10)) if m.group(10) else None))
        elif re_ecnt.search(line):
            m = re_ecnt.search(line)
            ecnts.append(dict(step=int(m.group(1)), ep=int(m.group(3)), t=int(m.group(4))))
        for tag in ('[ZOMBIE]', '[ENDTURN_FUSE]', '[OBS-INIT]', 'obs_nz=0', 'Traceback'):
            if tag in line:
                events[tag].append((ln, line.strip()[:150]))
        if 'Loaded train state' in line:
            mm = re.search(r'step=(\d+)', line)
            resumes.append((ln, int(mm.group(1)) if mm else -1))

def pct(a, b):
    return 100.0 * a / b if b else 0.0

# 当前进程段 = 最后一次 Loaded train state 之后
SEG_LN = resumes[-1][0] if resumes else 0
seg_ep  = [x for x in eps if x['ln'] > SEG_LN]
seg_ept = [x for x in epts if x['ln'] > SEG_LN]
SEG_STEP = resumes[-1][1] if resumes else 0
seg_upd = [u for u in upds if u['step'] >= SEG_STEP]
print(f'\n[当前段] 起于 ln={SEG_LN} resume step={SEG_STEP}, '
      f'EP={len(seg_ep)} 更新点={len(seg_upd)}')
if len(seg_upd) >= 2:
    a, b = seg_upd[0], seg_upd[-1]
    ds, dt = b['step'] - a['step'], b['t'] - a['t']
    de = max(b['ep'] - a['ep'], 1)
    print(f'当前段吞吐: {ds/max(dt,1):.2f} step/s, {ds/de:.0f} step/ep, '
          f'{de/max(dt,1)*3600:.1f} ep/h, 已训 {b["t"]/3600:.1f}h')

print('================ 总览 ================')
print(f'episode={len(eps)} EP_TIME={len(epts)} 更新点={len(upds)} resume={len(resumes)}')
for tag in ('[ZOMBIE]', '[ENDTURN_FUSE]', 'obs_nz=0', 'Traceback'):
    print(f'  {tag}: {len(events[tag])}')
if eps:
    e = eps[-1]
    print(f'最新EP: ln={e["ln"]} map={e["mp"]} steps={e["steps"]} r={e["r"]} obs_nz={e["nz"]}')
if upds:
    u = upds[-1]
    print(f'最新更新: step={u["step"]} ep={u["ep"]} time={u["t"]}s ({u["t"]/3600:.1f}h) '
          f'avg_r={u["avg"]} vloss={u["vl"]} kl={u["kl"]} entc={u["entc"]} ent={u["ent"]}')
if len(upds) >= 2:
    a, b = upds[0], upds[-1]
    ds, dt = b['step'] - a['step'], b['t'] - a['t']
    de = max(b['ep'] - a['ep'], 1)
    print(f'吞吐(全段): {ds/max(dt,1):.2f} step/s, {ds/de:.0f} step/ep, '
          f'{de/max(dt,1)*3600:.0f} ep/h')

# ---- 最近 N 更新点趋势 (当前段) ----
print('\n================ 训练指标趋势 (当前段, 最近14个更新点) ================')
trend_src = seg_upd if len(seg_upd) >= 2 else upds
for u in trend_src[-14:]:
    print(f'  step={u["step"]:>7} ep={u["ep"]:>4} avg_r={u["avg"]:>6.2f} '
              f'kl={u["kl"]:.3f} klc={u["klc"]:.3f} vloss={u["vl"]:.3f} '
              f'entc={u["entc"] if u["entc"] is not None else "-"} '
              f'ent={u["ent"] if u["ent"] is not None else "-"}')

# ---- 分窗口 episode 统计 ----
def window_report(name, sub):
    if not sub:
        return
    rs = sorted(x['r'] for x in sub)
    n = len(rs)
    cap = 250 if any(x['steps'] > 200 for x in sub) else 200
    trunc = sum(1 for x in sub if x['steps'] >= cap)
    win = sum(1 for x in sub if x['r'] >= WIN_R and x['steps'] < WIN_S)
    short = sum(1 for x in sub if x['steps'] < 30)
    nz0 = sum(1 for x in sub if x['nz'] == 0)
    bigneg = sum(1 for x in sub if x['r'] <= -100)
    q = lambda f: rs[min(n - 1, int(n * f))]
    print(f'-- {name} (n={n}, 步上限={cap}) --')
    print(f'   mean_r={sum(rs)/n:7.2f} p10={q(0.1):7.1f} p50={q(0.5):7.1f} '
          f'p90={q(0.9):7.1f} min={rs[0]:7.1f} max={rs[-1]:7.1f}')
    print(f'   截断={trunc}({pct(trunc,n):.0f}%) 首胜代理={win}({pct(win,n):.1f}%) '
          f'<30步短局={short}({pct(short,n):.0f}%) r<=-100={bigneg}({pct(bigneg,n):.0f}%) obs_nz=0={nz0}')

print('\n================ Episode 窗口 (当前段) ================')
window_report(f'当前段全部 {len(seg_ep)} 局' if seg_ep else '当前段为空', seg_ep)
if len(eps) > len(seg_ep):
    window_report('上一进程段最后 100 局(对照)', eps[:max(0, len(eps)-len(seg_ep))][-100:])

# ---- 分地图 (当前段) ----
print(f'\n================ 分地图 (当前段 {len(seg_ep)} 局) ================')
by = defaultdict(list)
for x in seg_ep:
    key = re.sub(r'_\d+\.vmap$', '', x['mp']).replace('.vmap', '')
    by[key].append(x)
print(f'{"map":<36}{"n":>4}{"mean_r":>9}{"截断%":>7}{"短局%":>7}{"首胜%":>7}{"均步":>6}{"均sec":>7}')
ept_by_map = defaultdict(list)
for x in epts:
    ept_by_map[x['mp']].append(x['secs'])
for k in sorted(by):
    v = by[k]
    n = len(v)
    cap = 250 if any(x['steps'] > 200 for x in v) else 200
    trunc = sum(1 for x in v if x['steps'] >= cap)
    short = sum(1 for x in v if x['steps'] < 30)
    win = sum(1 for x in v if x['r'] >= WIN_R and x['steps'] < WIN_S)
    avgs = sum(x['steps'] for x in v) / n
    fullname = v[-1]['mp']
    secs = ept_by_map.get(fullname, [])
    avgsec = sum(secs[-n:]) / max(min(len(secs), n), 1)
    print(f'{k:<36}{n:>4}{sum(x["r"] for x in v)/n:>9.1f}{pct(trunc,n):>6.0f}%'
          f'{pct(short,n):>6.0f}%{pct(win,n):>6.0f}%{avgs:>6.0f}{avgsec:>7.0f}')

# ---- EP_TIME err ----
errs = [x for x in epts if x['err'] != 'no']
print(f'\n================ EP_TIME err={len(errs)} ================')
for x in errs[-10:]:
    print(f'  ln={x["ln"]} {x["mp"]} steps={x["steps"]} r={x["r"]} err={x["err"]}')

# ---- 事件样例 ----
for tag in ('[ZOMBIE]', '[ENDTURN_FUSE]', 'Traceback'):
    ev = events[tag]
    if ev:
        print(f'\n==== {tag} 共{len(ev)}, 最近3条 ====')
        for ln, s in ev[-3:]:
            print(f'  ln={ln}: {s}')
