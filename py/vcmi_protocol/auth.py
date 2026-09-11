"""
P8-D 跨机器部署 — 认证层
设计目标: 轻量 HMAC-SHA256 Token 方案，防未授权 AI 客户端接入 VCMI server。

方案:
  1. 双方持有共享密钥 (HSK, 32B)，部署前预交换 (密钥管理器/密钥文件)
  2. 每次连接时客户端生成: token = HMAC-SHA256(HSK, client_id + timestamp + nonce)
  3. Server 端验证 token 有效期 (±5 分钟时间窗) 和 nonce 去重
  4. 传输层默认走 TCP plaintext (内网场景)；公网可选 TLS 封装 (预留接口)
"""
from __future__ import annotations
import hmac
import hashlib
import time
import struct
import json
import base64
import secrets
from dataclasses import dataclass, field
from typing import Optional, Tuple

# ---------------------------------------------------------------------------
# 密钥管理
# ---------------------------------------------------------------------------

class SharedKeyManager:
    """共享密钥管理器 — 生成/加载/校验 HSK"""

    KEY_LEN = 32  # 32 bytes = 256 bits

    @classmethod
    def generate(cls) -> bytes:
        """生成新的 HSK (随机 32 字节)"""
        return secrets.token_bytes(cls.KEY_LEN)

    @classmethod
    def to_base64(cls, key: bytes) -> str:
        return base64.b64encode(key).decode()

    @classmethod
    def from_base64(cls, b64_str: str) -> bytes:
        return base64.b64decode(b64_str)

    @classmethod
    def validate(cls, key: bytes) -> bool:
        return len(key) == cls.KEY_LEN

    @classmethod
    def save_to_file(cls, key: bytes, path: str):
        """密钥落盘 (权限 0o600)"""
        import os
        with open(path, 'wb') as f:
            f.write(key)
        os.chmod(path, 0o600)

    @classmethod
    def load_from_file(cls, path: str) -> bytes:
        with open(path, 'rb') as f:
            return f.read()


# ---------------------------------------------------------------------------
# Token 数据结构
# ---------------------------------------------------------------------------

@dataclass
class AuthToken:
    """连接认证 Token"""
    client_id: str
    timestamp: int
    nonce: str
    signature: str  # base64 HMAC-SHA256

    def to_bytes(self) -> bytes:
        """序列化为网络格式:
        [1B magic 'T'] [4B len] [payload: client_id + ts + nonce + sig]
        简化: 直接 JSON + base64
        """
        payload = json.dumps({
            "client_id": self.client_id,
            "ts": self.timestamp,
            "nonce": self.nonce,
            "sig": self.signature,
        }, separators=(',', ':'))
        raw = payload.encode()
        # 网络帧: magic(1) + len(4) + raw
        return b'T' + struct.pack('<I', len(raw)) + raw

    @classmethod
    def from_bytes(cls, data: bytes) -> Optional[AuthToken]:
        if len(data) < 5 or data[0] != ord('T'):
            return None
        length = struct.unpack('<I', data[1:5])[0]
        if len(data) < 5 + length:
            return None
        try:
            obj = json.loads(data[5:5 + length].decode())
            return cls(
                client_id=obj["client_id"],
                timestamp=int(obj["ts"]),
                nonce=obj["nonce"],
                signature=obj["sig"],
            )
        except (KeyError, json.JSONDecodeError, ValueError):
            return None

    def to_bytes_network(self) -> bytes:
        """带网络帧头 (4B length prefix) 的完整字节"""
        payload = json.dumps({
            "client_id": self.client_id,
            "ts": self.timestamp,
            "nonce": self.nonce,
            "sig": self.signature,
        }, separators=(',', ':')).encode()
        return struct.pack('<I', len(payload)) + payload


# ---------------------------------------------------------------------------
# Token 签发与验证
# ---------------------------------------------------------------------------

def _hmac(key: bytes, client_id: str, ts: int, nonce: str) -> bytes:
    """HMAC-SHA256(key, client_id | timestamp | nonce)"""
    msg = f"{client_id}|{ts}|{nonce}".encode()
    return hmac.new(key, msg, hashlib.sha256).digest()


class TokenIssuer:
    """客户端侧 — 签发 Token"""

    def __init__(self, key: bytes, client_id: str = "ai-client-001"):
        if not SharedKeyManager.validate(key):
            raise ValueError(f"HSK length must be {SharedKeyManager.KEY_LEN}")
        self._key = key
        self._client_id = client_id

    def issue(self, nonce: Optional[str] = None) -> AuthToken:
        if nonce is None:
            nonce = secrets.token_hex(8)
        ts = int(time.time())
        sig = base64.b64encode(
            _hmac(self._key, self._client_id, ts, nonce)
        ).decode()
        return AuthToken(
            client_id=self._client_id,
            timestamp=ts,
            nonce=nonce,
            signature=sig,
        )


class TokenVerifier:
    """Server 侧 — 验证 Token"""

    TIME_WINDOW = 300  # ±5 分钟
    _seen_nonces: dict[str, int] = {}  # nonce → expiry_ts

    def __init__(self, key: bytes):
        if not SharedKeyManager.validate(key):
            raise ValueError(f"HSK length must be {SharedKeyManager.KEY_LEN}")
        self._key = key

    def verify(self, token: AuthToken, now: Optional[int] = None) -> Tuple[bool, str]:
        """
        返回 (ok, reason)
        验证项:
          1. timestamp 在时间窗内
          2. HMAC 签名匹配
          3. nonce 未重放
        """
        if now is None:
            now = int(time.time())

        # 1. 时间窗
        if abs(now - token.timestamp) > self.TIME_WINDOW:
            return False, f"timestamp {token.timestamp} outside ±{self.TIME_WINDOW}s window"

        # 2. 签名
        expected = base64.b64encode(
            _hmac(self._key, token.client_id, token.timestamp, token.nonce)
        ).decode()
        if not hmac.compare_digest(token.signature, expected):
            return False, "signature mismatch"

        # 3. nonce 去重 (简单内存版, 生产用 Redis)
        expiry = now + self.TIME_WINDOW
        old = self._seen_nonces.get(token.nonce)
        if old is not None and old > now:
            return False, f"nonce {token.nonce} already used (replay)"
        self._seen_nonces[token.nonce] = expiry

        # 清理过期 nonce (避免内存泄漏)
        to_del = [k for k, v in self._seen_nonces.items() if v <= now]
        for k in to_del:
            del self._seen_nonces[k]

        return True, "ok"
