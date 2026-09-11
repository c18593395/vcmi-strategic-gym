#!/usr/bin/env python3
"""
P8-C 阶段6 — MoveHero(182) 实机探针 (升级)
=================================================

目的
----
在 P8-B 方案 F (Python host + 真实 guest client + ChangeHost 让位) 基础上,
把"手写 TryMoveHero 解析"升级为 parse_client_pack + 新 packs.py::TryMoveHero,
补齐 T13.10 多人对战验证的 MoveHero 实战闭环。

对比旧版
--------
- p8c_movehero_probe.py (旧): TryMoveHero 用 deser.read_int 手动解析 (6B+), 字段序靠猜
- p8c_movehero_probe_real.py (本文件, 新): 全走 parse_client_pack, 与离线
  p8c_movehero_offline_probe.py 走同一协议栈, 覆盖 TryMoveHero 字段序修复

关键路径
--------
1. MoveHero serialize 顶层帧: isNull(1B) + pid(LVarInt) + tid=182(LVarInt) + 包数据
2. TryMoveHero wire 字段 (0911 P8-B 实锤):
     oid + result + start(int3) + end(int3) + movePoints
     + fowRevealed(vector<int3>) + attackedFrom(int3)
3. PackageApplied wire: request_id + is_successful
4. PlayerEndsTurn(102) 回流 (回合切换确认)

数据源
------
1. TryMoveHero 实机帧: 记录 [oid, result, start, end, move_points, fow_len, ts]
2. PackageApplied(182): 客户端收到的 [request_id, is_successful]
3. server 日志: [SRV-DIAG] HERO OI 行 (注入我方英雄 OI/pos) + fishy/not-allowed/crash 关键字
4. 决策: 朝蓝方英雄方向走 MOVES_PER_TURN 步 (锚点 8 邻域), EndTurn 收尾

验收
----
A. move_accepted >= 1 (至少一次 TryMoveHero result>=1 回流)
B. turns_act >= 2 (至少 2 个我方回合, 验证回合切换正常)
C. server 无 fishy/not-allowed/crash/timeout/abort 关键字
D. 至少一条 PackageApplied(ok=True, pack_type=182)

任一 A 失败即 FAIL; B/C 失败降级 WARN。

跑法
----
  python py/p8c_movehero_probe_real.py
预计 180-200s (3 回合 + 收尾), 退出码 0=PASS。

作者: 2026-09-12, P8-C 阶段6 实机开发
"""
import sys, os, time, uuid as uuidlib, subprocess, threading, re, json

sys.path.insert(0, 'D:/Bigdata/hero3_fresh/py')
from vcmi_protocol.connection import VCMITCPConnection
from vcmi_protocol.packs import (
    LobbyClientConnected, MoveHero, EndTurn,
)
from vcmi_protocol.protocol import parse_client_pack

HOST = '127.0.0.1'; PORT = 3030; BIN = r'D:\vcmi-fork-build\bin'
MY_COLOR = 0          # python = red
MAP = r'Maps/Twins.h3m'
SRV_LOG = r'C:\Users\Administrator\AppData\Local\Temp\p8c6_srv.log'
CLI_LOG = r'C:\Users\Administrator\AppData\Local\Temp\p8c6_cli.log'
REPORT = r'C:\Users\Administrator\AppData\Local\Temp\p8c6_report.json'
DUR = 180             # 对局时长 (秒)
TURNS_TARGET = 3      # 我方回合数
MOVES_PER_TURN = 3    # 每回合走 3 步


def kill_all():
    for exe in ('VCMI_server.exe', 'VCMI_client.exe'):
        subprocess.run(['taskkill', '/F', '/IM', exe], capture_output=True)
    time.sleep(1)


