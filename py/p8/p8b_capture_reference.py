#!/usr/bin/env python3
"""
P8-B 实验 2 — 假服务器: 捕获真实 VCMI client 发出的 LobbyClientConnected 参考字节
  1. 本脚本监听 3030 (假 server)
  2. 启动 VCMI_client.exe --testmap <map> --donotstartserver --serverport 3030
  3. 捕获客户端首包, 与 Python 生成的 LobbyClientConnected 逐字节对比
"""
import sys
import os
import socket
import struct
import threading
import time
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

HOST = '0.0.0.0'
PORT = 3030
CAPTURE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'p8b_captured_firstpack.bin')


def recv_exact(sock, n):
    buf = b''
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            return None
        buf += chunk
    return buf


def fake_server():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, PORT))
    srv.listen(1)
    print(f"[FAKE-SRV] listening on {PORT}")
    conn, addr = srv.accept()
    print(f"[FAKE-SRV] client connected from {addr}")

    # 读首包: 4B header + payload
    header = recv_exact(conn, 4)
    if header is None:
        print("[FAKE-SRV] client disconnected before sending")
        return
    size = struct.unpack('<I', header)[0]
    print(f"[FAKE-SRV] first frame: header={size}B")
    if size == 0:
        print("[FAKE-SRV] heartbeat — read next frame")
        header = recv_exact(conn, 4)
        size = struct.unpack('<I', header)[0]
    payload = recv_exact(conn, size)
    print(f"[FAKE-SRV] payload {len(payload)}B")
    with open(CAPTURE_FILE, 'wb') as f:
        f.write(payload)
    print(f"[FAKE-SRV] saved -> {CAPTURE_FILE}")

    # 保持连接 3s 让 client 不至于立刻断, 然后退出
    time.sleep(3)
    conn.close()
    srv.close()


def main():
    t = threading.Thread(target=fake_server, daemon=True)
    t.start()
    time.sleep(1)

    # 启动真实 client 连我们的假 server
    # --testmap 让它走 debugStartTest → resetStateForLobby → connectToServer
    # 需要一个 map; 用 fork 自带 Twins.h3m
    bin_dir = r'D:\vcmi-fork-build\bin'
    exe = bin_dir + r'\VCMI_client.exe'
    cmd = [exe, '--testmap', 'Maps/Twins.h3m', '--donotstartserver',
           '--serverport', str(PORT), '--headless']
    print(f"[RUN] {' '.join(cmd)}")
    proc = subprocess.Popen(cmd, cwd=bin_dir,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # 等捕获完成
    t.join(timeout=60)
    proc.kill()
    print("[DONE]")


if __name__ == '__main__':
    main()
