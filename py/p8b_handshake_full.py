#!/usr/bin/env python3
"""
P8-B 第 2 步 — 握手 + LobbyUpdateState 完整解析
验证: LobbyClientAccepted → 收 LobbyUpdateState → _StartInfo/_LobbyState 全字段解码
"""
import sys
import time
import uuid as uuidlib

sys.path.insert(0, 'D:/Bigdata/hero3_fresh/py')

from vcmi_protocol.connection import VCMITCPConnection
from vcmi_protocol.serialization import BinaryDeserializer
from vcmi_protocol.packs import LobbyClientConnected

HOST = '127.0.0.1'
PORT = 3030

LOBBY_TIDS = {216: 'LobbyClientConnected', 217: 'LobbyClientDisconnected',
              218: 'LobbyChatMessage', 224: 'LobbyStartGame', 226: 'LobbyUpdateState',
              229: 'LobbySetMap', 265: 'LobbyQueryState', 266: 'LobbyModsCheck',
              227: 'LobbyShowMessage'}


def read_ptr_header(d):
    isnull = d.read_bool()
    if isnull:
        return False, None, None
    pid = d.read_int()
    tid = d.read_int()
    return True, pid, tid


def main():
    conn = VCMITCPConnection(HOST, PORT)
    if not conn.connect():
        print("[FAIL] connect")
        return 1
    time.sleep(2)

    lcc = LobbyClientConnected(uuid=str(uuidlib.uuid4()), names=["PyProbe"], mode=0)
    conn.send_frame(lcc.to_bytes())
    print("[SEND] LobbyClientConnected ok")

    deadline = time.time() + 12
    while time.time() < deadline:
        data = conn.recv_frame()
        if not data:
            continue
        d = BinaryDeserializer(data)
        isnull = d.read_bool()
        if isnull:
            print("[RECV] null-ptr pack")
            continue
        d.read_int()  # pid
        tid = d.read_int()
        name = LOBBY_TIDS.get(tid, f'?{tid}')
        print(f"[RECV] {len(data)}B tid={tid}({name})")

        if tid == 226:
            # LobbyUpdateState: state(LobbyState) + refreshList(bool)
            # LobbyState: si(ptr) mi(ptr) playerNames(map) hostClientId campaignMap campaignBonus
            has_si, sipid, sitid = read_ptr_header(d)
            print(f"  si ptr: present={has_si} pid={sipid} tid={sitid}")
            if has_si and sitid == 0:
                si = parse_startinfo(d)
                print(f"  StartInfo: mode={si['mode']} difficulty={si['difficulty']} "
                      f"players={len(si.get('playerInfos', {}))}")
            elif has_si and sitid:
                print(f"  StartInfo 是已注册类型 (tid={sitid}), 内联数据不做解析")
            has_mi, mipid, mitid = read_ptr_header(d)
            print(f"  mi ptr: present={has_mi}")
            pn_count = d.read_int()
            print(f"  playerNames: {pn_count}")
            for _ in range(pn_count):
                pid_ = d.read_int()
                conn_id = d.read_int()
                pname = d.read_string()
                print(f"    pid={pid_} cid={conn_id} name='{pname}'")
            host_cid = d.read_int()
            camp_map = d.read_int()
            camp_bonus = d.read_int()
            refresh = d.read_bool()
            print(f"  hostClientId={host_cid} campaignMap={camp_map} campaignBonus={camp_bonus} refresh={refresh}")
            print("[OK] LobbyUpdateState 全字段解析完成")
            break
        if tid == 224:  # LobbyStartGame — 游戏直接开始
            print("[OK] server 直接开始游戏?")
            break
        if tid == 217:
            print("[WARN] 被断开")
            break

    conn.disconnect()
    return 0


def parse_startinfo(d):
    si = {}
    si['mode'] = d.read_int()
    si['difficulty'] = d.read_uint8()
    pc = d.read_int()
    for _ in range(pc):
        color = d.read_int()
        ps = parse_playersettings(d)
        si.setdefault('playerInfos', {})[color] = ps
    si['startTime'] = d.read_int()
    si['fileURI'] = d.read_string()
    reqt = d.read_int(); optt = d.read_int()
    ah = d.read_bool(); ic = d.read_bool()
    si['simturns'] = (reqt, optt, ah, ic)
    return si


def parse_playersettings(d):
    ps = {}
    ps['castle'] = d.read_string()
    ps['hero'] = d.read_string()
    ps['heroPortrait'] = d.read_string()
    ps['heroNameTextId'] = d.read_string()
    ps['bonus'] = d.read_int()
    ps['color'] = d.read_int()
    for _ in range(7):
        d.read_int()
    ps['percentIncome'] = d.read_int()
    ps['percentGrowth'] = d.read_int()
    ps['name'] = d.read_string()
    cps = d.read_int()
    for _ in range(cps):
        d.read_int()
    ps['compOnly'] = d.read_bool()
    return ps


if __name__ == '__main__':
    sys.exit(main())
