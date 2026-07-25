#!/usr/bin/env python3
"""读取 VCMI 训练轨迹，解析模型动作"""
import json, sys, os, math

ACTIONS = ["→","↘","↓","↙","←","↖","↑","↗","交互","换英雄","结束回合"]
STATUS = ["idle","moving","fighting","interacting"]

def analyze_traj(path):
    with open(path) as f:
        d = json.load(f)
    
    if "error" in d:
        print(f"❌ 轨迹出错: {d['error']}")
        return
    
    print(f"=== 轨迹分析: {os.path.basename(path)} ===")
    print(f"步数: {d.get('steps', 0)}  |  总奖励: {d.get('total_rew', 0):.1f}")
    print()
    
    for i in range(len(d.get('act', []))):
        a = d['act'][i]
        r = d['rew'][i] if i < len(d['rew']) else 0
        done = d['done'][i] if i < len(d['done']) else False
        
        act_name = ACTIONS[a] if a < len(ACTIONS) else f"未知({a})"
        done_mark = " [DONE]" if done else ""
        
        # 读取 obs 中的关键字段（前 3 维：英雄位置）
        obs = d['obs'][i] if i < len(d['obs']) else []
        pos_info = ""
        if len(obs) >= 3:
            hx, hy = obs[0], obs[1]
            # 第二个英雄的 pos
            hx2, hy2 = (obs[29], obs[30]) if len(obs) > 30 else (0, 0)
            pos_info = f"  H1=({hx:.0f},{hy:.0f})"
            if hx2 > 0:
                pos_info += f" H2=({hx2:.0f},{hy2:.0f})"
        
        print(f"  step {i:2d}: {act_name:6s}  r={r:+.1f}{done_mark}{pos_info}")
    
    print()
    # 动作分布统计
    act_counts = {}
    for a in d.get('act', []):
        n = ACTIONS[a] if a < len(ACTIONS) else f"未知({a})"
        act_counts[n] = act_counts.get(n, 0) + 1
    
    print("动作分布:")
    for name in ACTIONS:
        c = act_counts.get(name, 0)
        bar = "█" * c
        print(f"  {name:6s}: {c:2d}  {bar}")

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/traj_one.json"
    analyze_traj(path)
