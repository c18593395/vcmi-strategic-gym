"""Key to Victory.h3m — single test"""
import sys,os,time,numpy as np
sys.path.insert(0,'/mnt/d/Bigdata/hero3_fresh')
os.environ['STRATEGIC_STATE_LIB']='/home/administrator/vcmi-native/rel/bin/libmlclient.so'
from vcmi_gym.envs.v13.strategic_env import StrategicEnv

env = StrategicEnv(mapname="Key to Victory.h3m",max_turns=3,
    vcmi_loglevel_global="warn",vcmi_loglevel_ai="error",
    vcmienv_loglevel="WARN",red="MMAI_USER",blue="StupidAI",
    random_heroes=1,boot_timeout=60)

obs,info=env.reset()
print(f"reset nz={np.count_nonzero(obs)} day={info['day']}")

t0=time.time()
obs,r,t,tr,info=env.step(10)
print(f"step  nz={np.count_nonzero(obs)} dt={time.time()-t0:.1f}s t={t}")

if not t:
    t0=time.time()
    obs,r,t,tr,info=env.step(10)
    print(f"step2 nz={np.count_nonzero(obs)} dt={time.time()-t0:.1f}s t={t}")

env.close()
print("PASS")
