#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_obs_v2.py — OBS schema v2 (2689 维) 布局验证

用 ctypes 构造假的 StrategicState (strategic_reader.py 的类), 填哨兵值,
调用 strategic_env.py 中**真实**的 _strategic_state_to_obs 函数
(通过 ast 提取源码, 绕开 connector_v13/gymnasium 导入链),
逐段验证 obs 布局与规格一致:

  [0:8]      global 8        [8:104] players 96
  [104:288]  heroes 184      [288:400] towns 112
  [400:625]  local 225       [625:2673] gexpl 2048
  [2673:2681] active_hero 8  [2681:2689] passable 8
"""
import ast
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # hero3_fresh
ENV_PATH = os.path.join(ROOT, "vcmi_gym", "envs", "v13", "strategic_env.py")

# 1. strategic_reader.py 纯 stdlib 可直接 import
sys.path.insert(0, ROOT)
import strategic_reader as sr

# 2. ast 提取 strategic_env.py 中的常量与 _strategic_state_to_obs 真实源码
src = open(ENV_PATH, encoding="utf-8").read()
tree = ast.parse(src)
CONST_NAMES = ("OBS_DIM", "MAX_PLAYERS", "MAX_HEROES", "MAX_TOWNS",
               "LOCAL_WIN", "GLOBAL_GRID", "MAX_LEVELS")
parts = []
for node in tree.body:
    if isinstance(node, ast.Assign) and any(
        isinstance(t, ast.Name) and t.id in CONST_NAMES for t in node.targets
    ):
        parts.append(ast.get_source_segment(src, node))
    if isinstance(node, ast.FunctionDef) and node.name == "_strategic_state_to_obs":
        parts.append(ast.get_source_segment(src, node))
ns = {"np": np, "_sr": sr, "StrategicState": sr.StrategicState}  # 注解/常量需要
exec("\n\n".join(parts), ns)
to_obs = ns["_strategic_state_to_obs"]
OBS_DIM = ns["OBS_DIM"]

fails = []


def chk(name, cond):
    if cond:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}")
        fails.append(name)


chk("strategic_reader 常量 LOCAL_WIN=15/GLOBAL_GRID=32/MAX_LEVELS=2",
    (sr.LOCAL_WIN, sr.GLOBAL_GRID, sr.MAX_LEVELS) == (15, 32, 2))
chk("strategic_env OBS_DIM == 2689", OBS_DIM == 2689)
chk("strategic_env 常量与 reader 一致",
    (ns["LOCAL_WIN"], ns["GLOBAL_GRID"], ns["MAX_LEVELS"]) == (15, 32, 2))

# 3. 构造假 state, 填哨兵值
st = sr.StrategicState()
st.day, st.week, st.month = 5, 2, 1
st.current_player = 0
st.map_width, st.map_height = 64, 64
st.has_underground = 1
st.player_count = 2
st.players[0].color = 7
st.players[0].human = 1
st.players[0].gold = 1234
st.heroes[0].id = 1
st.heroes[0].owner = 7
st.heroes[0].level = 5
st.heroes[0].army_count[0] = 3
st.heroes[0].army_count[6] = 9
st.heroes[2].id = 3          # 跳空槽后第 3 个英雄
st.heroes[2].exp = 999
st.heroes[7].id = 8          # 第 8 个英雄槽 — 8 个全装下
st.heroes[7].mana = 77
st.towns[0].id = 100
st.towns[0].owner = 7
st.towns[0].buildings = 5
st.towns[0].garrison[0] = 6
st.towns[0].gold_income = 2500
st.towns[1].id = 101
st.towns[1].pos_x = 10
st.local_tiles[0][0] = 3
st.local_tiles[0][1] = 2
st.local_tiles[7][7] = 1
st.local_tiles[14][14] = 1
st.global_explored[0][0][0] = 1
st.global_explored[0][5][7] = 1
st.global_explored[1][0][0] = 1
st.global_explored[1][31][31] = 1
st.active_hero = 2
st.passable[0] = 1
st.passable[7] = 1

obs = to_obs(st)

print("\n== 哨兵布局验证 ==")
chk("shape == (2689,)", obs.shape == (2689,))
chk("dtype == float32", obs.dtype == np.float32)

# global [0:8]
chk("obs[0]=day=5", obs[0] == 5)
chk("obs[6]=has_underground=1", obs[6] == 1)
chk("obs[7]=player_count=2", obs[7] == 2)

# players [8:104]
chk("obs[8]=player0.color=7", obs[8] == 7)
chk("obs[10]=player0.gold=1234", obs[10] == 1234)
chk("obs[20]=player1.color=0 (player_count=2 后槽位保持 0)", obs[20] == 0)

# heroes [104:288]  (23 字段: id,owner,posx,posy,posz,mov,maxmov,level,att,def,pow,know,mana,maxmana,exp,army[7],in_battle)
chk("obs[104]=hero0.id=1", obs[104] == 1)
chk("obs[105]=hero0.owner=7", obs[105] == 7)
chk("obs[111]=hero0.level=5", obs[111] == 5)
chk("obs[119]=hero0.army[0]=3", obs[119] == 3)
chk("obs[125]=hero0.army[6]=9", obs[125] == 9)
chk("obs[126]=hero0.in_battle=0", obs[126] == 0)
chk("obs[150]=hero2.id=3 (跳空槽)", obs[150] == 3)
chk("obs[164]=hero2.exp=999", obs[164] == 999)
chk("obs[265]=hero7.id=8 (第 8 槽全装下)", obs[265] == 8)
chk("obs[277]=hero7.mana=77", obs[277] == 77)
chk("obs[127:150] hero1 空槽全 0", np.all(obs[127:150] == 0))

# towns [288:400]  (14 字段: id,owner,posx,posy,posz,buildings,garrison[7],gold_income)
chk("obs[288]=town0.id=100", obs[288] == 100)
chk("obs[289]=town0.owner=7", obs[289] == 7)
chk("obs[293]=town0.buildings=5", obs[293] == 5)
chk("obs[294]=town0.garrison[0]=6", obs[294] == 6)
chk("obs[301]=town0.gold_income=2500", obs[301] == 2500)
chk("obs[302]=town1.id=101", obs[302] == 101)
chk("obs[304]=town1.pos_x=10", obs[304] == 10)
chk("obs[316:330] town2 空槽全 0", np.all(obs[316:330] == 0))

# local window [400:625]  行主序
chk("obs[400]=local[0][0]=3", obs[400] == 3)
chk("obs[401]=local[0][1]=2", obs[401] == 2)
chk("obs[512]=local[7][7]=1", obs[512] == 1)
chk("obs[624]=local[14][14]=1", obs[624] == 1)

# global explored [625:2673]  (z, gy, gx) 顺序, 先 z=0 再 z=1
chk("obs[625]=gexpl[0][0][0]=1", obs[625] == 1)
chk("obs[792]=gexpl[0][5][7]=1", obs[792] == 1)
chk("obs[1648]=gexpl[0][31][31]=0 (未设置)", obs[1648] == 0)
chk("obs[1649]=gexpl[1][0][0]=1 (z=1 层起点)", obs[1649] == 1)
chk("obs[2672]=gexpl[1][31][31]=1 (z=1 层终点)", obs[2672] == 1)

# active_hero [2673:2681]
chk("obs[2673]=active_hero=2", obs[2673] == 2)
chk("obs[2674:2681] 保留 0", np.all(obs[2674:2681] == 0))

# passable [2681:2689]
chk("obs[2681]=passable[0]=1", obs[2681] == 1)
chk("obs[2688]=passable[7]=1", obs[2688] == 1)

# 4. 全满状态: 所有槽位/所有字段有效, 验证无越界/无错位
print("\n== 全满状态验证 ==")
st2 = sr.StrategicState()
st2.day, st2.week, st2.month, st2.current_player = 1, 1, 1, 1
st2.map_width, st2.map_height, st2.has_underground, st2.player_count = 1, 1, 1, 8
for i in range(8):
    p = st2.players[i]
    p.color = i + 1; p.human = 1; p.gold = 100 + i
    p.wood = p.mercury = p.ore = p.sulfur = p.crystal = p.gems = i + 1
    p.hero_count, p.town_count, p.alive = 1, 1, 1
    h = st2.heroes[i]
    h.id = i + 1; h.owner = i + 1
    h.pos_x, h.pos_y, h.pos_z = 1, 1, 1
    h.movement, h.max_movement, h.level = 1, 1, 1
    h.attack, h.defense, h.power, h.knowledge = 1, 1, 1, 1
    h.mana, h.max_mana, h.exp = 1, 1, 1
    for ai in range(7):
        h.army_count[ai] = ai + 1
    h.in_battle = 1
    t = st2.towns[i]
    t.id = i + 1; t.owner = i + 1
    t.pos_x, t.pos_y, t.pos_z = 1, 1, 1
    t.buildings = 1
    for ai in range(7):
        t.garrison[ai] = ai + 1
    t.gold_income = 100 + i
for z in range(2):
    for gy in range(32):
        for gx in range(32):
            st2.global_explored[z][gy][gx] = 1
for li in range(15):
    for lj in range(15):
        st2.local_tiles[li][lj] = 1
st2.active_hero = 5
for di in range(8):
    st2.passable[di] = 1
obs2 = to_obs(st2)
chk("shape (2689,)", obs2.shape == (2689,))
chk("obs[8]=player0.color=1", obs2[8] == 1)
chk("obs[265]=hero8.id=8", obs2[265] == 8)
chk("obs[288+7*14]=town8.id=8", obs2[288 + 7 * 14] == 8)
chk("obs[288+7*14+13]=town8.gold_income=107", obs2[288 + 7 * 14 + 13] == 107)
chk("obs[400:625] local 全 1", np.all(obs2[400:625] == 1))
chk("obs[625:2673] gexpl 全 1", np.all(obs2[625:2673] == 1))
chk("obs[2673]=active_hero=5", obs2[2673] == 5)
chk("obs[2681:2689] passable 全 1", np.all(obs2[2681:2689] == 1))

# 5. 结构性不变量: 全满状态非零元素数
#   global 8 + players 96 + heroes 184 + towns 112 + local 225 + gexpl 2048
#   + active_hero 1 (保留段强制 0) + passable 8 = 2682
expected_nz = 8 + 96 + 184 + 112 + 225 + 2048 + 1 + 8
chk(f"全满非零元素数 == {expected_nz} (2682)", np.count_nonzero(obs2) == expected_nz)

print()
if fails:
    print(f"RESULT: {len(fails)} FAILED -> {fails}")
    sys.exit(1)
print("RESULT: ALL PASS — OBS schema v2 布局验证通过 (2689 维)")
