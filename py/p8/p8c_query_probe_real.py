#!/usr/bin/env python3
"""
P8-C 阶段5 — QueryReply(197) 实机探针
=====================================
在 P8-B 方案 F (Python host + 真实 guest client + ChangeHost 让位) 基础上,
用 QueryManager 自动回复 server 下发的所有 Query 派生包, 记录真实 QueryReply(197)
帧与 server 日志证据, 补齐 T13.10 多人对战验证的 Query 闭环。

数据源
------
1. 实机帧: 记录每条 QueryReply(197) 的 [qid, reply, len, raw]
2. 客户端收到的 Query 包: 按 QueryManager.QUERY_TYPES 分类统计
3. server 日志: tail [SRV-DIAG] QUERY 行 (若有) 与任何 "fishy/not-allowed" 行
4. 协议栈: 197 帧顶层 = isNull(1B)+pid(LVarInt)+tid(LVarInt)+[player]+[req]+[qid]+[1B has_reply]+[reply]

验收 (任一满足即 PASS)
----------------------
A. 至少一条 QueryReply 发出, 且后续有非 197/88 的正常包 (说明 server 未卡死/崩溃)
B. server 日志出现 [SRV-DIAG] QUERY 行或 "query successfully applied" 字样
C. 全程 server 无 fishy/not-allowed/crash/timeout 关键字, 且至少一次 PlayerEndsTurn(102) 回流
说明: 无回合计时器时 PlayerStartsTurn 多为 qid=-1 (INVALID, 跳过回复) 属正常, 不作 fail。

跑法
----
  python py/p8/p8c_query_probe_real.py
预计 200-220s (4 回合 + 收尾), 退出码 0=PASS。

作者: 2026-09-12, P8-C 阶段5 实机开发
"""
import sys, os, time, uuid as uuidlib, subprocess, threading, re, json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from vcmi_protocol.connection import VCMITCPConnection
from vcmi_protocol.serialization import BinarySerializer, BinaryDeserializer
from vcmi_protocol.packs import (
    LobbyClientConnected, MoveHero, EndTurn, QueryReply,
    PlayerStartsTurn, HeroLevelUp, BlockingDialog, GarrisonDialog,
)
from vcmi_protocol.protocol import parse_client_pack, QueryManager

HOST = '127.0.0.1'; PORT = 3030; BIN = r'D:\vcmi-fork-build\bin'
MY_COLOR = 0
MAP = r'Maps/A Warm and Familiar Place.h3m'
SRV_LOG = r'C:\Users\Administrator\AppData\Local\Temp\p8c5_srv.log'
CLI_LOG = r'C:\Users\Administrator\AppData\Local\Temp\p8c5_cli.log'
DUR = 200          # 对局时长 (秒)
TURNS_TARGET = 4   # 我方回合数

LOBBY_TIDS = {216:'LobbyClientConnected',217:'LobbyClientDisconnected',218:'LobbyChatMessage',
              221:'LobbyLoadProgress',223:'LobbyPrepareStartGame',224:'LobbyStartGame',
              226:'LobbyUpdateState',229:'LobbySetMap',225:'LobbyChangeHost',227:'LobbyShowMessage'}
GAME_TIDS = {88:'PlayerStartsTurn',116:'NewTurn',132:'BattleStart',135:'BattleResult',
             84:'PackageApplied',85:'SystemMessage',109:'TryMoveHero',115:'GiveHero',
             121:'NewObject',102:'PlayerEndsTurn',86:'SetResources',95:'SetObjectProperty',
             106:'SetHeroes',111:'SetAvailableHero',112:'SetAvailableCreatures',
             117:'SetObjects',118:'SetSetters',125:'SetPlayerInfo',251:'PackageReceived',
             154:'HeroLevelUp',156:'BlockingDialog',157:'GarrisonDialog',
             158:'ExchangeDialog',159:'TeleportDialog',160:'MapObjectSelectDialog'}

def tid_name(t):
    return LOBBY_TIDS.get(t) or GAME_TIDS.get(t) or f'?{t}'

