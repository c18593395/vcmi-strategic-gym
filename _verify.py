import sys, numpy as np
sys.path.insert(0,"/mnt/d/Bigdata/hero3_fresh")
from vcmi_gym.envs.v13.strategic_env import StrategicEnv
import os
os.environ['LD_LIBRARY_PATH']='/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-native/rel/bin/AI:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel'
e=StrategicEnv(mapname='For Sale.h3m',max_turns=2,vcmi_loglevel_global='error',vcmi_loglevel_ai='error',vcmienv_loglevel='CRITICAL',red='StupidAI',blue='StupidAI',random_heroes=1,boot_timeout=10,vcmi_timeout=15)
o,_=e.reset()
p=[int(x) for x in o[-8:]]
print('1: passable='+str(p)+' nz='+str(sum(p)))
assert sum(p) < 8, 'all-1 passability'
a=[d for d in range(8) if p[d]][0]
n,r,d,t,_=e.step(a)
print('2: a=%d (%d,%d)->(%d,%d) r=%.1f done=%s' % (a, o[106], o[107], n[106], n[107], r, d))
assert int(o[106]) != int(n[106]), 'hero stuck'
assert r > 0, 'no reward: %.1f' % r
assert not d and not t, 'episode ended'
print('PASS')