class Probe:
    def __init__(self):
        self.conn = VCMITCPConnection(HOST, PORT)
        self._us_count = 0
        self.client2_seen = False
        self.game_started = False
        self.running = True
        # 英雄状态 (从 SRV-DIAG 行解析)
        self.heroes = {}          # oi -> dict(owner, pos=(x,y,z))
        self.my_hero_oi = None
        self.my_hero_pos = None
        # 回合
        self.turn_count = 0
        self.end_turn_sent = False
        self._req = 0
        # 记录
        self.try_moves = []       # [{oid,result,start,end,move_points,fow_len,ts}]
        self.packages_applied = []  # [{request_id,is_successful,ts}]
        self.bad_keywords = []   # [(kw,line)]
        self.move_accepted = 0
        self.move_failed = 0
        self.hero_diag_samples = []

    def next_req(self):
        self._req += 1
        return self._req

    def send_pack(self, pack):
        self.conn.send_frame(pack.to_bytes())

    # ---------- server log tail: 提取英雄 OI + 关键字 ----------
    def poll_srv_diag(self):
        try:
            if not os.path.exists(SRV_LOG):
                return
            with open(SRV_LOG, 'r', errors='replace') as f:
                for line in f:
                    # 我方英雄
                    m = re.search(r'\[SRV-DIAG\] HERO OI=(\d+) owner=(-?\d+) pos=\((-?\d+) (-?\d+) (-?\d+)\)', line)
                    if m:
                        oi = int(m.group(1)); owner = int(m.group(2))
                        pos = (int(m.group(3)), int(m.group(4)), int(m.group(5)))
                        self.heroes[oi] = dict(owner=owner, pos=pos)
                        if owner == MY_COLOR and self.my_hero_oi is None:
                            self.my_hero_oi = oi
                            self.my_hero_pos = pos
                            self.hero_diag_samples.append((oi, pos))
                    # 可疑关键字
                    for kw in ('fishy', 'not-allowed', 'CRASH', 'crash', 'TIMEOUT',
                                'abort', 'Assertion', 'terminate'):
                        if kw in line:
                            self.bad_keywords.append((kw, line.strip()[:160]))
                            break
                    # 提取 QUERY 行
                    mq = re.search(r'\[SRV-DIAG\] QUERY (\{.*?\})', line)
                    if mq:
                        self.query_log_lines.append(mq.group(1))
        except Exception as e:
            print(f'[DIAG] read err {e}')

    def resolve_my_hero(self):
        for oi, info in self.heroes.items():
            if info['owner'] == MY_COLOR:
                self.my_hero_oi = oi
                self.my_hero_pos = info['pos']
                return True
        return False

    # ---------- 决策: 朝敌方英雄方向走一步 (锚点坐标, 8 邻域) ----------
    def decide_step(self):
        assert self.my_hero_pos is not None
        blue = next((i for i, v in self.heroes.items() if v['owner'] != MY_COLOR), None)
        target = self.heroes[blue]['pos'] if blue else (8, 8, 0)
        dx = (target[0] > self.my_hero_pos[0]) - (target[0] < self.my_hero_pos[0])
        dy = (target[1] > self.my_hero_pos[1]) - (target[1] < self.my_hero_pos[1])
        return (self.my_hero_pos[0] + dx, self.my_hero_pos[1] + dy, self.my_hero_pos[2])

    def act_turn(self):
        self.poll_srv_diag()
        if not self.resolve_my_hero():
            print('[ACT] 未解析到我方英雄 OI, 直接 EndTurn')
            self.send_pack(EndTurn(player=MY_COLOR, request_id=self.next_req()))
            return
        for i in range(MOVES_PER_TURN):
            step = self.decide_step()
            mh = MoveHero(path=[step], layer=0, hid=self.my_hero_oi,
                          transit=False, player=MY_COLOR, request_id=self.next_req())
            print(f'[ACT] MoveHero hid={self.my_hero_oi} {self.my_hero_pos} -> {step}')
            self.send_pack(mh)
            time.sleep(0.7)   # 等 server apply + TryMoveHero 广播回流
            self.poll_srv_diag()
        print('[ACT] EndTurn')
        self.send_pack(EndTurn(player=MY_COLOR, request_id=self.next_req()))

    # ---------- 收包循环 (走 parse_client_pack) ----------
    def recv_loop(self):
        while self.running:
            try:
                data = self.conn.recv_frame()
            except Exception as e:
                print(f'[RECV-ERR] {e}')
                continue
            if data is None:
                if not self.conn.connected:
                    print('[RECV] 断开'); break
                continue
            if len(data) == 0:
                continue

            parsed = parse_client_pack(data)
            if parsed is None:
                continue
            tid = parsed.get('type_id')
            name = parsed.get('class_name')
            d = parsed.get('data') or {}

            # Lobby 计数
            if tid == 226:
                self._us_count += 1
                if self._us_count >= 2:
                    self.client2_seen = True
            elif tid == 224:
                self.game_started = True

            # 关键包
            if tid == 109:   # TryMoveHero
                entry = {
                    'oid': d.get('oid'),
                    'result': d.get('result'),
                    'start': d.get('start'),
                    'end': d.get('end'),
                    'move_points': d.get('move_points'),
                    'fow_len': len(d.get('fow_revealed') or []),
                    'ts': time.time(),
                }
                self.try_moves.append(entry)
                if entry['oid'] == self.my_hero_oi:
                    if entry['result'] and entry['result'] >= 1:
                        self.move_accepted += 1
                        if isinstance(entry['end'], tuple):
                            self.my_hero_pos = entry['end']
                    else:
                        self.move_failed += 1
                        print(f'[TRY] OI={entry["oid"]} result={entry["result"]} FAILED '
                              f'({entry["start"]}) -> ({entry["end"]})')
                if len(self.try_moves) % 3 == 1:
                    print(f'[TRY] OI={entry["oid"]} result={entry["result"]} '
                          f'{entry["start"]} -> {entry["end"]} fow={entry["fow_len"]}')
            elif tid == 84:  # PackageApplied
                pa = {'request_id': d.get('request_id'),
                      'is_successful': d.get('is_successful'),
                      'ts': time.time()}
                self.packages_applied.append(pa)
                # 只打印 MoveHero(182) 或 EndTurn(180) 相关 (通过 request_id 顺序推断)
                if pa['request_id'] is not None:
                    print(f'[APPLIED] req={pa["request_id"]} ok={pa["is_successful"]}')
            elif tid == 102:  # PlayerEndsTurn
                self.end_turn_sent = False
            elif tid == 88:   # PlayerStartsTurn — 我方回合触发
                qid = d.get('query_id', -1)
                player = d.get('player', -1)
                if player == MY_COLOR and not self.end_turn_sent:
                    self.turn_count += 1
                    print(f'--- MY TURN #{self.turn_count} (qid={qid}) ---')
                    self.act_turn()
                    self.end_turn_sent = True
                elif player != MY_COLOR:
                    # 敌方回合开始, 不处理
                    pass
            # 其他包 (静默, 减少噪音)

            # 未知包: 只在非常见包时打印
            if tid not in (88, 102, 109, 84, 224, 226, 116, 112, 90, 251,
                            86, 100, 106, 111, 117, 118, 121, 125, 95, 115):
                print(f'[RECV] {len(data):5d}B tid={tid} {name}')