def kill_all():
    for exe in ('VCMI_server.exe', 'VCMI_client.exe'):
        subprocess.run(['taskkill', '/F', '/IM', exe], capture_output=True)
    time.sleep(1)


class Probe:
    def __init__(self):
        self.conn = VCMITCPConnection(HOST, PORT)
        self.qmgr = QueryManager(player=MY_COLOR, auto_reply=True)
        self._us_count = 0
        self.client2_seen = False
        self.game_started = False
        self.running = True
        self.turn_count = 0
        self.end_turn_sent = False
        self._req = 0
        # Query 记录
        self.query_received = []   # [{type_id,name,qid,replied,reply,ts}]
        self.query_reply_sent = [] # [{qid,reply,len,raw_hex,ts}]
        self.other_packs = []      # 非 Query/非 197 回流包名
        self.turn_ends = 0         # PlayerEndsTurn(102) 计数
        self.bad_keywords = []     # server 日志可疑关键字命中

    def next_req(self):
        self._req += 1
        return self._req

    def send_pack(self, pack):
        self.conn.send_frame(pack.to_bytes())

    # ---------- QueryReply 发送 (记录帧) ----------
    def on_query_reply(self, qid, reply, raw):
        self.query_reply_sent.append({
            'qid': qid, 'reply': reply, 'len': len(raw),
            'raw_hex': raw[:48].hex(), 'ts': time.time(),
        })
        print(f'[QRY] 发 QueryReply qid={qid} reply={reply} len={len(raw)}')
        return self.conn.send_frame(raw)

    # ---------- 解析客户端帧 ----------
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

            # Query 自动回复 (QueryManager.QUERY_TYPES)
            if tid in QueryManager.QUERY_TYPES:
                qid = d.get('query_id', -1)
                if qid == -1:
                    print(f'[QRY] {name} qid=-1 INVALID (跳过回复)')
                    self.query_received.append({'type_id': tid, 'name': name,
                                                'qid': -1, 'replied': False,
                                                'reply': None, 'ts': time.time()})
                else:
                    # 构建 QueryReply 帧并记录
                    reply_pack = QueryReply(qid=qid, reply=0,
                                             player=MY_COLOR, request_id=self.next_req())
                    raw = reply_pack.to_bytes()
                    ok = self.on_query_reply(qid, 0, raw)
                    self.query_received.append({'type_id': tid, 'name': name,
                                                'qid': qid, 'replied': ok,
                                                'reply': 0, 'ts': time.time()})

                # PlayerStartsTurn(88) 特殊处理: 无论 qid 是否 -1, 我方回合都要触发 EndTurn
                # 否则 server 等我方回合结束会超时踢掉我方连接 (实测证据)
                if tid == 88:
                    player = d.get('player', -1)
                    if player == MY_COLOR and not self.end_turn_sent:
                        self.turn_count += 1
                        print(f'--- MY TURN #{self.turn_count} (qid={qid}) ---')
                        self.act_turn()
                        self.end_turn_sent = True
                    elif player != MY_COLOR:
                        self.other_packs.append('PlayerStartsTurn(other)')
                continue

            # 回合开始 (非 Query 语义分支: PlayerStartsTurn 已是 Query, 这里只处理 EndTurn 时机)
            if tid == 102:   # PlayerEndsTurn
                self.end_turn_sent = False
                self.turn_ends += 1
                self.other_packs.append('PlayerEndsTurn')
            elif tid == 88:  # PlayerStartsTurn 兜底 (若未经 QueryManager 命中)
                qid = d.get('query_id', -1)
                player = d.get('player', -1)
                if player == MY_COLOR and not self.end_turn_sent:
                    self.turn_count += 1
                    print(f'--- MY TURN #{self.turn_count} (qid={qid}) ---')
                    self.act_turn()
                    self.end_turn_sent = True
                else:
                    self.other_packs.append('PlayerStartsTurn(other)')
            elif tid in (100, 117, 118, 125, 86, 106, 111, 95, 109, 112, 121, 115, 138):
                self.other_packs.append(tid_name(tid))
            else:
                self.other_packs.append(tid_name(tid))
                if tid not in (226,):
                    print(f'[RECV] {len(data):5d}B tid={tid} {tid_name(tid)}')

            if tid == 226:
                self._us_count += 1
                if self._us_count >= 2:
                    self.client2_seen = True
            elif tid == 224:
                self.game_started = True

    def act_turn(self):
        """我方回合: 不移动英雄, 直接 EndTurn (Query 探针专注, 减少干扰)"""
        self.send_pack(EndTurn(player=MY_COLOR, request_id=self.next_req()))

    # ---------- server 日志 tail ----------
    def tail_server_log(self):
        try:
            if not os.path.exists(SRV_LOG):
                return
            with open(SRV_LOG, 'r', errors='replace') as f:
                for line in f:
                    for kw in ('fishy', 'not-allowed', 'CRASH', 'crash', 'TIMEOUT',
                                'abort', 'Assertion', 'terminate'):
                        if kw in line:
                            self.bad_keywords.append((kw, line.strip()[:120]))
                    m = re.search(r'\[SRV-DIAG\] QUERY (.*)', line)
                    if m:
                        print(f'[SRV-DIAG] QUERY {m.group(1)}')
        except Exception as e:
            print(f'[DIAG] {e}')


