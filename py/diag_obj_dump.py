#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""0910 偏移诊断: 引擎 hero/城对象位置 vs vmap 静态坐标对照 (T05 守卫假 +100 根因实证)
用法 (WSL): python3 py/diag_obj_dump.py T05_adventure_36X36_01.vmap [T06_adventure_72X72_01.vmap ...]
单局 reset 即停, 不训练; 每图 ~1-2 分钟。
"""
import sys, os, json, zipfile, time
os.environ["STRATEGIC_STATE_LIB"] = "/home/administrator/vcmi-native/rel/bin/libmlclient.so"
sys.path.insert(0, "/mnt/d/Bigdata/hero3_fresh")
from vcmi_gym.envs.v13.strategic_env import StrategicEnv

MAP_DIR = "/mnt/d/Bigdata/hero3_fresh/maps/training/"

def static_coords(mapname):
    p = MAP_DIR + mapname
    with zipfile.ZipFile(p) as z:
        objs = json.loads(z.read("objects.json"))
    heroes = [(int(o["x"]), int(o["y"])) for k, o in objs.items() if k.startswith("hero_")]
    monsters = [(int(o["x"]), int(o["y"]), o.get("subtype", "?")) for k, o in objs.items() if k.startswith("monster_")]
    towns = [(int(o["x"]), int(o["y"]), o.get("options", {}).get("owner", "?")) for k, o in objs.items() if k.startswith("town_")]
    return heroes, monsters, towns

for mapname in sys.argv[1:]:
    heroes_s, monsters_s, towns_s = static_coords(mapname)
    print(f"\n===== {mapname} =====")
    print(f"  vmap静态: hero0={heroes_s[0] if heroes_s else '?'} 全hero={heroes_s}")
    print(f"  vmap静态: monsters={monsters_s}")
    print(f"  vmap静态: towns={towns_s}")
    env = StrategicEnv(
        mapname=mapname, max_turns=3,
        vcmi_loglevel_global="error", vcmi_loglevel_ai="error",
        vcmienv_loglevel="ERROR", red="StupidAI", blue="StupidAI",
        random_heroes=1, boot_timeout=180, vcmi_timeout=120,
        red_adventure_ai="MMAI", blue_adventure_ai="MMAI",
        reward_explore=0.0,
    )
    try:
        t0 = time.time()
        obs, info = env.reset()
        ah = int(obs[3203])
        b0 = 128 + ah * 26
        hx, hy = int(obs[b0 + 2]), int(obs[b0 + 3])
        print(f"  reset {time.time()-t0:.0f}s obs_nz={(obs>0).sum()} active_hero_slot={ah}")
        print(f"  引擎实测: hero_pos=({hx},{hy})  vs vmap hero0={heroes_s[0] if heroes_s else '?'}")
        towns_e = []
        for ti in range(8):
            tb = 336 + ti * 18
            tid = int(obs[tb])
            if tid > 0:
                towns_e.append((tid, int(obs[tb + 1]), int(obs[tb + 2]), int(obs[tb + 3])))
        print(f"  引擎实测: towns(id,owner,x,y)={towns_e}")
        print(f"  偏移(hero) = ({hx - heroes_s[0][0]},{hy - heroes_s[0][1]})" if heroes_s else "")
    except Exception as e:
        print(f"  EXC: {e}")
    finally:
        env.close()
print("\n[diag] done")
