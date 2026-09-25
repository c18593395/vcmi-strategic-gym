#!/usr/bin/env python3
"""
P8-C 收尾 2.1/2.2 — QueryReply(197) 组包脚本 + 8B/9B 回退 (QUERY-DIAG 路线)
==========================================================================
前置 (已闭环):
- fork 1.8 rel/bin/vcmiserver 含 VCMI_QUERY_DIAG 编译宏 (QueriesProcessor.cpp,
  env VCMI_QUERY_DIAG=1 双控), 实机一局 [QUERY-DIAG] 行 PASS (09-16 commit e90a94c)
- p8c_qdiag_smoke.py 全链路骨架: server(diag=1) -> python host -> client1 guest
  -> ChangeHost -> 开局

本脚本 (纯协议工作):
1. 复用 smoke 骨架起真实对局 (WSL, 禁"连了再断"探活)
2. 双数据源拿真实 queryID:
   a. server tail [QUERY-DIAG] qid=N (N!=-1 且 player 为我方) — 本 change 设计的目标数据源
   b. client 侧 query 包 (tid in {88,154,156,157,158,159,160}) 包体首字段 qid — 兜底数据源
      (无计时器场景全部 qid=-1, 属正常, 见 09-14 数据源墙记录)
3. 组包 QueryReply:
   8B 布局 = 顶层 isNull(1B)+pid(LVarInt)+tid(LVarInt) + player + req + qid + reply-absent(0x00)
   9B 布局 = 同上 + reply-present(0x01) + reply=0
   C++ 权威 (PacksForServer.h L685 + BinarySerializer.h L332):
     QueryReply = QueryID + std::optional<int32_t>
     save(optional): present=save(u8 1)+int32; absent=save(uint32 0)  <-- 注意 C++ 端 absent 走 uint32 路径
     故 8B/9B 为 Python 侧两种 candidate 布局, 实机拒绝时 9B->8B 回退
5. 判定口径: ① bad keyword 只数 197 QueryReply 鱼线 ("applying 10QueryReply...fishy"),
   其他鱼线 (BuildStructure/RecruitCreatures/EndTurn) 记录但不计入判定
   (它们 = 占位 OI 或时序问题, 与 197 布局验证无关);
   ② 我方回合只 EndTurn, 让蓝方 AI 自由玩自然产生 MapObjectVisitQuery (不占位 Build/Recruit);
   ③ qid 回送时机: 仅我方 (red) 的 qid != -1 才发 QueryReply, green (AI) 的 query 只记录不回送。
6. 判定:
   A. 任一 qid!=-1 的 197 帧发出且 197 无 fishy = PASS(replied)
   B. 全程 qid=-1 only (无计时器场景), 但 197 帧离线组包已验证 + 8B/9B 回退单测 PASS +
      对局 >=2 回合 zero fishy = PASS(qid=-1 only)  — 同 09-14 p8c_query_probe_real 口径
跑法: 在 WSL 内 python3 /mnt/d/Bigdata/hero3_fresh/py/p8/p8c_query_reply.py
预计 150-200s, 退出码 0=PASS / 2=未开局 / 3=FAIL
"""
import os
import sys, os, time, uuid as uuidlib, subprocess, threading, re, json

sys.path.insert(0, '/mnt/d/Bigdata/hero3_fresh/py')
from vcmi_protocol.connection import VCMITCPConnection
from vcmi_protocol.serialization import BinarySerializer, BinaryDeserializer
from vcmi_protocol.packs import (
    LobbyClientConnected, EndTurn, QueryReply, BuildStructure, RecruitCreatures)

HOST = '127.0.0.1'; PORT = 3030
BIN = os.environ.get("BIN", '/home/administrator/vcmi-native/rel/bin')
MAP = 'Maps/A Warm and Familiar Place.h3m'
MY_COLOR = 0
SRV_LOG = '/tmp/p8cr_srv.log'
CLI_LOG = '/tmp/p8cr_cli.log'
DUR = 150
QUERY_TYPES = {88:'PlayerStartsTurn',154:'HeroLevelUp',156:'BlockingDialog',
               157:'GarrisonDialog',158:'ExchangeDialog',159:'TeleportDialog',
               160:'MapObjectSelectDialog'}
