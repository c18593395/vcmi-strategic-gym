#!/usr/bin/env python3
"""
P8-C 阶段5 — MoveHero(182) 探针 (离线闭环)
=================================================

目的
----
为 T13.10 多人对战验证补齐 MoveHero 实战闭环。
离线 mock server 模拟 server 侧:
  收 MoveHero(182) -> 应用校验 -> 回 PackageApplied(84) + TryMoveHero(109)

覆盖本轮关键路径:
  1. MoveHero serialize 顶层帧: isNull(1B) + pid(LVarInt) + tid=182(LVarInt) + 包数据
  2. MoveHero 字段序: player + request_id + path(len+int3*N) + layer + hid + transit
  3. TryMoveHero 字段序 (本轮已修正 packs.py):
       oid + result + start(int3) + end(int3) + movePoints
       + fowRevealed(len+int3*N) + attackedFrom(int3)
  4. PackageApplied 字段: request_id + is_successful
  5. result 语义: 1=SUCCESS / 0=FAILED (其他 2..5 保留)

对比
----
- 在线版: p8c_movehero_probe.py — 启真实 VCMI_server.exe + client.exe + Twins.h3m
- 离线版: 本文件 — 纯 mock, 无 VCMI 二进制, 无端口冲突, 无 kill_all
  与主训练线 (systemd homm3-train-v5) 零冲突, 可并行运行

用例矩阵
--------
  case1 default_success      : MoveHero(path=1pt, hid=5)     -> TryMoveHero result=1 SUCCESS
  case2 multi_point_path     : MoveHero(path=3pt)             -> TryMoveHero result=1, end=最后一点
  case3 fow_revealed_entries : TryMoveHero fowRevealed=[2 pts]-> 客户端解析到 2 个 tuple
  case4 rejected_move        : hid=999 (未知英雄)             -> TryMoveHero result=0 FAILED
  case5 endturn_roundtrip    : EndTurn(180) -> PlayerEndsTurn(102) 回流
  case6 request_id_echo      : 客户端发 request_id=42         -> PackageApplied request_id=42

跑法
----
  python py/p8/p8c_movehero_offline_probe.py
预期
----
6 个用例全部 PASS, 无失败, 退出码 0

作者: 2026-09-12, P8-C 阶段5 离线开发
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
from vcmi_protocol.protocol import parse_client_pack, parse_server_pack
from vcmi_protocol.packs import (
    MoveHero, EndTurn, QueryReply,
    PackageApplied, TryMoveHero, PlayerEndsTurn,
)


# ============================================================
# MockServer — 离线 mock VCMI 服务器 (MoveHero 版)
# ============================================================

class MockMoveServer:
    """
    收客户端 MoveHero/EndTurn, 按规则回包:
      - MoveHero(hid < 100)      -> PackageApplied(ok) + TryMoveHero(result=1, end=最后一点)
      - MoveHero(hid >= 100)     -> PackageApplied(ok=False) + TryMoveHero(result=0)
      - EndTurn                  -> PlayerEndsTurn
    """

    # MockServer 侧的 hero registry (只用于判定 hid 是否有效)
    HERO_VALID_MAX = 100

    def __init__(self, port=0):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('127.0.0.1', port))
        self.sock.listen(1)
        self.sock.settimeout(10.0)
        self.port = self.sock.getsockname()[1]

        self.conn: Optional[socket.socket] = None
        # [(tid, class_name, data_dict, raw_bytes)] — 客户端收到的下游包
        self.sent = []
        # [(qid, pack_type, request_id, payload, parsed_dict)] — server 收到的上行包
        self.incoming = []
        self._cv = threading.Condition()
        self._running = False
        self._recv_buf = bytearray()

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

    def accept_client(self):
        self.conn, _ = self.sock.accept()
        self.conn.settimeout(0.3)
        self._running = True
        threading.Thread(target=self._recv_loop, daemon=True).start()
        return True

    # -------------------------------------------------------
    # 收客户端 pack
    # -------------------------------------------------------

    def _recv_loop(self):
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
            tid = parsed.get('type_id')
            name = parsed.get('class_name')
            data = parsed.get('data') or {}

            with self._cv:
                self.incoming.append((tid, name, data, payload, parsed))
                self._cv.notify_all()

            print(f'  [SRV] 收到 {name}(tid={tid}, req_id={data.get("request_id", "?")})')

            # 按规则回应
            if tid == MoveHero.type_id:
                self._handle_move_hero(data, payload)
            elif tid == EndTurn.type_id:
                self._handle_end_turn(data)
            else:
                print(f'  [SRV] 未知 server pack tid={tid}, 忽略')

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
    # 下发 client pack
    # -------------------------------------------------------

    def send_client_pack(self, pack):
        ser = BinarySerializer()
        ser.write_bool(False)
        ser.write_int(0)
        ser.write_int(pack.type_id)
        pack.serialize(ser)
        frame = ser.get_bytes()
        payload = struct.pack('<I', len(frame)) + frame
        self.conn.sendall(payload)
        with self._cv:
            self.sent.append((pack.type_id, pack.__class__.__name__, frame, pack))
            self._cv.notify_all()

    # -------------------------------------------------------
    # 业务规则
    # -------------------------------------------------------

    def _handle_move_hero(self, data, raw):
        hid = data.get('hid', 0)
        path = data.get('path', [])
        request_id = data.get('request_id', 0)
        success = hid < self.HERO_VALID_MAX and len(path) > 0

        # PackageApplied
        pa = PackageApplied(request_id=request_id, is_successful=success)
        self.send_client_pack(pa)

        # TryMoveHero
        if success and path:
            last = path[-1]
            first = path[0]
            start = (first[0], first[1], first[2]) if isinstance(first, tuple) else (first.x, first.y, first.z)
            end = (last[0], last[1], last[2]) if isinstance(last, tuple) else (last.x, last.y, last.z)
            # 若 path 含多个点, 客户端收到 fow_revealed = [path[1], path[2], ...]
            fow = []
            for p in path[1:]:
                if isinstance(p, tuple):
                    fow.append((p[0], p[1], p[2]))
                else:
                    fow.append((p.x, p.y, p.z))
            t = TryMoveHero(oid=hid, result=1, start=start, end=end,
                            move_points=len(path) * 10,
                            fow_revealed=fow,
                            attacked_from=(0, 0, 0))
        else:
            t = TryMoveHero(oid=hid, result=0,
                            start=(0, 0, 0), end=(0, 0, 0),
                            move_points=0, fow_revealed=[],
                            attacked_from=(0, 0, 0))
        self.send_client_pack(t)

        tag = 'SUCCESS' if success else 'FAILED'
        print(f'  [SRV] -> PackageApplied(ok={success}) + TryMoveHero(result={t.result}, {tag})')

    def _handle_end_turn(self, data):
        self.send_client_pack(PlayerEndsTurn())

    # -------------------------------------------------------
    # 同步工具
    # -------------------------------------------------------

    def wait_incoming(self, predicate: Callable, timeout=3.0):
        deadline = time.time() + timeout
        with self._cv:
            while True:
                for entry in self.incoming:
                    if predicate(entry):
                        return entry
                remaining = deadline - time.time()
                if remaining <= 0:
                    return None
                self._cv.wait(timeout=remaining)

    def wait_client_pack(self, tid: int, timeout=3.0):
        """等待 server 侧已发送过的 (tid, ...) 记录"""
        deadline = time.time() + timeout
        with self._cv:
            while True:
                for e in self.sent:
                    if e[0] == tid:
                        return e
                remaining = deadline - time.time()
                if remaining <= 0:
                    return None
                self._cv.wait(timeout=remaining)

    def clear_incoming(self):
        with self._cv:
            self.incoming.clear()

    def clear_sent(self):
        with self._cv:
            self.sent.clear()


# ============================================================
# ProbeClient — MoveHero 探针客户端
# ============================================================

class ProbeClient:
    """
    VCMITCPConnection -> recv_frame -> parse_client_pack
    所有网络 IO 在主线程同步, 无多线程竞争。
    """

    def __init__(self, host, port):
        self.conn = VCMITCPConnection(host, port)
        self.received = []         # [(type_id, class_name, data_dict)]

    def connect(self):
        return self.conn.connect()

    def disconnect(self):
        self.conn.disconnect()

    def send_pack(self, pack):
        self.conn.send_pack(pack)

    def pump(self, timeout=3.0):
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

            if tid == TryMoveHero.type_id:
                print(f'  [CLI] 收到 TryMoveHero(oid={d.get("oid")}, result={d.get("result")}, '
                      f'start={d.get("start")} end={d.get("end")}, fow={len(d.get("fow_revealed", []))})')
            elif tid == PackageApplied.type_id:
                print(f'  [CLI] 收到 PackageApplied(req_id={d.get("request_id")}, ok={d.get("is_successful")})')
            elif tid == PlayerEndsTurn.type_id:
                print(f'  [CLI] 收到 PlayerEndsTurn')
            else:
                print(f'  [CLI] 收到 {name}(tid={tid})')

    def clear_received(self):
        self.received.clear()


# ============================================================
# 断言工具
# ============================================================

def _wait_cli(cli, tid, timeout=3.0):
    """等待客户端收到指定 tid 的包, 返回 data_dict 或 None"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        for _, _, d in cli.received:
            for t, n, dd in cli.received:
                if t == tid:
                    return dd
        time.sleep(0.05)
        cli.pump(timeout=0.1)
    return None


