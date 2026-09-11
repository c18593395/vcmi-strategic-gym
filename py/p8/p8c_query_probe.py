#!/usr/bin/env python3
"""
P8-C 阶段4 — QueryReply(197) 探针 (离线闭环)
=================================================

目的
----
为 T13.10 多人对战验证补齐 Query 派生类实战闭环。
覆盖本轮修好的关键路径:
  1. QueryID 字段序 (queryID 首字段, 已从 player 先行修正)
  2. QueryManager 用真实 qid (已从 type_id 简化改为 data['query_id'])
  3. qid == -1 语义 (VCMI 官方 INVALID, 跳过回复)
  4. 三类 Query 派生: HeroLevelUp(154) / BlockingDialog(156) / GarrisonDialog(157)
  5. PlayerStartsTurn(88) — 已正确, 回归测试

设计
----
离线 mock server (无真实 VCMI 二进制):
  - MockServer: 裸 TCP, 主动下发 Query 包 (帧格式: [uint32 length][isNull+pid+tid+data])
  - ProbeClient: 用 VCMITCPConnection + parse_client_pack + QueryManager.handle_query
  - MockServer 收 QueryReply(197) 用 parse_server_pack 验证 qid/reply

用例矩阵
--------
  case1 default        : HeroLevelUp(qid=7)           -> QueryReply qid=7, reply=0
  case2 skip_invalid   : PlayerStartsTurn(qid=-1)     -> 无 QueryReply (skip)
  case3 custom_handler : HeroLevelUp(qid=7) + 自定义  -> QueryReply qid=7, reply=3
  case4 blocking       : BlockingDialog(qid=12)       -> QueryReply qid=12, reply=0
  case5 garrison       : GarrisonDialog(qid=15)       -> QueryReply qid=15, reply=0
  case6 player_start   : PlayerStartsTurn(qid=42)     -> QueryReply qid=42, reply=0 (回归)

跑法
----
  python py/p8/p8c_query_probe.py
预期
----
6 个用例全部 PASS, 无失败, 退出码 0

作者: 2026-09-12, P8-C 阶段4 离线开发
"""
import sys
import os
import time
import socket
import struct
import threading
from typing import Optional, Callable

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vcmi_protocol.connection import VCMITCPConnection
from vcmi_protocol.serialization import BinarySerializer, BinaryDeserializer
from vcmi_protocol.protocol import parse_client_pack, parse_server_pack, QueryManager
from vcmi_protocol.packs import (
    HeroLevelUp, BlockingDialog, GarrisonDialog,
    PlayerStartsTurn, QueryReply,
)


# ============================================================
# MockServer — 离线 mock 服务器
# ============================================================

