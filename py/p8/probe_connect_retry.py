#!/usr/bin/env python3
# 最小复现: server 起来后, python connect 为何 refused?
# 猜测: server 的 "Listening" 在 accept loop 就绪前打印; port probe 成功后立刻断开
# (probe 本身占了一个 accept!), 随后 backlog 满/状态异常导致真连接被拒?
# 测试: 不做 port probe, 直接 connect + 重试
import socket, time, subprocess, os
BIN = "/home/administrator/vcmi-native/rel/bin"
env = dict(os.environ); env["VCMI_QUERY_DIAG"] = "1"
subprocess.run(["pkill", "-f", "vcmiserver"], capture_output=True)
time.sleep(1)
srv = subprocess.Popen([BIN + "/vcmiserver", "--port=3030"], cwd=BIN,
                       stdout=open("/tmp/p5_srv.log", "w"), stderr=subprocess.STDOUT, env=env)
for attempt in range(15):
    time.sleep(1)
    try:
        s = socket.create_connection(("127.0.0.1", 3030), 2)
        print(f"attempt {attempt+1}: CONNECTED")
        s.close()
        break
    except Exception as e:
        print(f"attempt {attempt+1}: {e}")
srv.terminate(); srv.kill()