def _find_cli(cli, tid):
    for t, n, d in cli.received:
        if t == tid:
            return d
    return None


def _find_all_cli(cli, tid):
    return [d for t, n, d in cli.received if t == tid]


# ============================================================
# 6 个用例
# ============================================================

def case1_default_success(srv, cli):
    """MoveHero(path=1pt, hid=5) -> TryMoveHero result=1 SUCCESS"""
    srv.clear_incoming()
    cli.clear_received()
    mh = MoveHero(path=[(8, 8, 0)], layer=0, hid=5, transit=False, player=0, request_id=1)
    print(f'  [CLI] 发送 MoveHero(hid=5, path=[(8,8,0)], req_id=1)')
    cli.send_pack(mh)
    cli.pump(3.0)

    ok = True
    # 客户端: 收到 PackageApplied(request_id=1, ok=True)
    pa = _find_cli(cli, PackageApplied.type_id)
    if pa is None:
        print(f'  [case1] FAIL: 未收到 PackageApplied')
        ok = False
    else:
        if pa.get('request_id') != 1:
            print(f'  [case1] FAIL: PackageApplied.request_id 期望=1 实际={pa.get("request_id")}')
            ok = False
        if not pa.get('is_successful'):
            print(f'  [case1] FAIL: PackageApplied.is_successful 期望=True 实际={pa.get("is_successful")}')
            ok = False

    # 客户端: 收到 TryMoveHero result=1, end=(8,8,0)
    tm = _find_cli(cli, TryMoveHero.type_id)
    if tm is None:
        print(f'  [case1] FAIL: 未收到 TryMoveHero')
        ok = False
    else:
        if tm.get('result') != 1:
            print(f'  [case1] FAIL: TryMoveHero.result 期望=1 实际={tm.get("result")}')
            ok = False
        if tm.get('oid') != 5:
            print(f'  [case1] FAIL: TryMoveHero.oid 期望=5 实际={tm.get("oid")}')
            ok = False
        if tuple(tm.get('end') or ()) != (8, 8, 0):
            print(f'  [case1] FAIL: TryMoveHero.end 期望=(8,8,0) 实际={tm.get("end")}')
            ok = False
        if tm.get('move_points') != 10:
            print(f'  [case1] FAIL: move_points 期望=10 实际={tm.get("move_points")}')
            ok = False

    # server 侧收到 MoveHero, 字段解析正确
    entry = srv.wait_incoming(
        lambda e: e[0] == MoveHero.type_id, timeout=2.0)
    if entry is None:
        print(f'  [case1] FAIL: server 侧未收到 MoveHero')
        ok = False
    else:
        _, _, d, raw, _ = entry
        if d.get('hid') != 5:
            print(f'  [case1] FAIL: server 侧 hid 期望=5 实际={d.get("hid")}')
            ok = False
        if d.get('request_id') != 1:
            print(f'  [case1] FAIL: server 侧 request_id 期望=1 实际={d.get("request_id")}')
            ok = False
        path0 = d.get('path')
        if not path0:
            print(f'  [case1] FAIL: server 侧 path 为空')
            ok = False
        else:
            p0 = path0[0]
            if isinstance(p0, tuple):
                got0 = tuple(p0)
            else:
                got0 = (p0.x, p0.y, p0.z)
            if got0 != (8, 8, 0):
                print(f'  [case1] FAIL: server 侧 path[0] 期望=(8,8,0) 实际={got0}')
                ok = False
        if d.get('layer') != 0:
            print(f'  [case1] FAIL: server 侧 layer 期望=0 实际={d.get("layer")}')
            ok = False
        if d.get('transit') is not False:
            print(f'  [case1] FAIL: server 侧 transit 期望=False 实际={d.get("transit")}')
            ok = False

    if ok:
        print(f'  [case1] PASS: MoveHero 单点 -> TryMoveHero SUCCESS (raw={len(entry[3]) if entry else 0}B)')
    return ok


