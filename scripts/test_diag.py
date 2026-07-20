"""Diagnostic: per-step state changes on Key to Victory.h3m"""
import sys,os,time,numpy as np
sys.path.insert(0,'/mnt/d/Bigdata/hero3_fresh')
os.environ['STRATEGIC_STATE_LIB']='/home/administrator/vcmi-native/rel/bin/libmlclient.so'
from vcmi_gym.envs.v13.strategic_env import StrategicEnv

env=StrategicEnv(mapname="Key to Victory.h3m",max_turns=10,
    vcmi_loglevel_global="error",vcmi_loglevel_ai="error",
    vcmienv_loglevel="ERROR",red="MMAI_USER",blue="StupidAI",
    random_heroes=1,boot_timeout=60)

obs,_=env.reset()
state=env.get_state_raw()
prev_gold=[state.players[i].gold for i in range(state.player_count)]
prev_hero=[state.players[i].hero_count for i in range(state.player_count)]
print(f"day={state.day} p0_gold={prev_gold[0]} p1_gold={prev_gold[1]}",flush=True)

for step in range(5):
    a=int(env.action_space.sample())
    obs,r,_,_,_=env.step(a)
    state=env.get_state_raw()
    g0=state.players[0].gold; g1=state.players[1].gold
    h0=state.players[0].hero_count; h1=state.players[1].hero_count
    dg0=g0-prev_gold[0]; dg1=g1-prev_gold[1]
    dh0=h0-prev_hero[0]; dh1=h1-prev_hero[1]
    print(f"  step{step} a={a} r={r:+.2f} | p0: gold{g0:+d}({dg0:+d}) hero{h0}({dh0:+d}) | p1: gold{g1:+d}({dg1:+d}) hero{h1}({dh1:+d})",flush=True)
    prev_gold=[g0,g1]; prev_hero=[h0,h1]