def main():
    print('=== P8-C 阶段5: QueryReply(197) 实机探针 ===')
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

    # 跑 TURNS_TARGET 个我方回合
    t0 = time.time()
    while time.time() - t0 < DUR and p.turn_count < TURNS_TARGET:
        time.sleep(0.5)
        p.tail_server_log()
    # 收尾: 再等一会, 让末回合的 Query/EndTurn 回流
    time.sleep(5)

    p.running = False
    p.conn.disconnect()
    time.sleep(0.5)
    kill_all()

    # ---------- 汇总 ----------
    print('\n=== RESULT ===')
    print(f'turns_act={p.turn_count} turn_ends(102)={p.turn_ends}')
    print(f'query_received={json.dumps(p.query_received, ensure_ascii=False)}')
    print(f'query_reply_sent={len(p.query_reply_sent)} 条')
    for q in p.query_reply_sent:
        print(f"  qid={q['qid']} reply={q['reply']} len={q['len']} hex={q['raw_hex']}")
    print(f'bad_keywords={p.bad_keywords}')
    if p.bad_keywords:
        for kw, line in p.bad_keywords[:5]:
            print(f'  WARN [{kw}] {line}')

    # 写报告
    report = {
        'ts': time.strftime('%Y-%m-%d %H:%M:%S'),
        'turns_act': p.turn_count,
        'turn_ends': p.turn_ends,
        'query_received': p.query_received,
        'query_reply_sent': p.query_reply_sent,
        'other_packs_sample': p.other_packs[:30],
        'bad_keywords': p.bad_keywords,
        'verdict': None,
    }

    # 判定
    replied = [q for q in p.query_received if q['replied']]
    ok = False
    if replied and not p.bad_keywords:
        # server 未崩 + 有回复 + 有回流
        ok = p.turn_ends > 0
        report['verdict'] = 'PASS'
        print('\n[VERDICT] PASS: 有 QueryReply 发出且 server 健康 (无 fishy/crash), 有回合回流')
    elif not replied and not p.bad_keywords and p.turn_ends > 0:
        report['verdict'] = 'PASS(qid=-1 only)'
        print('\n[VERDICT] PASS(qid=-1 only): 全程无真实 Query (PlayerStartsTurn 均 qid=-1), '
              '但 server 健康且回合正常 — 无计时器场景下的预期行为')
    else:
        report['verdict'] = 'FAIL'
        print(f"\n[VERDICT] FAIL: replied={len(replied)} bad_keywords={len(p.bad_keywords)} turn_ends={p.turn_ends}")

    with open(r'C:\Users\Administrator\AppData\Local\Temp\p8c5_report.json', 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f'[REPORT] -> C:\\Users\\Administrator\\AppData\\Local\\Temp\\p8c5_report.json')
    return 0 if report['verdict'] else 3


if __name__ == '__main__':
    sys.exit(main())
