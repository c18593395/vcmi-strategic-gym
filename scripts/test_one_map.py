"""Single h3m test — one at a time"""
import sys,os,time,numpy as np
sys.path.insert(0,'/mnt/d/Bigdata/hero3_fresh')
os.environ['STRATEGIC_STATE_LIB']='/home/administrator/vcmi-native/rel/bin/libmlclient.so'

# Get mapname from args
mapname = sys.argv[1] if len(sys.argv)>1 else "Key to Victory.h3m"
from vcmi_gym.envs.v13.strategic_env import StrategicEnv

env = StrategicEnv(mapname=mapname,max_turns=3,
    vcmi_loglevel_global="warn",vcmi_loglevel_ai="error",
    vcmienv_loglevel="WARN",red="MMAI_USER",blue="StupidAI",
    random_heroes=1,boot_timeout=60)

t0=time.time()
obs,info=env.reset()
nz=np.count_nonzero(obs)
print(f"RESET nz={nz} day={info['day']} dt={time.time()-t0:.1f}s")

if nz>0:
    t0=time.time()
    obs,r,t,tr,info=env.step(10)
    print(f"STEP  nz={np.count_nonzero(obs)} dt={time.time()-t0:.1f}s t={t}")
env.close()
print("DONE")
