#!/usr/bin/env python3
# headless client segfault 定位: 用 logLocation 拿完整日志, 看连接失败前的最后行为
import subprocess, os, time, socket

BIN = '/home/administrator/vcmi-native/rel/bin'
env = dict(os.environ)
env['VCMI_TESTMAP_ONLYAI'] = '1'

subprocess.run(['pkill', '-f', 'vcmiserver'], capture_output=True)
subprocess.run(['pkill', '-f', 'vcmiclient'], capture_output=True)
time.sleep(1)

srv = subprocess.Popen([BIN + '/vcmiserver', '--port=3030'], cwd=BIN,
                       stdout=open('/tmp/p3_srv.log', 'w'), stderr=subprocess.STDOUT, env=env)
os.makedirs('/tmp/p3logs', exist_ok=True)
srvlog = open('/tmp/p3_srv.log', 'w')
up = False
for i in range(20):
    time.sleep(0.5)
    try:
        s = socket.create_connection(('127.0.0.1', 3030), 1)
        s.close(); up = True; break
    except Exception:
        pass
print('server up:', up)

cli = subprocess.Popen([BIN + '/vcmiclient', '--testmap', 'Maps/A Warm and Familiar Place.h3m',
                        '--donotstartserver', '--headless', '--logLocation', '/tmp/p3logs'],
                       cwd=BIN, stdout=open('/tmp/p3_cli.log', 'w'), stderr=subprocess.STDOUT, env=env)
for i in range(30):
    time.sleep(2)
    if cli.poll() is not None:
        print(f'cli EXITED rc={cli.returncode} at {2*(i+1)}s')
        break
srv.terminate(); cli.terminate(); time.sleep(1); srv.kill(); cli.kill()
print('--- full client log ---')
os.system('grep -vE "^loading|redundant" /tmp/p3logs/VCMI_Client_log.txt | tail -30')
