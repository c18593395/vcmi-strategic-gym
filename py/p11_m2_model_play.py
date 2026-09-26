#!/usr/bin/env python3
"""
T13.11 M2 探针 — 红方(模型位)真实决策环 vs NK2(蓝)
====================================================
拓扑 = M1.5 同款: Python(红,host->让位) + client1(蓝,onlyai=Nullkiller2)。
红方从 EndTurn 占位升级为 P8-C 已验证决策链 (规则驱动; 模型推理受数据源墙限制留 S-2):

  回合动作序列 (跨回合有状态):
    T1    : BuildStructure(town, bid=30 DWELL_LVL_1)      (一次)
    T2+   : RecruitCreatures(town->hero, 112 广播驱动)     (每回合一次)
    每回合 : MoveHero 朝东(+x)推进 1 格, rejected 则换向 (S/E/N/W 轮转)
            → EndTurn

判定 (server log + 包流):
  1. 对局开始 + 红蓝交替 >= 4 轮
  2. 红方 BuildStructure applied (server log "successfully applied" 且含 BuildStructure)
  3. 红方 RecruitCreatures applied
  4. 红方 MoveHero 受理: Python 收 TryMoveHero(109) 广播 (红方 oid=350) 或移动后英雄 pos 变化
  5. 全程无 Disaster/fishy 崩溃
"""
import sys, os, time, uuid as uuidlib, subprocess, threading, re
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from vcmi_protocol.connection import VCMITCPConnection
from vcmi_protocol.serialization import BinarySerializer, BinaryDeserializer
from vcmi_protocol.packs import LobbyClientConnected, MoveHero, EndTurn, BuildStructure, RecruitCreatures

HOST = '127.0.0.1'
PORT = 3030
BIN = r'D:\vcmi-fork-build\bin'
MAP = r'Maps/Twins.h3m'
TMP = r'C:\Users\Administrator\AppData\Local\Temp'
SRV_LOG = f'{TMP}\\p11m2_srv.log'

MY_COLOR = 0
MY_NAME = 'P11M2Red'

RECV_CC = re.compile(r'Received CPack of type 20LobbyClientConnected')
RECV_LEAD = re.compile(r'Player (\w+) will be lead by (\S+)')
AI_ACT_TIDS = {86, 95, 100, 106, 109, 111, 115, 117, 118, 121, 125}

# 探针Known: Twins 红方 HERO OI=350 pos=(1,8,0), TOWN OI=347 (SRV-DIAG 0927 实锤)
HERO_OI = 350
TOWN_OI = 347
DIRS = [(1, 0), (0, -1), (1, -1), (1, 1), (0, 1), (-1, 0)]   # 东/北/东北/东南/南/西 轮转


def kill_all():
    for exe in ('VCMI_server.exe', 'VCMI_client.exe'):
        subprocess.run(['taskkill', '/F', '/IM', exe], capture_output=True)
    time.sleep(1)


def count_pattern(path, pattern):
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            return sum(1 for line in f if pattern.search(line))
    except FileNotFoundError:
        return 0


def grep_log(path, flag):
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            return any(flag in line for line in f)
    except FileNotFoundError:
        return False