class MockServer:
    """
    离线 mock VCMI 服务器

    - TCP 监听 127.0.0.1:port
    - 主动下发 Query 包 (帧格式: [uint32 length][isNull+pid+tid+data])
    - 接收客户端回传的 QueryReply, 用 parse_server_pack 验证
    - 支持 wait_for_reply() 条件变量同步
    """

    def __init__(self, port=0):
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('127.0.0.1', port))
        self.sock.listen(1)
        self.sock.settimeout(10.0)
        self.port = self.sock.getsockname()[1]

        self.conn: Optional[socket.socket] = None
        self.replies = []          # [(qid, reply, raw_bytes, parsed_dict)]
        self._reply_cv = threading.Condition()
        self._running = False
        self._recv_buf = bytearray()
        self._recv_lock = threading.Lock()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        self._running = False
        if self.conn:
            try:
                self.conn.close()
            except Exception:
                pass
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass

    # -------------------------------------------------------
    # 接收客户端连接
    # -------------------------------------------------------

    def accept_client(self):
        """阻塞等待客户端 TCP 连接, 启动后台接收线程"""
        self.conn, _ = self.sock.accept()
        self.conn.settimeout(0.3)
        self._running = True
        threading.Thread(target=self._recv_loop, daemon=True).start()
        return True

    def _recv_loop(self):
        """从 conn 收帧, 解析为 server pack, 记录 QueryReply"""
        while self._running:
            try:
                header = self._recv_exact(4)
                if header is None:
                    break
                length = struct.unpack('<I', header)[0]
                if length == 0:
                    continue
                payload = self._recv_exact(length)
                if payload is None:
                    break
            except Exception as e:
                print(f'  [SRV] recv err: {e}')
                break

            parsed = parse_server_pack(payload)
            if parsed is None:
                continue
            if parsed.get('type_id') != QueryReply.type_id:
                print(f'  [SRV] 非 QueryReply tid={parsed.get("type_id")} {parsed.get("class_name")}')
                continue

            d = parsed.get('data', {})
            qid = d.get('qid')
            reply = d.get('reply')
            entry = (qid, reply, payload, parsed)
            with self._reply_cv:
                self.replies.append(entry)
                print(f'  [SRV] 收到 QueryReply qid={qid} reply={reply}')
                self._reply_cv.notify_all()

    def _recv_exact(self, n: int) -> Optional[bytes]:
        while len(self._recv_buf) < n:
            try:
                chunk = self.conn.recv(4096)
                if not chunk:
                    return None
                self._recv_buf.extend(chunk)
            except socket.timeout:
                time.sleep(0.02)
            except Exception:
                return None
        data = bytes(self._recv_buf[:n])
        del self._recv_buf[:n]
        return data

    # -------------------------------------------------------
    # 下发 Query 包 (顶层帧: isNull+pid+tid+包数据)
    # -------------------------------------------------------

    def send_query(self, pack):
        ser = BinarySerializer()
        ser.write_bool(False)       # isNull = false
        ser.write_int(0)            # pid (首指针)
        ser.write_int(pack.type_id)  # tid
        pack.serialize(ser)
        frame = ser.get_bytes()
        payload = struct.pack('<I', len(frame)) + frame
        self.conn.sendall(payload)
        print(f'  [SRV] 下发 {pack.__class__.__name__}(tid={pack.type_id}, qid={getattr(pack, "query_id", "?")}) — {len(frame)}B')

    # -------------------------------------------------------
    # 条件同步
    # -------------------------------------------------------

    def wait_for_reply(self, qid, timeout=3.0) -> Optional[tuple]:
        """等待 qid 对应的 QueryReply 到达"""
        deadline = time.time() + timeout
        with self._reply_cv:
            while True:
                for e in self.replies:
                    if e[0] == qid:
                        return e
                remaining = deadline - time.time()
                if remaining <= 0:
                    return None
                self._reply_cv.wait(timeout=remaining)

    def wait_no_reply(self, timeout=1.5) -> bool:
        """等待指定时间, 期间无新 QueryReply 到达 (用于 qid=-1 skip 场景)"""
        with self._reply_cv:
            snapshot = len(self.replies)
        time.sleep(timeout)
        with self._reply_cv:
            return len(self.replies) == snapshot


# ============================================================
# ProbeClient — 探针客户端
# ============================================================

class ProbeClient:
    """
    探针客户端:
      VCMITCPConnection -> parse_client_pack -> QueryManager.handle_query -> send QueryReply

    所有网络 IO 在主线程同步执行, 避免多线程竞争。
    """

    def __init__(self, host, port, player=0):
        self.conn = VCMITCPConnection(host, port)
        self.player = player
        self.qmgr = QueryManager(player=player, auto_reply=True)
        self.received = []         # [(type_id, class_name, data_dict)]

    def connect(self):
        return self.conn.connect()

    def disconnect(self):
        self.conn.disconnect()

    def pump(self, timeout=3.0, quiet=False):
        """
        同步收包 + 处理 Query
        quiet=True 用于 skip 场景 (无需回复, 只需观察)
        """
        end = time.time() + timeout
        while time.time() < end:
            try:
                data = self.conn.recv_frame()
            except Exception as e:
                print(f'  [CLI] recv err: {e}')
                break
            if data is None:
                time.sleep(0.02)
                continue
            if len(data) == 0:
                continue

            parsed = parse_client_pack(data)
            if parsed is None:
                continue
            tid = parsed.get('type_id')
            name = parsed.get('class_name')
            d = parsed.get('data') or {}
            self.received.append((tid, name, d))
            if not quiet:
                print(f'  [CLI] 收到 {name}(tid={tid}, qid={d.get("query_id", "?")})')

            if tid in QueryManager.QUERY_TYPES:
                self.qmgr.handle_query(parsed, self._send)

    def _send(self, pack):
        """发送函数 (QueryManager.handle_query 的 send_fn 参数)"""
        if isinstance(pack, bytes):
            self.conn.send_frame(pack)
        else:
            self.conn.send_pack(pack)


# ============================================================
# 用例定义
# ============================================================

def _emit(srv: MockServer, pack):
    srv.send_query(pack)
    time.sleep(0.15)   # 让客户端接收机会


def _pump(cli: ProbeClient, timeout=3.0, quiet=False):
    cli.pump(timeout=timeout, quiet=quiet)