def case2_multi_point_path(srv, cli):
    """MoveHero(path=3pt) -> TryMoveHero end=最后一点, fow=中间点"""
    srv.clear_incoming()
    cli.clear_received()
    path = [(5, 5, 0), (6, 6, 0), (7, 7, 0)]
    mh = MoveHero(path=path, layer=0, hid=5, transit=False, player=0, request_id=2)
    print(f'  [CLI] 发送 MoveHero(hid=5, path={path}, req_id=2)')
    cli.send_pack(mh)
    cli.pump(3.0)

    ok = True
    tm = _find_cli(cli, TryMoveHero.type_id)
    if tm is None:
        print(f'  [case2] FAIL: 未收到 TryMoveHero')
        ok = False
    else:
        if tm.get('result') != 1:
            print(f'  [case2] FAIL: result 期望=1 实际={tm.get("result")}')
            ok = False
        if tuple(tm.get('start') or ()) != (5, 5, 0):
            print(f'  [case2] FAIL: start 期望=(5,5,0) 实际={tm.get("start")}')
            ok = False
        if tuple(tm.get('end') or ()) != (7, 7, 0):
            print(f'  [case2] FAIL: end 期望=(7,7,0) 实际={tm.get("end")}')
            ok = False
        fow = tm.get('fow_revealed') or []
        # path[1:] = [(6,6,0), (7,7,0)] — 起点已算在 start 里, 从 path[1] 开始算 fow
        if len(fow) != 2:
            print(f'  [case2] FAIL: fow_revealed 长度期望=2 实际={len(fow)}')
            ok = False
        else:
            for i, exp in enumerate([(6, 6, 0), (7, 7, 0)]):
                if tuple(fow[i]) != exp:
                    print(f'  [case2] FAIL: fow[{i}] 期望={exp} 实际={fow[i]}')
                    ok = False
        if tm.get('move_points') != 30:
            print(f'  [case2] FAIL: move_points 期望=30 实际={tm.get("move_points")}')
            ok = False

    # server 侧 path 长度 3
    entry = srv.wait_incoming(lambda e: e[0] == MoveHero.type_id, timeout=2.0)
    if entry is None:
        print(f'  [case2] FAIL: server 未收到 MoveHero')
        ok = False
    else:
        d = entry[2]
        if len(d.get('path') or []) != 3:
            print(f'  [case2] FAIL: server 侧 path 长度期望=3 实际={len(d.get("path") or [])}')
            ok = False

    if ok:
        print(f'  [case2] PASS: 多点 path -> end 为最后一点, fow 包含中间点')
    return ok