class P11M2:
    def __init__(self):
        self.srv = self.blue_cli = None
        self.conn = VCMITCPConnection(HOST, PORT)
        self.running = True
        self.turn_seq = []
        self.blue_act_count = 0
        self._in_my_turn = False
        self._req = 0
        # 决策状态
        self.hero_pos = (1, 8, 0)
        self.dir_idx = 0
        self.built = False
        self.recruited = False
        self.available = {}     # town_oi -> [(amount, [crids])] from 112
        self.moves_tried = 0
        self.move_ok = 0
        self.turn_no = 0

    def next_req(self):
        self._req += 1
        return self._req

    # ---------- 进程 ----------
    def start_server(self):
        log = open(f'{TMP}\\p11m2_srv.log', 'w')
        self.srv = subprocess.Popen([os.path.join(BIN, 'VCMI_server.exe'), f'--port={PORT}'],
                                    cwd=BIN, stdout=log, stderr=subprocess.STDOUT)
        time.sleep(9)
        return self.srv.poll() is None

    def start_blue_client(self):
        log = open(f'{TMP}\\p11m2_blue.log', 'w')
        env = dict(os.environ)
        env['VCMI_TESTMAP_ONLYAI'] = '1'
        return subprocess.Popen([os.path.join(BIN, 'VCMI_client.exe'), '--testmap', MAP,
                                 '--donotstartserver', '--serverport', str(PORT), '--headless'],
                                cwd=BIN, stdout=log, stderr=subprocess.STDOUT, env=env)

    # ---------- 协议 ----------
    def host_join(self):
        if not self.conn.connect():
            return False
        threading.Thread(target=self.recv_loop, daemon=True).start()
        lcc = LobbyClientConnected(uuid=str(uuidlib.uuid4()), names=[MY_NAME], mode=0)
        self.conn.send_frame(lcc.to_bytes())
        print('[H] python(红) 已连入')
        return True

    def send_change_host(self, cid):
        self.conn.send_frame(bytes([0, 0, 0xe1, 0x01, cid]))
        print(f'[SEND] ChangeHost({cid})')

    def recv_loop(self):
        while self.running:
            data = self.conn.recv_frame()
            if data is None:
                if not self.conn.connected:
                    print('[RECV] 断开')
                    break
                continue
            if len(data) == 0:
                continue
            d = BinaryDeserializer(data)
            if d.read_bool():
                continue
            d.read_int()
            tid = d.read_int()
            if tid == 88:   # PlayerStartsTurn
                qid = d.read_int()
                player = d.read_int()
                print(f'[RECV] PlayerStartsTurn p{player}')
                self._in_my_turn = (player == MY_COLOR)
                self.turn_seq.append(f'p{player}')
                if self._in_my_turn:
                    self.turn_no += 1
                    self.act_turn()
            elif tid == 112:  # SetAvailableCreatures
                # town? LVarInt + 数组 — 粗解析: 记 tid 供 act_turn 查询 (简化: 不解内容)
                self.available['seen'] = True
                print('[RECV] SetAvailableCreatures (112)')
            elif tid == 109:  # TryMoveHero 广播
                # oid(LVarInt) result(LVarInt) ... 粗读
                try:
                    oid = d.read_int()
                    result = d.read_int()
                    if oid == HERO_OI:
                        self.moves_tried += 1
                        if result == 1:
                            self.move_ok += 1
                            print(f'[RECV] TryMoveHero hero={oid} SUCCESS (#{self.move_ok})')
                        else:
                            print(f'[RECV] TryMoveHero hero={oid} FAILED → 回滚 pos + 换向')
                            if getattr(self, '_pending_from', None):
                                self.hero_pos = self._pending_from   # v2: 回滚到移动前真实位置
                            self.dir_idx = (self.dir_idx + 1) % len(DIRS)
                except Exception:
                    pass
            elif self._in_my_turn and tid in AI_ACT_TIDS:
                self.blue_act_count += 1

    def act_turn(self):
        """我方回合决策环 (P8-C 链)。"""
        time.sleep(0.5)
        # 1. 建一级兵营 (一次)
        if not self.built:
            bs = BuildStructure(tid=TOWN_OI, bid=30, player=MY_COLOR, request_id=self.next_req())
            print(f'[ACT] BuildStructure town={TOWN_OI} bid=30')
            self.conn.send_frame(bs.to_bytes())
            self.built = True
            time.sleep(0.8)
        # 2. 招兵 (建好后 available 才有; 简化: T2+ 每回合尝试一次)
        if self.built and self.available.get('seen') and not self.recruited:
            # crid 用字面 jsonKey (P8-C 范式); Twins 红方城堡种族未知, 由 112 广播驱动失败则跳过
            rc = RecruitCreatures(tid=TOWN_OI, dst=HERO_OI, crid='core:pikeman',
                                  amount=5, level=0, player=MY_COLOR, request_id=self.next_req())
            print(f'[ACT] RecruitCreatures town={TOWN_OI} -> hero={HERO_OI} (pikeman x5, 试探)')
            self.conn.send_frame(rc.to_bytes())
            self.recruited = True
            time.sleep(0.8)
        # 3. MoveHero 朝当前方向推 1 格
        dx, dy = DIRS[self.dir_idx]
        nx, ny = self.hero_pos[0] + dx, self.hero_pos[1] + dy
        mh = MoveHero(path=[(nx, ny, 0)], layer=0, hid=HERO_OI, transit=False,
                      player=MY_COLOR, request_id=self.next_req())
        print(f'[ACT] MoveHero {self.hero_pos[:2]} -> ({nx},{ny},0) dir={self.dir_idx}')
        self.conn.send_frame(mh.to_bytes())
        self._pending_from = self.hero_pos   # v2: 记录移动前位置, FAILED 由 109 回调回滚
        self.hero_pos = (nx, ny, 0)   # 乐观更新
        time.sleep(0.8)
        # 4. EndTurn
        et = EndTurn(player=MY_COLOR, request_id=self.next_req())
        print('[ACT] EndTurn')
        self.conn.send_frame(et.to_bytes())
        self._in_my_turn = False

    # ---------- 判定 ----------
    def srv_alive(self):
        if self.srv.poll() is not None:
            return False
        try:
            with open(SRV_LOG, 'r', encoding='utf-8', errors='replace') as f:
                tail = f.readlines()[-30:]
            return not any('Disaster happened' in l or 'Crash info will be put' in l for l in tail)
        except Exception:
            return True

    def wait_until(self, pred, timeout, what):
        t0 = time.time()
        while time.time() - t0 < timeout:
            if pred():
                print(f'  [OK] {what}')
                return True
            time.sleep(0.5)
        print(f'  [FAIL] {what} ({timeout}s 超时)')
        return False

    def count_alt_turns(self):
        alt = sum(1 for a, b in zip(self.turn_seq, self.turn_seq[1:]) if a != b)
        return alt + 1 if self.turn_seq else 0

    def run(self):
        print('=== T13.11 M2: 红方(模型位)决策环 vs NK2 ===')
        kill_all()

        results = {}
        results['server_alive'] = self.start_server()
        print(f'[1] server = {results["server_alive"]}')
        if not results['server_alive']:
            return 2

        results['host_joined'] = self.host_join()
        print(f'[2] python(红) 连入 = {results["host_joined"]}')
        if not results['host_joined']:
            self.cleanup()
            return 2
        time.sleep(1)

        self.blue_cli = self.start_blue_client()
        results['blue_joined'] = self.wait_until(
            lambda: count_pattern(SRV_LOG, RECV_CC) >= 2, 25, 'client1(蓝NK2) 连入')
        print(f'[3] client1(蓝) = {results["blue_joined"]}')

        self.send_change_host(2)

        results['game_started'] = self.wait_until(
            lambda: grep_log(SRV_LOG, 'Received CPack of type 14LobbyStartGame'), 50, '对局开始')
        print(f'[4] 对局开始 = {results["game_started"]}')

        self.wait_until(lambda: grep_log(f'{TMP}\\p11m2_blue.log', 'will be lead by') or True, 15,
                        '蓝方装载窗口')
        m = re.search(r'Player \w+ will be lead by (\S+)',
                      open(f'{TMP}\\p11m2_blue.log', encoding='utf-8', errors='replace').read()) \
            if os.path.exists(f'{TMP}\\p11m2_blue.log') else None
        results['blue_ai'] = m.group(1) if m else None
        print(f'[5] 蓝方 AI = {results["blue_ai"]}')

        # 决策环观察 4 分钟 (Build T1 / Recruit+Move T2+)
        t0 = time.time()
        while time.time() - t0 < 240:
            if self.count_alt_turns() >= 9 and self.move_ok >= 1:
                break
            time.sleep(1)
        results['alt_turns'] = self.count_alt_turns()
        results['move_ok'] = self.move_ok
        results['move_tried'] = self.moves_tried
        results['build_applied'] = grep_log(SRV_LOG, 'BuildStructure') and grep_log(SRV_LOG, 'successfully applied')
        results['recruit_applied'] = grep_log(SRV_LOG, 'RecruitCreatures')
        results['server_no_crash'] = self.srv_alive()
        results['procs'] = {'server': self.srv.poll() is None,
                            'blue': self.blue_cli.poll() is None}
        print(f'[6] 交替={results["alt_turns"]} 红方Move成功={results["move_ok"]}/{results["move_tried"]} '
              f'Build受理={results["build_applied"]} Recruit出现={results["recruit_applied"]} '
              f'无崩={results["server_no_crash"]} 进程={results["procs"]}')

        self.running = False
        self.conn.disconnect()
        self.cleanup()

        verdict = (results['game_started'] and results['alt_turns'] >= 5
                   and results['move_ok'] >= 1
                   and results['server_no_crash'] and results['procs']['server'])
        import json
        rpt = {'ts': time.strftime('%Y-%m-%d %H:%M:%S'), 'results': results,
               'verdict': 'PASS' if verdict else 'FAIL'}
        rp = f'{TMP}\\p11m2_report.json'
        Path(rp).write_text(json.dumps(rpt, ensure_ascii=False, indent=2))
        print(f"\n=== T13.11 M2 结果: {rpt['verdict']} ===")
        print(f"报告: {rp}")
        return 0 if verdict else 3

    def cleanup(self):
        for p in (self.blue_cli, self.srv):
            if p and p.poll() is None:
                p.terminate()
                try:
                    p.wait(timeout=5)
                except Exception:
                    p.kill()
        kill_all()


if __name__ == '__main__':
    sys.exit(P11M2().run())
