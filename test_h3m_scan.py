"""Two h3m maps quick test"""
import sys,os,time,numpy as np
sys.path.insert(0,'/mnt/d/Bigdata/hero3_fresh')
os.environ['STRATEGIC_STATE_LIB']='/home/administrator/vcmi-native/rel/bin/libmlclient.so'
from vcmi_gym.envs.v13.strategic_env import StrategicEnv

for m in ['Key to Victory.h3m','Golems Aplenty.h3m']:
    print(f'=== {m} ===')
    env = StrategicEnv(mapname=m,max_turns=3,vcmi_loglevel_global='warn',
        vcmi_loglevel_ai='error',vcmienv_loglevel='WARN',
        red='MMAI_USER',blue='StupidAI',random_heroes=1,boot_timeout=30)
    obs,info=env.reset()
    print(f'reset nz={np.count_nonzero(obs)} day={info["day"]}')
    if np.count_nonzero(obs)==0:
        env.close(); continue
    t0=time.time()
    obs,r,t,tr,info=env.step(10)
    print(f'step  nz={np.count_nonzero(obs)} dt={time.time()-t0:.1f}s')
    env.close()
print('DONE')
