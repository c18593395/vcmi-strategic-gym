#!/usr/bin/env python3
# headless 客户端在 ENGINE=nullptr 下连接失败即崩 (fork 1.8 上游 bug: onConnectionFailed 无 ENGINE 空指针防护)。
# 因此 headless --testmap 必须保证 server 已在监听。方案: 先让 server 打印 Listening 后再拉 client。
# 本脚本: 起 server -> 轮询 3030 端口通 -> 起 client1 -> 观察是否还崩
import subprocess, os, time, socket

BIN = '/home/administrator/vcmi-native/rel/bin'
env = dict(os.environ)
env['VCMI_QUERY_DIAG'] = '1'
env['VCMI_TESTMAP_ONLYAI'] = '1'

subprocess.run(['pkill', '-f', 'vcmiserver'], capture_output=True)
subprocess.run(['pkill', '-f', 'vcmiclient'], capture_output=True)
time.sleep(1)

srv = subprocess.Popen([BIN + '/vcmiserver', '--port=3030'], cwd=BIN,
                       stdout=open('/tmp/p2_srv.log', 'w'), stderr=subprocess.STDOUT, env=env)
up = False
for i in range(20):
    time.sleep(0.5)
    try:
        s = socket.create_connection(('127.0.0.1', 3030), 1)
        s.close()
        up = True
        print(f'server listening after {0.5*(i+1):.1f}s')
        break
    except Exception:
        pass
if not up:
    print('SERVER NEVER LISTENED'); srv.kill(); raise SystemExit(1)

cli = subprocess.Popen([BIN + '/vcmiclient', '--testmap', 'Maps/A Warm and Familiar Place.h3m',
                        '--donotstartserver', '--headless'], cwd=BIN,
                       stdout=open('/tmp/p2_cli.log', 'w'), stderr=subprocess.STDOUT, env=env)
for i in range(45):
    time.sleep(2)
    if cli.poll() is not None:
        print(f'cli EXITED rc={cli.returncode} at {2*(i+1)}s')
        break
    print(f'{2*(i+1)}s alive, cli log tail: {open("/tmp/p2_cli.log").readlines()[-1].strip()[:80]}')
else:
    print('cli survived 90s')

srv.terminate(); cli.terminate()
time.sleep(1)
srv.kill(); cli.kill()
print('--- srv tail ---')
os.system('tail -5 /tmp/p2_srv.log')