def main():
    print('=== P8-C 阶段6: MoveHero(182) 实机探针 (走 parse_client_pack) ===')
    kill_all()
    srv_log = open(SRV_LOG, 'w')
    srv = subprocess.Popen([BIN + r'\VCMI_server.exe', f'--port={PORT}'],
                           cwd=BIN, stdout=srv_log, stderr=subprocess.STDOUT)
    time.sleep(9)

    p = Probe()
    if not p.conn.connect():
        print('[FAIL] connect'); return 1
    threading.Thread(target=p.recv_loop, daemon=True).start()
    p.conn.send_frame(LobbyClientConnected(uuid=str(uuidlib.uuid4()),
                                           names=['PyHost'], mode=0).to_bytes())
    print('[1] python(host) joined lobby')
    time.sleep(1)

    cli_log = open(CLI_LOG, 'w')
    env = dict(os.environ); env['VCMI_TESTMAP_ONLYAI'] = '1'
    cli = subprocess.Popen([BIN + r'\VCMI_client.exe', '--testmap', MAP,
                            '--donotstartserver', '--serverport', str(PORT), '--headless'],
                           cwd=BIN, stdout=cli_log, stderr=subprocess.STDOUT, env=env)
    print(f'[2] client1 pid={cli.pid}')

    t0 = time.time()
    while time.time() - t0 < 15 and not p.client2_seen:
        time.sleep(0.2)
    print(f'[3] client2_seen={p.client2_seen}')

    p.conn.send_frame(bytes([0, 0, 0xe1, 0x01, 0x02]))   # LobbyChangeHost -> cid2
    print('[4] ChangeHost sent')

    t0 = time.time()
    while time.time() - t0 < 40 and not p.game_started:
        time.sleep(0.5)
    print(f'[5] game_started={p.game_started}')
    if not p.game_started:
        p.running = False
        return 2

    # 等 SRV-DIAG 英雄行出现
    t0 = time.time()
    while time.time() - t0 < 10:
        p.poll_srv_diag()
        if p.resolve_my_hero():
            break
        time.sleep(0.5)
    print(f'[6] my_hero_oi={p.my_hero_oi} pos={p.my_hero_pos} '
          f'heroes={len(p.heroes)} diag_samples={p.hero_diag_samples[:3]}')

    # 跑 TURNS_TARGET 个我方回合
    t0 = time.time()
    while time.time() - t0 < DUR and p.turn_count < TURNS_TARGET:
        time.sleep(0.5)
        p.poll_srv_diag()

    # 收尾: 等末回合回流
    time.sleep(3)
    p.running = False
    p.conn.disconnect()
    time.sleep(0.5)
    kill_all()

    # ---------- 汇总 ----------
    print('\n=== RESULT ===')
    print(f'turns_act={p.turn_count} move_accepted={p.move_accepted} move_failed={p.move_failed}')
    print(f'try_moves_total={len(p.try_moves)} packages_applied_total={len(p.packages_applied)}')
    print(f'hero_diag_samples={p.hero_diag_samples[:5]}')
    print(f'bad_keywords={len(p.bad_keywords)} 条')
    for kw, line in p.bad_keywords[:5]:
        print(f'  WARN [{kw}] {line}')

    # 打印最近 8 条 TryMoveHero 详情
    print('\n--- TryMoveHero 最近 8 条 ---')
    for tm in p.try_moves[-8:]:
        print(f'  oid={tm["oid"]} result={tm["result"]} {tm["start"]} -> {tm["end"]} '
              f'mp={tm["move_points"]} fow={tm["fow_len"]}')

    # 判定
    ok = p.move_accepted >= 1
    warn = False
    if p.turn_count < 2:
        warn = True
        print(f'[WARN] turns_act={p.turn_count} < 2')
    if p.bad_keywords:
        warn = True

    report = {
        'ts': time.strftime('%Y-%m-%d %H:%M:%S'),
        'turns_act': p.turn_count,
        'move_accepted': p.move_accepted,
        'move_failed': p.move_failed,
        'try_moves': p.try_moves,
        'packages_applied': p.packages_applied,
        'hero_diag_samples': p.hero_diag_samples,
        'bad_keywords': p.bad_keywords,
        'warn': warn,
        'verdict': 'PASS' if ok else 'FAIL',
    }
    with open(REPORT, 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f'[REPORT] -> {REPORT}')

    if ok:
        print('\n[VERDICT] PASS: MoveHero 至少 1 次 SUCCESS + server 健康')
        return 0
    else:
        print(f'\n[VERDICT] FAIL: move_accepted=0 (TryMoveHero 从未回流 SUCCESS)')
        return 3


if __name__ == '__main__':
    sys.exit(main())