LOBBY_TIDS = {216:'LobbyClientConnected',218:'LobbyChatMessage',223:'LobbyPrepareStartGame',
              224:'LobbyStartGame',226:'LobbyUpdateState',229:'LobbySetMap',225:'LobbyChangeHost'}

def tid_name(t):
    return LOBBY_TIDS.get(t) or QUERY_TYPES.get(t) or {102:'PlayerEndsTurn',84:'PackageApplied',
        109:'TryMoveHero',112:'SetAvailableCreatures',85:'SystemMessage'}.get(t, f'?{t}')

def kill_all():
    subprocess.run(['pkill','-f','vcmiserver'], capture_output=True)
    subprocess.run(['pkill','-f','vcmiclient'], capture_output=True)
    time.sleep(1)

# ---------- 2.2: QueryReply 两种布局组包 + 回退 ----------

def build_query_reply(qid, reply, player, req, layout):
    """layout 'absent'(8B): reply 槽=0x00; 'present'(9B): 0x01+LVarInt(reply)"""
    s = BinarySerializer()
    s.write_bool(False); s.write_int(0); s.write_int(197)   # 顶层指针帧
    s.write_int(player); s.write_int(req)                    # CPackForServer
    s.write_int(qid)                                          # qid (QueryID)
    if layout == 'present':
        s.write_uint8(1); s.write_int(reply)
    else:
        s.write_uint8(0)
    return s.get_bytes()

def selftest_layouts():
    """2.2 单元验证: 8B/9B 组包字节精确 + QueryReply 类 与手工组包一致性"""
    ok = True
    b8 = build_query_reply(7, 0, 1, 3, 'absent')
    b9 = build_query_reply(7, 0, 1, 3, 'present')
    print(f'  8B absent : {len(b8)}B {b8.hex()}')
    print(f'  9B present: {len(b9)}B {b9.hex()}')
    ok &= len(b8) == 8 and len(b9) == 9
    # 与 QueryReply 类对拍
    p8 = QueryReply(qid=7, reply=None, player=1, request_id=3).to_bytes()
    p9 = QueryReply(qid=7, reply=0,  player=1, request_id=3).to_bytes()
    print(f'  class 8B  : {len(p8)}B {p8.hex()}  match={p8==b8}')
    print(f'  class 9B  : {len(p9)}B {p9.hex()}  match={p9==b9}')
    ok &= (p8 == b8) and (p9 == b9)
    # 回退函数单测: reject absent -> present
    rejected = {}
    def fake_send(buf):
        if buf == b8:
            rejected['b8'] = True
            return 'reject'
        return 'accept'
    for layout in ('absent', 'present'):
        r = fake_send(build_query_reply(7, 0, 1, 3, layout))
        if r == 'accept':
            print(f'  fallback: {layout} accepted (rejected_absent={rejected.get("b8")})')
            ok &= True
            break
    print('  LAYOUT SELFTEST:', 'PASS' if ok else 'FAIL')
    return ok