def _assert_reply(srv: MockServer, cli: ProbeClient, qid, expect_reply,
                  expect_query_type=None, expect_query_data=None,
                  label=''):
    """
    断言: 收到 QueryReply(qid, reply), 且客户端本地解析到的 Query 类型/数据正确
    """
    print(f'  [{label}] 等待 qid={qid} QueryReply...')
    entry = srv.wait_for_reply(qid=qid, timeout=3.0)
    if entry is None:
        print(f'  [{label}] FAIL: 未收到 qid={qid} 的 QueryReply')
        return False

    got_qid, got_reply, raw, parsed = entry
    ok = True

    if got_qid != qid:
        print(f'  [{label}] FAIL: qid 期望={qid} 实际={got_qid}')
        ok = False
    if expect_reply is not None and got_reply != expect_reply:
        print(f'  [{label}] FAIL: reply 期望={expect_reply} 实际={got_reply}')
        ok = False

    # 顶层 wire 层校验
    if parsed.get('type_id') != QueryReply.type_id:
        print(f'  [{label}] FAIL: 顶层 tid 期望={QueryReply.type_id} 实际={parsed.get("type_id")}')
        ok = False

    # 客户端侧: query_history 中该 qid 记录正确
    hist = [h for h in cli.qmgr.query_history if h.get('qid') == qid]
    if not hist:
        print(f'  [{label}] FAIL: 客户端 query_history 无 qid={qid} 记录')
        ok = False
    else:
        h = hist[-1]
        if h.get('reply') != expect_reply:
            print(f'  [{label}] FAIL: query_history reply 期望={expect_reply} 实际={h.get("reply")}')
            ok = False
        if expect_query_type and h.get('name') != expect_query_type:
            print(f'  [{label}] FAIL: query_history name 期望={expect_query_type} 实际={h.get("name")}')
            ok = False

    # 客户端侧: received 中该 Query 的数据字段正确
    if expect_query_type:
        q_rec = None
        for tid, name, d in cli.received:
            if name == expect_query_type and d.get('query_id') == qid:
                q_rec = (tid, name, d)
        if q_rec is None:
            print(f'  [{label}] FAIL: 客户端 received 中无 {expect_query_type}(qid={qid})')
            ok = False
        elif expect_query_data:
            for k, v in expect_query_data.items():
                if q_rec[2].get(k) != v:
                    print(f'  [{label}] FAIL: {expect_query_type}.{k} 期望={v} 实际={q_rec[2].get(k)}')
                    ok = False

    if ok:
        print(f'  [{label}] PASS: qid={got_qid} reply={got_reply} (raw={len(raw)}B)')
    return ok


def _assert_skip(srv: MockServer, cli: ProbeClient, label=''):
    """断言: qid=-1 场景下不发 QueryReply (skip)"""
    print(f'  [{label}] 观察 1.5s 内是否有 QueryReply...')
    no_new = srv.wait_no_reply(timeout=1.5)
    if no_new:
        print(f'  [{label}] PASS: 未收到 QueryReply (skip 正确)')
        # 检查 query_history 记录了 skipped=True
        skipped = [h for h in cli.qmgr.query_history if h.get('skipped')]
        if skipped:
            print(f'  [{label}] PASS: query_history 记录 skipped=True')
            return True
        else:
            print(f'  [{label}] WARN: query_history 无 skipped 记录 (但不影响主断言)')
            return True
    else:
        print(f'  [{label}] FAIL: 收到意外的 QueryReply, 应跳过')
        return False


# ============================================================
# 6 个用例函数
# ============================================================

def case1_default_hero_level_up(srv, cli):
    """HeroLevelUp(qid=7) 默认 handler -> QueryReply qid=7 reply=0"""
    _emit(srv, HeroLevelUp(player=0, hero_id=3, primskill=2, skills=[5, 8], query_id=7))
    _pump(cli, 3.0)
    return _assert_reply(
        srv, cli, qid=7, expect_reply=0,
        expect_query_type='HeroLevelUp',
        expect_query_data={'hero_id': 3, 'primskill': 2, 'skills': [5, 8], 'player': 0},
        label='case1',
    )


def case2_skip_invalid_qid(srv, cli):
    """PlayerStartsTurn(qid=-1) 跳过回复"""
    _emit(srv, PlayerStartsTurn(player=0, query_id=-1))
    _pump(cli, 2.0, quiet=True)
    return _assert_skip(srv, cli, label='case2')