def case3_fow_revealed_entries(srv, cli):
    """MoveHero(path=4pt) -> TryMoveHero fowRevealed 有 3 个 int3"""
    srv.clear_incoming()
    cli.clear_received()
    path = [(2, 2, 0), (3, 2, 0), (4, 2, 0), (5, 2, 0)]
    mh = MoveHero(path=path, layer=0, hid=7, transit=False, player=0, request_id=3)
    print(f'  [CLI] 发送 MoveHero(hid=7, path 长度=4, req_id=3)')
    cli.send_pack(mh)
    cli.pump(3.0)

    ok = True
    tm = _find_cli(cli, TryMoveHero.type_id)
    if tm is None:
        print(f'  [case3] FAIL: 未收到 TryMoveHero')
        ok = False
    else:
        fow = tm.get('fow_revealed') or []
        if len(fow) != 3:
            print(f'  [case3] FAIL: fow_revealed 长度期望=3 实际={len(fow)}')
            ok = False
        else:
            expected = [(3, 2, 0), (4, 2, 0), (5, 2, 0)]
            for i, (got, exp) in enumerate(zip(fow, expected)):
                if tuple(got) != exp:
                    print(f'  [case3] FAIL: fow[{i}] 期望={exp} 实际={got}')
                    ok = False
        # attacked_from 应正确解析 (默认 (0,0,0))
        af = tm.get('attacked_from')
        if tuple(af or ()) != (0, 0, 0):
            print(f'  [case3] FAIL: attacked_from 期望=(0,0,0) 实际={af}')
            ok = False

    if ok:
        print(f'  [case3] PASS: fow_revealed 3 条 int3 全部解析正确')
    return ok


