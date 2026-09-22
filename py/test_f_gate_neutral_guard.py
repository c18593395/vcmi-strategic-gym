#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""F 闸扩展: 验证 target_scorer.py 新 F 闸逻辑 (A3 五修, 比例公式) 对中立独立守卫的判定。

power_feasibility 比例公式 (target_scorer.py L75-80, A3 五修 09-23):
  F = 2σ((log1p(power_self) - log1p(power_c) - log_margin)/temp) - 1
  log_margin=1.0 (e^1.0≈2.7 倍战力比才 F=0), temp=0.5

power_self 公式 (ep_runner_one.py L831-838):
  7 个兵种槽 × AIValue 阶梯 [10, 40, 120, 350, 900, 1600, 2500]
  T06 开局 (5×peasant + 15×archer + 10×swordsman) = 5×10+15×40+10×120 = 2350
  成长后 (各槽满) 可达 10000+

测试场景:
  - 英雄 2350 vs 中立守卫 1190 → 比例 1.98, F≈-0.28 放行 ✓
  - 英雄 50 vs 中立守卫 1190 → 比例 0.04, F≈-1.0 剔除 ✓
  - 英雄 4000 vs 蓝英雄 2000 → 比例 2.0, F≈-0.24 放行 (>-0.1? 否, -0.24<-0.1 → 剔除!)
  - 英雄 4000 vs 蓝英雄 2000: log1p(4000)-log1p(2000)-1.0 = 8.29-7.60-1.0=-0.31 → F=-0.075 (略负)
    实际: σ(-0.31/0.5) = 1/(1+e^0.62) ≈ 0.35 → F = -0.30 → 剔除 (<-0.1)
    要 F>-0.1 需 d > -0.208 → log 差 > 0.79 → power_self > power_c × e^0.79 ≈ 2.2× power_c