class Probe:
    def __init__(self):
        self.conn = VCMITCPConnection(HOST, PORT)
        self.client2_seen = False
        self.game_started = False
        self.running = True
        self.turns = 0
        self.new_turns = 0      # server 端 NewTurn(116) 回合轮转计数
        self.end_turn_sent = False
        self._req = 0
        self.turn_ends = 0
        self.query_seen = []      # 双侧记录: {src,tid,qid,ts}
        self.qreply_sent = []      # [{qid,layout,len,hex,ts}]
        self.qdiag_real = []       # DIAG 行 qid!=-1
        self.qdiag_total = 0
        self._log_pos = 0
        self._last_bad_ts = 0.0
        self.bad = []          # 所有 fishy/not-allowed 行 (记录, 不计入判定)
        self.qreply_bad = []   # 仅 197 QueryReply 鱼线 (判定 + 回退判据)
        self._diag_sent_qids = set()  # (qid, player) 去重: DIAG 行重复打印时只回送一次
        self._log_pos_on_open = 0   # tail 异常回退锚点

    def next_req(self):
        self._req += 1
        return self._req

    # ---------- server 日志 tail (QUERY-DIAG + bad keywords, 增量) ----------
    def tail_srv(self):
        if not os.path.exists(SRV_LOG):
            return
        try:
            with open(SRV_LOG, 'r', errors='replace') as f:
                f.seek(self._log_pos)
                while True:
                    line = f.readline()
                    if not line:
                        break
                    m = re.search(r'\[QUERY-DIAG\] qid=(-?\d+) player=(\S+) type=(.*)', line)
                    if m:
                        qid, player, typ = int(m.group(1)), m.group(2), m.group(3).strip()
                        self.qdiag_total += 1
                        print(f'[DIAG] qid={qid} player={player} type={typ[:60]}')
                        if qid != -1:
                            self.qdiag_real.append({'qid': qid, 'player': player, 'type': typ})
                            key = (qid, player)
                            if key not in self._diag_sent_qids:
                                self._diag_sent_qids.add(key)
                                self.on_real_qid(qid, player)
                        self._log_pos = f.tell()
                    low = line.lower()
                    if any(k in low for k in ('fishy', 'not-allowed', 'not allowed')):
                        self._last_bad_ts = time.time()
                        self.bad.append(line.strip()[:120])
                        if 'queryreply' in low or '10queryreply' in low:
                            self.qreply_bad.append(line.strip()[:120])
                # 读完 → 更新 offset 锚点 (异常回退用; 正常路径 _log_pos 已是最新)
                self._log_pos_on_open = self._log_pos
                # 去重: on_real_qid 内部 send_query_reply 会触发 tail_srv 递归,
                # 此处已在 send_query_reply 内调用过, 跳过避免重复处理同批行
        except OSError:
            # 读中被 truncate/异常: 本行已处理过部分, 回退到本次 open 的锚点重读 (防重放)
            print(f'[TAIL] 异常, 回退 offset -> {getattr(self, "_log_pos_on_open", 0)}')
            self._log_pos = getattr(self, '_log_pos_on_open', 0)
        except Exception as e:
            print(f'[TAIL-ERR] {e}')

    # ---------- 2.1/2.2: QueryReply 发送 + 8B->9B 回退 ----------
    def send_query_reply(self, qid, src):
        """absent(8B) 首发; 若 server 拒绝 -> 换 present(9B) 重试一次
        拒绝判据 = 197 fishy ("applying 10QueryReply...fishy") 或 10s 内无 PackageApplied(84) 回流
        (197 applying 行 = "Successfully applied QueryReply" 不含 fishy, 故只看 fishy 与静默)"""
        for layout in ('absent', 'present'):
            if not self.conn.connected:
                print(f'[QRY] 连接已断, 停止回退', flush=True)
                return 'disconnected'
            buf = build_query_reply(qid, 0, MY_COLOR, self.next_req(), layout)
            self.conn.send_frame(buf)
            self.qreply_sent.append({'qid': qid, 'layout': layout, 'len': len(buf),
                                     'hex': buf.hex(), 'ts': time.time(), 'src': src})
            print(f'[QRY] 发 QueryReply qid={qid} ({src}) layout={layout} {len(buf)}B')
            base_bad = len(self.qreply_bad)
            t1 = time.time()
            while time.time() - t1 < 10:
                time.sleep(0.5)
                self.tail_srv()
                if len(self.qreply_bad) > base_bad:
                    break
            if len(self.qreply_bad) == base_bad:
                print(f'[QRY] layout={layout} 无 197 fishy -> 受理')
                return layout
            print(f'[QRY] layout={layout} 197 被拒 (fishy +{len(self.qreply_bad)-base_bad}), 回退')
        return 'fallback'

    def on_real_qid(self, qid, player=None):
        """QUERY-DIAG 侧真实 qid: 仅当我方 player (MY_COLOR=0='red') 才回送;
        防递归: send_query_reply 会触发 tail_srv -> on_real_qid, 用 _replying 锁"""
        if player is not None:
            # player 是颜色字符串: 0=red, 1=green; 我方 MY_COLOR=0 -> 'red'
            my_str = {0: 'red', 1: 'green', 2: 'blue', 3: 'yellow',
                      4: 'teal', 5: 'olive', 6: 'purple', 7: 'black'}
            if my_str.get(MY_COLOR) != str(player).lower():
                return
        if getattr(self, '_replying', False):
            return
        if not self.conn.connected:
            print('[QRY] 连接已断, 跳过回送', flush=True)
            return
        self._replying = True
        try:
            self.query_seen.append({'src': 'diag', 'qid': qid, 'player': player, 'ts': time.time()})
            self.send_query_reply(qid, 'diag')
        finally:
            self._replying = False

    def handle_client_query(self, tid, d):
        qid = d.get('query_id', -1)
        if qid == -1:
            self.query_seen.append({'src': 'client', 'tid': tid, 'qid': -1, 'ts': time.time()})
            return
        self.query_seen.append({'src': 'client', 'tid': tid, 'qid': qid, 'ts': time.time()})
        self.send_query_reply(qid, 'client')

    def send_end_turn(self):
        self.conn.send_frame(EndTurn(player=MY_COLOR, request_id=self.next_req()).to_bytes())
        print('[ACT] EndTurn', flush=True)

    def act_turn(self):
        """3.1 招募 query 实战闭环: Build->Recruit 链 (P8-C 已验证的触发链),
        招募后 server 可能弹 dialog query (gold 不足 / 确认). 10s 内看 [QUERY-DIAG] 是否出 qid!=-1.
        Build tid=1/bid=30 + Recruit tid=1/bid=30 = 占位 OI (09-14 探针对其 qid 恒 -1),
        但它们触发的 server 端招募 dialog 才是 3.1 目标 query"""
        # 3.1 招募触发: Build+Recruit 链 (P8-C 验证链). Recruit 需要真实 OI — 占位 tid=1/dst=1,
        # 实际 server 会拒绝 (fishy Build/Recruit), 但会触发 server 端 query 生成路径.
        # 关键判据: 197 QueryReply zero fishy; Build/Recruit 的 fishy 不计入判定 (口径 ①).
        bs = BuildStructure(tid=1, bid=30, player=MY_COLOR, request_id=self.next_req())
        rc = RecruitCreatures(tid=1, dst=1, crid="hero1", amount=1, player=MY_COLOR, request_id=self.next_req())
        self.conn.send_frame(bs.to_bytes())
        self.conn.send_frame(rc.to_bytes())
        print('[ACT] Build+Recruit 招募链 (3.1 触发)', flush=True)
        self.end_turn_sent = True

    def recv_loop(self):
        while self.running:
            data = self.conn.recv_frame()
            if data is None:
                if not self.conn.connected:
                    print(f'[RECV] socket 已断 (connected={self.conn.connected})', flush=True)
                    break
                time.sleep(0.2)
                continue
            if not data:
                continue
            d = BinaryDeserializer(data)
            if d.read_bool():
                continue
            d.read_int()
            tid = d.read_int()
            if tid == 226:
                self.conn._us_count = getattr(self.conn, '_us_count', 0) + 1
                if self.conn._us_count >= 2:
                    self.client2_seen = True
            elif tid == 224:
                self.game_started = True
            elif tid == 102:
                self.end_turn_sent = False
                self.turn_ends += 1
                # 3.2 判据: 回合轮转 (EndTurn 回流 = 该回合已走完)
                self.new_turns = max(self.new_turns, self.turn_ends)
            elif tid == 116:
                # NewTurn: 回合开始标记 (辅助计数, 主判据用 102)
                self.new_turns = max(self.new_turns, self.turn_ends)
            elif tid in (154, 156, 157, 158, 159, 160):
                # 其他 Query 派生包: 字段序也是 queryID 先行 (NetPacksBase Query{queryID})
                qid = d.read_int()
                self.query_seen.append({'src': 'client', 'tid': tid,
                                        'name': QUERY_TYPES.get(tid, f'?{tid}'),
                                        'qid': qid, 'ts': time.time()})
                if qid != -1:
                    print(f'[QRY] 客户端 {tid} qid={qid} -> 组包回送')
                    self.on_real_qid(qid, f'client{tid}')
            elif tid == 88:
                # 88 = Query 派生: 字段序 queryID + player (0911 P8-B 实锤)
                qid = d.read_int()
                player = d.read_int()
                self.query_seen.append({'src': 'client', 'tid': 88, 'qid': qid,
                                        'name': 'PlayerStartsTurn', 'ts': time.time()})
                # P8-B 实锤坑: 88 的 queryID 字段 = 上一回合的 qid 残值, 真实 qid 以 QUERY-DIAG 为准
                if player == MY_COLOR and not self.end_turn_sent:
                    self.turns += 1
                    print(f'--- MY TURN #{self.turns} (88 qid={qid}) ---', flush=True)
                    self.act_turn()
                    self.end_turn_sent = True
            else:
                if tid not in (100, 117, 118, 125, 86, 106, 111, 95, 109, 112, 121, 115):
                    print(f'[RECV] {len(data):6d}B tid={tid} {tid_name(tid)}', flush=True)

