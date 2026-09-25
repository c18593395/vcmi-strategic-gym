#!/usr/bin/env python3
# 直接跑 vcmiclient --testmap 看卡在哪: 观察无 server 模式下 (端口不通) 的行为
import os
import subprocess, os, time
BIN = os.environ.get("BIN", '/home/administrator/vcmi-native/rel/bin')
MAP = 'Maps/A Warm and Familiar Place.h3m'
env = dict(os.environ)
env['VCMI_TESTMAP_ONLYAI'] = '1'
log = open('/tmp/probe_cli.log', 'w')
p = subprocess.Popen([BIN + '/vcmiclient', '--testmap', MAP,
                      '--donotstartserver', '--serverport', '3030', '--headless'],
                     cwd=BIN, stdout=log, stderr=subprocess.STDOUT, env=env)
for i in range(40):
    time.sleep(2)
    if p.poll() is not None:
        print(f'EXITED rc={p.returncode} after {2*(i+1)}s')
        break
    if i % 5 == 4:
        os.system(f'tail -1 /tmp/probe_cli.log')
print('--- final tail ---')
os.system('tail -3 /tmp/probe_cli.log')
p.terminate(); time.sleep(0.5); p.kill()
