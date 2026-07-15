import ctypes, struct, sys, os
sys.path.insert(0, '.')

lib = ctypes.CDLL('/home/administrator/vcmi-native/rel/bin/libmlclient.so')

import gymnasium
from vcmi_gym.envs.v13.vcmi_env import VcmiEnv
gymnasium.register(id='Z', entry_point='vcmi_gym.envs.v13.vcmi_env:VcmiEnv', disable_env_checker=True, order_enforce=False)

env = gymnasium.make('Z', mapname='gym/A2.vmap', max_steps=5,
    opponent='BattleAI', vcmi_stats_mode='disabled',
    vcmi_loglevel_global='error', user_timeout=10, boot_timeout=10)

obs, info = env.reset()
print('reset done -- reading state')

ptr = ctypes.c_void_p.in_dll(lib, 'g_strategic_state')
val = ptr.value
print('ptr:', hex(val or 0))
if val:
    data = ctypes.string_at(val, 256)
    day = struct.unpack_from('i', data)[0]
    print('day=%d' % day)
    print('PHASE A: SUCCESS' if day > 0 else 'day=0')
else:
    print('NULL')

os._exit(0)