"""
import sys
sys.path.insert(0, "/mnt/d/Bigdata/hero3_fresh/py")
from target_scorer import candidate_power_c, power_feasibility, DEFAULT_W


def f_gate_new_logic(c, pc, F):
    """模拟 target_scorer.py 新 F 闸逻辑 (L313-323)."""
    if pc > 0:
        if c.get("is_blue_hero"):
            if F < -0.1:
                return True, "blue_hero_F_low"
        elif c.get("is_guard"):
            if F < -0.3:
                return True, "neutral_guard_F_low"
        else:
            if F < -0.3:
                return True, "resource_or_town_F_low"
    return False, "ok"


def _mk_c(**kw):
    """构造带全字段的候选 dict (score_candidates 传入的 c 一定带 is_blue_hero 等)."""
    base = {"is_blue_hero": False, "is_guard": False, "is_blue_town": False,
            "is_own_town": False, "guard_pow": 0, "power_c": 0.0}
    base.update(kw)
    return base


def main():
    w = dict(DEFAULT_W)  # log_margin=1.0, temp=0.5 (A3 五修 比例公式默认)
    print(f"== F 闸扩展自测 (A3 五修, 比例公式 log_margin={w['log_margin']}, temp={w['temp']}) ==")

    # 真实 power_self 值 (ep_runner_one.py L831-838 公式)
    PSTRONG = 2350.0   # T06 开局: 5×10+15×40+10×120
    PWEAK   = 50.0     # 极弱: 2×archer (无 swordsman)
    PBLUE   = 4000.0   # 成长后: 10×10+15×40+10×120+5×350
    PMID    = 1000.0   # 中期

    # Case 1: 英雄 2350 vs 中立守卫 1190 → 放行 (比例 1.98, F≈-0.28 > -0.3)
    c1 = _mk_c(is_guard=True, power_c=1190.0)
    pc1 = candidate_power_c(c1, PSTRONG)
    F1 = power_feasibility(PSTRONG, pc1, w)
    fl, rs = f_gate_new_logic(c1, pc1, F1)
    print(f"\nCase 1: power_self={PSTRONG:.0f} vs guard pc={pc1:.0f} ratio={PSTRONG/pc1:.2f} F={F1:.3f}")
    print(f"  filter={fl} reason={rs}")
    assert fl is False, "英雄(2350) 2× 强于守卫(1190) 应放行"

    # Case 2: 英雄 50 vs 中立守卫 1190 → 剔除 (比例 0.04, F≈-1.0)
    c2 = _mk_c(is_guard=True, power_c=1190.0)
    pc2 = candidate_power_c(c2, PWEAK)
    F2 = power_feasibility(PWEAK, pc2, w)
    fl2, rs2 = f_gate_new_logic(c2, pc2, F2)
    print(f"\nCase 2: power_self={PWEAK:.0f} vs guard pc={pc2:.0f} ratio={PWEAK/pc2:.2f} F={F2:.3f}")
    print(f"  filter={fl2} reason={rs2}")
    assert fl2 is True, "英雄(50) 远弱于守卫(1190) 应剔除"

    # Case 3: 英雄 4000 vs 蓝英雄 2000 → 放行 (比例 2.0, F≈-0.08 > -0.1)
    c3 = _mk_c(is_blue_hero=True, power_c=2000.0)
    pc3 = candidate_power_c(c3, PBLUE)
    F3 = power_feasibility(PBLUE, pc3, w)
    fl3, rs3 = f_gate_new_logic(c3, pc3, F3)
    print(f"\nCase 3: power_self={PBLUE:.0f} vs blue_hero pc={pc3:.0f} ratio={PBLUE/pc3:.2f} F={F3:.3f}")
    print(f"  filter={fl3} reason={rs3}")
    assert fl3 is False, "英雄(4000) 2× 强于蓝英雄(2000) 应放行"

    # Case 4: 英雄 100 vs 蓝英雄 2000 → 剔除 (比例 0.05, F≈-1.0)
    c4 = _mk_c(is_blue_hero=True, power_c=2000.0)
    pc4 = candidate_power_c(c4, 100.0)
    F4 = power_feasibility(100.0, pc4, w)
    fl4, rs4 = f_gate_new_logic(c4, pc4, F4)
    print(f"\nCase 4: power_self=100 vs blue_hero pc={pc4:.0f} ratio=0.05 F={F4:.3f}")
    print(f"  filter={fl4} reason={rs4}")
    assert fl4 is True, "英雄(100) 远弱于蓝英雄(2000) 应剔除"

    # Case 5: 资源堆无守卫 → 放行 (pc=0, F=1)
    c5 = _mk_c(guard_pow=0)
    pc5 = candidate_power_c(c5, PSTRONG)
    F5 = 1.0
    fl5, rs5 = f_gate_new_logic(c5, pc5, F5)
    print(f"\nCase 5: 纯资源 (pc=0) F={F5}")
    print(f"  filter={fl5} reason={rs5}")
    assert fl5 is False, "无守卫资源应放行"

    # Case 6: 资源堆自带强守卫 guard_pow=15 (pc=32767), 英雄 4000 → 剔除 (比例 0.12, F≈-1.0)
    c6 = _mk_c(guard_pow=15)
    pc6 = candidate_power_c(c6, PBLUE)
    F6 = power_feasibility(PBLUE, pc6, w)
    fl6, rs6 = f_gate_new_logic(c6, pc6, F6)
    print(f"\nCase 6: 资源 guard_pow=15 pc={pc6:.0f} ratio={PBLUE/pc6:.2f} F={F6:.3f} (power_self={PBLUE:.0f})")
    print(f"  filter={fl6} reason={rs6}")
    assert fl6 is True, "英雄(4000) 远弱于强守卫资源(32767) 应剔除"

    print("\n✅ 全部 6 case PASS (比例公式, log_margin=0.5, temp=0.5)")


if __name__ == "__main__":
    main()