def case4_rejected_move(srv, cli):
    """hid=999 (未知英雄) -> PackageApplied(ok=False) + TryMoveHero result=0"""
    srv.clear_incoming()
    cli.clear_received()
    mh = MoveHero(path=[(8, 8, 0)], layer=0, hid=999, transit=False, player=0, request_id=4)
    print(f'  [CLI] 发送 MoveHero(hid=999, req_id=4) — 期望拒绝')
    cli.send_pack(mh)
    cli.pump(3.0)

    ok = True
    pa = _find_cli(cli, PackageApplied.type_id)
    if pa is None:
        print(f'  [case4] FAIL: 未收到 PackageApplied')
        ok = False
    else:
        if pa.get('request_id') != 4:
            print(f'  [case4] FAIL: request_id 期望=4 实际={pa.get("request_id")}')
            ok = False
        if pa.get('is_successful') is not False:
            print(f'  [case4] FAIL: is_successful 期望=False 实际={pa.get("is_successful")}')
            ok = False

    tm = _find_cli(cli, TryMoveHero.type_id)
    if tm is None:
        print(f'  [case4] FAIL: 未收到 TryMoveHero')
        ok = False
    else:
        if tm.get('result') != 0:
            print(f'  [case4] FAIL: result 期望=0 (FAILED) 实际={tm.get("result")}')
            ok = False
        if tm.get('oid') != 999:
            print(f'  [case4] FAIL: oid 期望=999 实际={tm.get("oid")}')
            ok = False
        if tm.get('move_points') != 0:
            print(f'  [case4] FAIL: move_points 期望=0 实际={tm.get("move_points")}')
            ok = False

    if ok:
        print(f'  [case4] PASS: 未知 hid 被拒绝, result=0')
    return ok


def case5_endturn_roundtrip(srv, cli):
    """EndTurn(180) -> PlayerEndsTurn(102) 回流"""
    srv.clear_incoming()
    cli.clear_received()
    et = EndTurn(player=0, request_id=5)
    print(f'  [CLI] 发送 EndTurn(player=0, req_id=5)')
    cli.send_pack(et)
    cli.pump(3.0)

    ok = True
    pe = _find_cli(cli, PlayerEndsTurn.type_id)
    if pe is None:
        print(f'  [case5] FAIL: 未收到 PlayerEndsTurn')
        ok = False

    entry = srv.wait_incoming(lambda e: e[0] == EndTurn.type_id, timeout=2.0)
    if entry is None:
        print(f'  [case5] FAIL: server 未收到 EndTurn')
        ok = False
    else:
        d = entry[2]
        if d.get('request_id') != 5:
            print(f'  [case5] FAIL: request_id 期望=5 实际={d.get("request_id")}')
            ok = False
        if d.get('player') != 0:
            print(f'  [case5] FAIL: player 期望=0 实际={d.get("player")}')
            ok = False

    if ok:
        print(f'  [case5] PASS: EndTurn 双向回环')
    return ok


def case6_request_id_echo(srv, cli):
    """客户端发 request_id=42 -> PackageApplied 回显 request_id=42"""
    srv.clear_incoming()
    cli.clear_received()
    mh = MoveHero(path=[(9, 9, 0)], layer=0, hid=10, transit=False, player=0, request_id=42)
    print(f'  [CLI] 发送 MoveHero(hid=10, req_id=42)')
    cli.send_pack(mh)
    cli.pump(3.0)

    ok = True
    pa = _find_cli(cli, PackageApplied.type_id)
    if pa is None:
        print(f'  [case6] FAIL: 未收到 PackageApplied')
        ok = False
    else:
        if pa.get('request_id') != 42:
            print(f'  [case6] FAIL: request_id 回显期望=42 实际={pa.get("request_id")}')
            ok = False
        if pa.get('is_successful') is not True:
            print(f'  [case6] FAIL: is_successful 期望=True 实际={pa.get("is_successful")}')
            ok = False

    if ok:
        print(f'  [case6] PASS: request_id 严格回显 (双向一致)')
    return ok


CASES = [
    ("case1: MoveHero(1pt) -> TryMoveHero SUCCESS",       case1_default_success),
    ("case2: MoveHero(3pt path) -> end=最后, fow=中间",   case2_multi_point_path),
    ("case3: fowRevealed 3 条 int3 全部解析",             case3_fow_revealed_entries),
    ("case4: 未知 hid -> PackageApplied(ok=False)+result=0", case4_rejected_move),
    ("case5: EndTurn -> PlayerEndsTurn 回环",             case5_endturn_roundtrip),
    ("case6: request_id 严格回显",                        case6_request_id_echo),
]


# ============================================================
# 主流程
# ============================================================

def main():
    print('=' * 60)
    print('P8-C MoveHero 探针 — 离线闭环测试')
    print('=' * 60)

    with MockMoveServer() as srv:
        print(f'[SRV] mock 服务器已启动, 端口={srv.port}')

        cli = ProbeClient('127.0.0.1', srv.port)
        if not cli.connect():
            print('[CLI] 连接失败, 退出')
            return 1
        if not srv.accept_client():
            print('[SRV] 未接到客户端, 退出')
            return 1
        print('[CLI] 探针客户端已连接')
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

        print('\n' + '=' * 60)
        print('P8-C MoveHero 探针 — 结果汇总')
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
