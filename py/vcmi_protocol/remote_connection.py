"""
P8-D 跨机器部署 — 远程连接层
基于已有 VCMITCPConnection 扩展，增加:
  1. 认证握手 (auth.py Token)
  2. 连接重试 (指数退避)
  3. 健康监控 (心跳间隔可配)
  4. 优雅断连 (close 不阻塞)
"""
from __future__ import annotations
import socket
import time
import struct
import threading
from typing import Optional, Callable
from dataclasses import dataclass

from .connection import VCMITCPConnection
from .auth import AuthToken, TokenIssuer, TokenVerifier


class RemoteConnectionError(Exception):
    """远程连接通用异常"""
    pass


class AuthFailedError(RemoteConnectionError):
    """认证失败"""
    pass


@dataclass
class RemoteConnConfig:
    host: str = "127.0.0.1"
    port: int = 3030
    auth_enabled: bool = True
    hsk: Optional[bytes] = None
    client_id: str = "ai-client-001"
    connect_timeout: float = 10.0
    auth_timeout: float = 5.0
    max_retries: int = 3
    retry_backoff: float = 2.0
    heartbeat_interval: float = 30.0


class RemoteVCMITCPConnection:
    """
    远程 VCMI TCP 连接 (含认证)
    
    协议升级:
      原有:  4B length + payload (VCMI 原生)
      新增:  连接后先发 1 帧 AuthToken (4B len + JSON token)
            server 回 1 字节 ACK: 0x01=ok, 0x00=fail
    
    设计取舍:
      - 不把认证帧混入 VCMI 游戏帧，单独一次握手，游戏帧照旧走 4B+payload
      - 这样 VCMI 原生 binary 包格式 0 改动 (T13.3 已冻结)
    """

    def __init__(self, config: RemoteConnConfig):
        self.cfg = config
        self._sock: Optional[socket.socket] = None
        self._connected = False
        self._authenticated = False
        self._lock = threading.Lock()

        # 认证组件
        if config.auth_enabled:
            if not config.hsk:
                raise ValueError("auth_enabled=True 但 hsk 未提供")
            self._issuer = TokenIssuer(config.hsk, config.client_id)
        else:
            self._issuer = None

        # 底层 VCMI 连接 (复用)
        self._vcmi = VCMITCPConnection(config.host, config.port)
        self._vcmi.heartbeat_interval = config.heartbeat_interval

    # ------------------------------------------------------------------
    # 连接/断开
    # ------------------------------------------------------------------

    def connect(self) -> bool:
        """
        完整连接流程: TCP → 认证握手 → 就绪
        返回 True=就绪, 抛 RemoteConnectionError 失败
        """
        for attempt in range(1, self.cfg.max_retries + 1):
            try:
                self._do_connect()
                return True
            except (socket.timeout, ConnectionRefusedError, OSError) as e:
                if attempt == self.cfg.max_retries:
                    raise RemoteConnectionError(
                        f"连接失败 (attempt {attempt}/{self.cfg.max_retries}): {e}"
                    ) from e
                wait = self.cfg.retry_backoff * (2 ** (attempt - 1))
                time.sleep(wait)

    def _do_connect(self):
        # 复用 VCMITCPConnection.connect() 完成 TCP 建立
        ok = self._vcmi.connect()
        if not ok:
            raise RemoteConnectionError("TCP 连接失败")
        self._sock = self._vcmi.sock

        # 认证
        if self.cfg.auth_enabled:
            self._auth_handshake()

        self._connected = True

    def _auth_handshake(self):
        """
        认证握手协议:
          client → server: [4B len][AuthToken JSON]
          server → client: [1B] 0x01=OK / 0x00=FAIL
        """
        token = self._issuer.issue()
        frame = token.to_bytes_network()
        self._sock.sendall(frame)

        # 读 1 字节 ACK
        ack = self._recv_exact(1)
        if ack != b'\x01':
            self.disconnect()
            raise AuthFailedError(f"认证被拒绝 (ACK={ack[0] if ack else 'EOF'})")
        self._authenticated = True

    def disconnect(self):
        with self._lock:
            self._connected = False
            self._authenticated = False
            try:
                if self._sock:
                    self._sock.close()
            except Exception:
                pass
            self._sock = None

    @property
    def connected(self) -> bool:
        return self._connected and self._sock is not None and self._sock._closed == False

    @property
    def authenticated(self) -> bool:
        return self._authenticated

    # ------------------------------------------------------------------
    # 游戏帧收发 (透传到 VCMITCPConnection 的协议)
    # ------------------------------------------------------------------

    def send_frame(self, data: bytes):
        """发送一个 4B+payload 帧 (游戏包)"""
        if not self.connected:
            raise RemoteConnectionError("连接不可用")
        self._vcmi.send_frame(data)

    def recv_frame(self, timeout: float = 5.0) -> bytes:
        """接收一个 4B+payload 帧 (游戏包)"""
        if not self.connected:
            raise RemoteConnectionError("连接不可用")
        return self._vcmi.recv_frame(timeout)

    # ------------------------------------------------------------------
    # 内部工具
    # ------------------------------------------------------------------

    def _recv_exact(self, n: int, timeout: Optional[float] = None) -> bytes:
        """精确读 n 字节"""
        buf = b''
        remaining = n
        last = time.time()
        while remaining > 0:
            chunk = self._sock.recv(remaining)
            if not chunk:
                raise RemoteConnectionError(f"连接断开 (已读 {n - remaining}/{n})")
            buf += chunk
            remaining -= len(chunk)
            if time.time() - last > (timeout or self.cfg.auth_timeout):
                raise RemoteConnectionError(f"读超时 ({n}B)")
        return buf

    def get_stats(self) -> dict:
        return {
            'host': self.cfg.host,
            'port': self.cfg.port,
            'connected': self.connected,
            'authenticated': self.authenticated,
            'auth_enabled': self.cfg.auth_enabled,
            'client_id': self.cfg.client_id,
        }
