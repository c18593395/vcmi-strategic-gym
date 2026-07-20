"""Single h3m episode timing test"""
import sys,os,time,numpy as np
sys.path.insert(0,'/mnt/d/Bigdata/hero3_fresh')
os.environ['STRATEGIC_STATE_LIB']='/home/administrator/vcmi-native/rel/bin/libmlclient.so'
from vcmi_gym.envs.v13.strategic_env import StrategicEnv

for m in ['Key to Victory.h3m','Golems Aplenty.h3m']:
    t0=time.time()
    env=StrategicEnv(mapname=m,max_turns=50,vcmi_loglevel_global='error',
        vcmi_loglevel_ai='error',vcmienv_loglevel='ERROR',
        red='MMAI_USER',blue='StupidAI',random_heroes=1,boot_timeout=120)
    obs,_=env.reset()
    print(f"{m} reset dt={time.time()-t0:.0f}s nz={np.count_nonzero(obs)}",flush=True)
    for i in range(5):
        t1=time.time()
        obs,r,t,tr,_=env.step(10)
        print(f"  step{i} dt={time.time()-t1:.0f}s r={r:+.2f} nz={np.count_nonzero(obs)} t={t}",flush=True)
        if t or tr: break
    print(f"total={time.time()-t0:.0f}s",flush=True)
    break  # just first map for timing