def case3_custom_handler(srv, cli):
    """HeroLevelUp(qid=7) + 自定义 handler -> reply=3"""
    # 清空历史 replies, 避免 case1 的 qid=7 (reply=0) 遗留导致 wait_for_reply 命中旧条目
    with srv._reply_cv:
        srv.replies.clear()
    cli.qmgr.register_handler(HeroLevelUp.type_id, lambda d: 3)
    try:
        _emit(srv, HeroLevelUp(player=0, hero_id=5, primskill=1, skills=[2, 6], query_id=7))
        _pump(cli, 3.0)
        return _assert_reply(
            srv, cli, qid=7, expect_reply=3,
            expect_query_type='HeroLevelUp',
            expect_query_data={'hero_id': 5, 'primskill': 1, 'skills': [2, 6]},
            label='case3',
        )
    finally:
        # 清理 handler, 避免污染后续 case
        cli.qmgr.query_handlers.pop(HeroLevelUp.type_id, None)


def case4_blocking_dialog(srv, cli):
    """BlockingDialog(qid=12) -> QueryReply qid=12 reply=0"""
    _emit(srv, BlockingDialog(text='Confirm?', player=0, flags=5, sound_id=42, query_id=12))
    _pump(cli, 3.0)
    return _assert_reply(
        srv, cli, qid=12, expect_reply=0,
        expect_query_type='BlockingDialog',
        expect_query_data={'text': 'Confirm?', 'flags': 5, 'sound_id': 42, 'player': 0},
        label='case4',
    )


def case5_garrison_dialog(srv, cli):
    """GarrisonDialog(qid=15) -> QueryReply qid=15 reply=0"""
    _emit(srv, GarrisonDialog(objid=42, hid=7, removable_units=True, query_id=15))
    _pump(cli, 3.0)
    return _assert_reply(
        srv, cli, qid=15, expect_reply=0,
        expect_query_type='GarrisonDialog',
        expect_query_data={'objid': 42, 'hid': 7, 'removable_units': True},
        label='case5',
    )


def case6_player_starts_turn_valid(srv, cli):
    """PlayerStartsTurn(qid=42) 真实 query -> QueryReply qid=42 reply=0 (回归)"""
    _emit(srv, PlayerStartsTurn(player=0, query_id=42))
    _pump(cli, 3.0)
    return _assert_reply(
        srv, cli, qid=42, expect_reply=0,
        expect_query_type='PlayerStartsTurn',
        expect_query_data={'player': 0},
        label='case6',
    )


CASES = [
    ("case1: HeroLevelUp default -> qid=7 reply=0",              case1_default_hero_level_up),
    ("case2: PlayerStartsTurn qid=-1 -> skip",                   case2_skip_invalid_qid),
    ("case3: HeroLevelUp + custom handler -> reply=3",           case3_custom_handler),
    ("case4: BlockingDialog -> qid=12 reply=0",                  case4_blocking_dialog),
    ("case5: GarrisonDialog -> qid=15 reply=0",                  case5_garrison_dialog),
    ("case6: PlayerStartsTurn qid=42 (回归) -> reply=0",         case6_player_starts_turn_valid),
]


# ============================================================
# 主流程
# ============================================================

def main():
    print('=' * 60)
    print('P8-C QueryReply 探针 — 离线闭环测试')
    print('=' * 60)

    with MockServer() as srv:
        print(f'[SRV] mock 服务器已启动, 端口={srv.port}')

        cli = ProbeClient('127.0.0.1', srv.port, player=0)
        if not cli.connect():
            print('[CLI] 连接失败, 退出')
            return 1
        if not srv.accept_client():
            print('[SRV] 未接到客户端, 退出')
            return 1
        print(f'[CLI] 探针客户端已连接 (player=0)')
        print('-' * 60)

        failed = []
        for i, (name, fn) in enumerate(CASES, 1):
            print(f'\n[{i}/{len(CASES)}] {name}')
            try:
                ok = fn(srv, cli)
            except Exception as e:
                import traceback
                traceback.print_exc()
                ok = False
            if not ok:
                failed.append(name)

        # 清理已注册 handler, 避免 case3 的自定义 handler 污染后续测试
        # (注: 用例内部已按顺序隔离, 这里仅为可读性)

        print('\n' + '=' * 60)
        print('P8-C QueryReply 探针 — 结果汇总')
        print('=' * 60)
        print(f'总用例: {len(CASES)}')
        print(f'通过:   {len(CASES) - len(failed)}')
        print(f'失败:   {len(failed)}')
        if failed:
            for f in failed:
                print(f'  FAIL: {f}')
            print('\n[RESULT] FAIL')
            cli.disconnect()
            return 1
        else:
            print('\n[RESULT] ALL PASS')
            cli.disconnect()
            return 0


if __name__ == '__main__':
    sys.exit(main())
