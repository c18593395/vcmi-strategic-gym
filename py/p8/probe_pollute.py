import socket, time, subprocess, os
BIN = "/home/administrator/vcmi-native/rel/bin"
env = dict(os.environ); env["VCMI_QUERY_DIAG"] = "1"
subprocess.run(["pkill", "-f", "vcmiserver"], capture_output=True)
time.sleep(1)
srv = subprocess.Popen([BIN + "/vcmiserver", "--port=3030"], cwd=BIN,
                       stdout=open("/tmp/p6_srv.log", "w"), stderr=subprocess.STDOUT, env=env)
time.sleep(3)
s = socket.create_connection(("127.0.0.1", 3030), 2); s.close()
print("probe done", flush=True)
time.sleep(2)
for i in range(3):
    try:
        s2 = socket.create_connection(("127.0.0.1", 3030), 2)
        print(f"real connect {i+1}: OK", flush=True); s2.close(); break
    except Exception as e:
        print(f"real connect {i+1}: {e}", flush=True)
    time.sleep(1)
print("--- srv log ---", flush=True)
os.system('grep -E "connection|Connection|Listening" /tmp/p6_srv.log | head -8')
srv.terminate(); time.sleep(0.5); srv.kill()
