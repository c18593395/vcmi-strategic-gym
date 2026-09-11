#!/usr/bin/env python3
"""
P8-B 阶段3 数据源捕获 — 跑真实局, dump 英雄/位置相关包的原始字节
目标: 确认 Python 外挂手里有哪些数据能定位 "我的英雄 OI + 位置"
  抓: GiveHero(115) / ChangeObjPos(101) / NewObject(121) / TryMoveHero(109) / SetResources(91)
"""
import sys, os, time, uuid as uuidlib, subprocess, threading, struct

sys.path.insert(0, 'D:/Bigdata/hero3_fresh/py')
from vcmi_protocol.connection import VCMITCPConnection
from vcmi_protocol.serialization import BinarySerializer, BinaryDeserializer
from vcmi_protocol.packs import LobbyClientConnected

HOST='127.0.0.1'; PORT=3030; BIN=r'D:\vcmi-fork-build\bin'
MY_COLOR = 0

def kill_all():
    for exe in ('VCMI_server.exe','VCMI_client.exe'):
        subprocess.run(['taskkill','/F','/IM',exe],capture_output=True)
    time.sleep(1)

def read_top(d):
    """顶层包 = isNull + pid + tid, 返回 (tid, deser, raw_tid_bytes)"""
    if d.read_bool(): return None, d
    d.read_int()
    return d.read_int(), d

def main():
    kill_all()
    srv_log = open(r'C:\Users\Administrator\AppData\Local\Temp\p8c_srv.log','w')
    srv = subprocess.Popen([BIN+r'\VCMI_server.exe','--port=3030'],cwd=BIN,stdout=srv_log,stderr=subprocess.STDOUT)
    time.sleep(9)

    conn = VCMITCPConnection(HOST, PORT)
    if not conn.connect():
        print('[FAIL] connect'); return 1
    conn.send_frame(LobbyClientConnected(uuid=str(uuidlib.uuid4()), names=['PyHost'], mode=0).to_bytes())
    time.sleep(1)
    env = dict(os.environ); env['VCMI_TESTMAP_ONLYAI']='1'
    cli = subprocess.Popen([BIN+r'\VCMI_client.exe','--testmap','Maps/Twins.h3m','--donotstartserver','--serverport','3030','--headless'],
                           cwd=BIN,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT,env=env)
    # 等 client1 join (第2个 UpdateState) 再 ChangeHost — 时序同 p8be_host_start.py
    us=0; t0=time.time()
    while time.time()-t0 < 15:
        data = conn.recv_frame()
        if not data: continue
        d=BinaryDeserializer(data)
        if d.read_bool(): continue
        d.read_int(); tid=d.read_int()
        if tid==226:
            us+=1
            if us>=2: break
    conn.send_frame(bytes([0, 0, 0xe1, 0x01, 0x02]))
    print(f'[evt] client1 joined (us={us}), ChangeHost sent')

    captured = []
    def dump(data, tag):
        d = BinaryDeserializer(data)
        tid, d = read_top(d)
        if tid is None: return
        if tid in (115,101,121,109,91):
            # 顶层后剩余 = 包体
            body = data[3:]  # 近似: isNull+pid+tid 变长, 用实际 pos
            try:
                print(f'[{tag}] tid={tid} {len(data)}B raw={data.hex()}')
            except: pass
        return tid

    t0=time.time(); n_turns=0; first_turn_mine=False
    while time.time()-t0 < 60:
        data = conn.recv_frame()
        if not data: continue
        d = BinaryDeserializer(data)
        if d.read_bool(): continue
        d.read_int(); tid=d.read_int()
        if tid==224:
            # dump StartGame 全状态到盘上离线分析
            open(r'C:\Users\Administrator\AppData\Local\Temp\p8c_startgame.bin','wb').write(data)
            print(f'[evt] StartGame (171KB 全状态) dumped {len(data)}B -> p8c_startgame.bin')
        if tid in (115,101,121,109,91):
            print(f'[DUMP {tid}] {len(data)}B raw={data.hex()}')
        if tid==88:
            qid=d.read_int(); player=d.read_int()
            if player==MY_COLOR and not first_turn_mine:
                first_turn_mine=True
                print(f'[DUMP 88-mine] my turn start qid={qid} player={player} raw={data.hex()}')
                n_turns+=1
                # 抓到我回合后多等 8s, 让 server 广播本回合的 SetResources/TryMoveHero 等
                t_inner=time.time()
                while time.time()-t_inner < 8:
                    data2 = conn.recv_frame()
                    if not data2: continue
                    d2=BinaryDeserializer(data2)
                    if d2.read_bool(): continue
                    d2.read_int(); tid2=d2.read_int()
                    if tid2 in (115,101,121,109,91,116,86,108):
                        print(f'[DUMP2 {tid2}] {len(data2)}B raw={data2.hex()}')
                break
    print(f'\n=== 捕获结束 ===')
    conn.disconnect()
    kill_all()
    return 0

if __name__=='__main__':
    sys.exit(main())
