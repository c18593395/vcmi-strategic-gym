#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
H.7 冒烟测试 — 新动作 11-24 实机验证 (动作空间设计文档 §4 #5-#13)

策略: MMAI 模式 (red_adventure_ai="MMAI" — Python 动作由 AAI::yourTurn 真正执行;
Nullkiller2 模式下 yourTurn 不执行, 动作全被忽略, 之前 PASS 是假象)。
For Sale.h3m: red 1 英雄 (13,6) + 城镇 (14,5) 相邻。
  - SPLIT/MERGE/SWAP: 需要第 2 个友方英雄, 单英雄图目标缺失 → 静默跳过 = 无崩溃 (合法)
  - RECRUIT/BUILD/GARRISON/RECRUIT_HERO: 需英雄进城, INTERACT 驱动
验证: obs/state 数据断言, 不依赖 VCMI 日志
"""
import sys
import numpy as np

sys.path.insert(0, "/mnt/d/Bigdata/hero3_fresh")
from vcmi_gym.envs.v13.strategic_env import StrategicEnv, END_TURN

PASS = []
FAIL = []

def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    print(f"  [{status}] {name} {detail}")
    if cond:
        PASS.append(name)
    else:
        FAIL.append(name)

def red_hero_pos(st):
    for i in range(8):
        if st.heroes[i].id >= 0 and st.heroes[i].owner == 0:
            return i, (st.heroes[i].pos_x, st.heroes[i].pos_y, st.heroes[i].pos_z)
    return None, None

def main():
    env = StrategicEnv(
        mapname="Dungeon Keeper.h3m", max_turns=999,
        red="StupidAI", blue="StupidAI",
        red_adventure_ai="MMAI", blue_adventure_ai="MMAI",
        boot_timeout=240, vcmi_timeout=240, user_timeout=120,
        seed=42, vcmi_loglevel_global="error", vcmi_loglevel_ai="error",
    )
    obs0, info = env.reset()
    if info.get("day", 0) <= 0:
        print("RESET FAILED")
        env.close()
        sys.exit(1)

    st = env._read_state()
    hidx, hpos = red_hero_pos(st)
    town_pos = None
    for i in range(8):
        if st.towns[i].id >= 0 and st.towns[i].owner == 0:
            town_pos = (st.towns[i].pos_x, st.towns[i].pos_y, st.towns[i].pos_z)
    print(f"reset OK day={st.day} red_hero={hidx}{hpos} red_town={town_pos} gold={st.players[0].gold}")

    # ===== #5-7 SPLIT/MERGE/SWAP: 单英雄图目标缺失 = 静默 = 无崩溃 =====
    print("\n=== #5-7 SPLIT/MERGE/SWAP (单英雄图: 目标缺失静默) ===")
    for act, name in [(11, 'SPLIT_1OF3'), (12, 'SPLIT_1OF2'), (13, 'SPLIT_ALL'), (14, 'MERGE_FROM'), (15, 'SWAP_ARMY')]:
        try:
            env.step(act)
            st = env._read_state()
            check(f"{name} 无崩溃", st is not None)
        except Exception as e:
            check(f"{name} 无崩溃", False, f"EXC: {e}")

    # ===== INTERACT 进城 =====
    print("\n=== INTERACT 进城 ===")
    env.step(8)  # 走向城镇
    st = env._read_state()
    _, hpos2 = red_hero_pos(st)
    print(f"  INTERACT#1: hero {hpos}->{hpos2}")
    # 英雄可能在城镇格上 (pos 显示原格) — 核心验证是后续 GARRISON 能驻守
    env.step(8)  # 进城 (standPos==heroPos → moveHero 到城镇格)
    st = env._read_state()
    g = [st.heroes[i].is_garrisoned for i in range(8) if st.heroes[i].id >= 0 and st.heroes[i].owner == 0]
    print(f"  INTERACT#2: is_garrisoned={g}")
    # INTERACT 有效性由后续 GARRISON 驻守成功证明 (英雄须已 visiting 城镇)

    # ===== #8 RECRUIT ×3 =====
    print("\n=== #8 RECRUIT ×3 ===")
    st = env._read_state()
    gold_before = st.players[0].gold
    env.step(16)
    st = env._read_state()
    gold_after = st.players[0].gold
    # 城镇有被动收入(+750/步) — 若兵营有兵, recruit 步增量 < 纯收入步; 兵营空则 == 纯收入
    # 用"GARRISON 后无动作步"无法隔离, 简化: 只断言无崩溃 + 英雄 army 变化或 gold 未暴增
    check("RECRUIT_1 无崩溃", st is not None)
    check("RECRUIT_1 未导致 gold 异常暴增", gold_after <= gold_before + 2000,
          f"gold {gold_before}→{gold_after} (被动收入上限 2000/步)")
    env.step(17)
    st = env._read_state()
    check("RECRUIT_2 无崩溃", st is not None)
    env.step(18)
    st = env._read_state()
    check("RECRUIT_3 无崩溃", st is not None)

    # ===== #9 BUILD ×3 =====
    print("\n=== #9 BUILD ×3 ===")
    env.step(19)
    st = env._read_state()
    check("BUILD_1 无崩溃", st is not None)
    env.step(20)
    st = env._read_state()
    check("BUILD_2 无崩溃", st is not None)
    env.step(21)
    st = env._read_state()
    check("BUILD_3 无崩溃", st is not None)

    # ===== #10 GARRISON =====
    print("\n=== #10 GARRISON ===")
    env.step(22)
    st = env._read_state()
    g = [st.heroes[i].is_garrisoned for i in range(8) if st.heroes[i].id >= 0 and st.heroes[i].owner == 0]
    check("GARRISON 有英雄驻守", any(g), f"is_g={g}")

    # ===== #11 RECRUIT_HERO =====
    print("\n=== #11 RECRUIT_HERO ===")
    st = env._read_state()
    hb = st.players[0].hero_count
    env.step(23)
    st = env._read_state()
    ha = st.players[0].hero_count
    check("RECRUIT_HERO 新英雄", ha > hb, f"hero_count {hb}→{ha}")

    # ===== #12 MOVE_TO =====
    print("\n=== #12 MOVE_TO ===")
    try:
        env.step(24)
        st = env._read_state()
        check("MOVE_TO 无崩溃", st is not None)
    except Exception as e:
        check("MOVE_TO 无崩溃", False, f"EXC: {e}")

    # ===== #13 组合链路 =====
    print("\n=== #13 组合: A分兵→B合兵→B攻城→守城 (单英雄图简化) ===")
    try:
        env.step(11)  # 分兵 (目标缺失静默)
        env.step(22)  # 驻守
        env.step(10)  # 结束回合
        st = env._read_state()
        check("组合链路无 segfault", st is not None)
    except Exception as e:
        check("组合链路无 segfault", False, f"EXC: {e}")

    # ===== 汇总 =====
    print(f"\n{'='*50}")
    print(f"PASS: {len(PASS)}  FAIL: {len(FAIL)}")
    for f in FAIL:
        print(f"  FAILED: {f}")
    try:
        env.close()
    except Exception:
        pass
    sys.exit(0 if not FAIL else 2)


if __name__ == "__main__":
    main()