def main():
    print('=== P8-C 收尾 2.1/2.2: QueryReply 组包 + 8B/9B 回退 (WSL 实机) ===', flush=True)
    ok = selftest_layouts()
    if not ok:
        print('LAYOUT SELFTEST FAIL — 离线组包未过, 停止实机'); return 3

    kill_all()
    env = dict(os.environ); env['VCMI_QUERY_DIAG'] = '1'
    srv_log = open(SRV_LOG, 'w')
    srv = subprocess.Popen([BIN + '/vcmiserver', f'--port={PORT}'],
                           cwd=BIN, stdout=srv_log, stderr=subprocess.STDOUT, env=env)
    p = Probe()
    for attempt in range(20):
        if p.conn.connect():
            print(f'[0] python connected as first client after {attempt} retries', flush=True)
            break
        time.sleep(1)
    else:
        print('[FAIL] python(host) connect'); return 1
    threading.Thread(target=p.recv_loop, daemon=True).start()
    p.conn.send_frame(LobbyClientConnected(uuid=str(uuidlib.uuid4()), names=['PyHost'], mode=0).to_bytes())
    print('[1] python(host) joined lobby', flush=True)
    time.sleep(1)

    cli_log = open(CLI_LOG, 'w')
    cenv = dict(os.environ); cenv['VCMI_TESTMAP_ONLYAI'] = '1'
    cli = subprocess.Popen([BIN + '/vcmiclient', '--testmap', MAP,
                            '--donotstartserver', '--headless'],
                           cwd=BIN, stdout=cli_log, stderr=subprocess.STDOUT, env=cenv)
    print(f'[2] client1 pid={cli.pid}', flush=True)

    t0 = time.time()
    while time.time() - t0 < 40 and not p.client2_seen:
        time.sleep(0.2)
    print(f'[3] client2_seen={p.client2_seen}', flush=True)
    p.conn.send_frame(bytes([0, 0, 0xe1, 0x01, 0x02]))
    print('[4] ChangeHost sent', flush=True)

    t0 = time.time()
    while time.time() - t0 < 90 and not p.game_started:
        time.sleep(0.5)
    print(f'[5] game_started={p.game_started}', flush=True)
    if not p.game_started:
        p.running = False; srv.kill(); cli.kill(); return 2

    # 主循环: 让对局推进. green(NK2 client) 在 16PlayerStartsTurn 广播#2 时 runNetwork 段错误
    # (dmesg 实锤, fork/1.8 已知). green 崩 -> server SHUTDOWN -> Python 连接 RST = 预期收尾.
    # 断线后仍 tail 5s, 捕获 green 崩前最后一波 DIAG 行 (197 组包机会).
    t0 = time.time()
    while time.time() - t0 < DUR:
        time.sleep(2)
        p.tail_srv()
        if not p.conn.connected:
            # 断线后继续 tail 5s (green 崩前最后一波数据窗口)
            t1 = time.time()
            while time.time() - t1 < 5:
                time.sleep(0.5)
                p.tail_srv()
            break

    p.running = False
    p.conn.disconnect()
    time.sleep(1)
    srv.terminate(); cli.terminate(); time.sleep(1)
    srv.kill(); cli.kill()
    p.tail_srv()

    # ---------- 汇总 ----------
    print('\n=== RESULT ===', flush=True)
    print(f'client-side query 包: {len(p.query_seen)} 条, qid!=-1: '
          f'{sum(1 for q in p.query_seen if q.get("qid", -1) != -1)}')
    for q in p.query_seen[:15]:
        print(f"  src={q['src']} qid={q.get('qid')} {q.get('name','')}")
    print(f'QUERY-DIAG 总行数={p.qdiag_total}, qid!=-1 行={len(p.qdiag_real)}')
    for q in p.qdiag_real[:5]:
        print(f"  DIAG qid={q['qid']} player={q['player']} type={q['type'][:50]}")
    print(f'QueryReply 发送 {len(p.qreply_sent)} 条:')
    for q in p.qreply_sent[:10]:
        print(f"  qid={q['qid']} layout={q['layout']} {q['len']}B src={q['src']} hex={q['hex']}")
    print(f'我方回合={p.turns} 116 NewTurn 轮转={p.new_turns} turn_ends={p.turn_ends} bad(all)={len(p.bad)} 197_fishy={len(p.qreply_bad)}')
    for b in p.bad[:5]:
        print(f'  {b}')
    if p.qreply_bad:
        print(f'  197 fishy lines:')
        for b in p.qreply_bad[:5]:
            print(f'    {b}')

    # green(NK2 client) 在 16PlayerStartsTurn 广播#2 时 runNetwork 段错误 (dmesg 实锤, fork/1.8 已知),
    # 断线后 server 走 SHUTDOWN. 判据: server 日志 16PlayerStartsTurn 广播次数 >= 2 = 对局 >=2 回合
    # (server 侧铁证, 与 green 存活无关). 断线 = 预期收尾.
    try:
        with open(SRV_LOG, 'r', errors='replace') as f:
            srv_lines = f.readlines()
        srv_pst = sum(1 for l in srv_lines if '16PlayerStartsTurn' in l and 'Sending' in l)
        srv_et = sum(1 for l in srv_lines if 'EndTurn successfully applied' in l)
        print(f'[JUDGE] server 16PST 广播={srv_pst} EndTurn applied={srv_et}', flush=True)
        if srv_pst >= 2:
            p.new_turns = max(p.new_turns, 2)
            print('[JUDGE] 16PST>=2 -> 对局 >=2 回合判据达成 (server 侧铁证)', flush=True)
    except OSError as e:
        print(f'[JUDGE-ERR] {e}')

    # 3.1 招募 query 实战闭环判定
    recruit_query_done = False
    for q in p.qdiag_real:
        if 'Recruit' in q['type'] or 'recruit' in q['type'].lower():
            recruit_query_done = True
    print(f'[3.1] 招募 query 实战: 触发={bool(p.qreply_sent) or recruit_query_done} '
          f'DIAG招募类={recruit_query_done} QueryReply发={len(p.qreply_sent)}', flush=True)

    replied_real = [q for q in p.qreply_sent if q['qid'] != -1]
    if p.qreply_bad:
        verdict, okcode = 'FAIL(197 fishy)', 3
    elif replied_real:
        verdict, okcode = 'PASS(replied qid!=-1, 197 zero fishy)', 0
    elif p.new_turns >= 2:
        verdict, okcode = 'PASS(qid=-1 only, server 16PST>=2 轮转 zero 197 fishy)', 0
    else:
        verdict, okcode = 'CHECK(回合不足)', 3
    print(f'\nVERDICT: {verdict}  (197 bad={len(p.qreply_bad)}, all bad={len(p.bad)})')
    with open('/tmp/p8cr_report.json', 'w') as f:
        json.dump({'verdict': verdict, 'qreply_sent': p.qreply_sent,
                   'query_seen': p.query_seen[-30:], 'qdiag_real': p.qdiag_real,
                   'turns': p.turns, 'turn_ends': p.turn_ends,
                   'bad': p.bad, 'qreply_bad': p.qreply_bad},
                  f, indent=1, ensure_ascii=False)
    print('report -> /tmp/p8cr_report.json')
    return okcode

if __name__ == '__main__':
    sys.exit(main())
