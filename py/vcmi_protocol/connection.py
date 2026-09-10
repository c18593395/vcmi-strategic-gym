"""
T13.3 — TCP 连接层
管理 VCMI 服务器的 TCP 连接: 帧收发、心跳、重连
"""
import socket
import struct
import time
import threading
from typing import Optional, Callable

HEARTBEAT_INTERVAL = 10.0  # 秒
SEND_TIMEOUT = 5.0
RECV_TIMEOUT = 1.0
MAX_PACKET_SIZE = 64 * 1024 * 1024  # 64MB


class VCMITCPConnection:
    """
    VCMI TCP 连接管理器
    
    帧格式: [uint32 header (little-endian)] [payload]
    - header = payload 长度
    - header = 0 → heartbeat (空包, 每 10 秒)
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 5555):
        self.host = host
        self.port = port
        self.sock: Optional[socket.socket] = None
        self._connected = False
        self._lock = threading.Lock()
        self._recv_buffer = bytearray()
        self.on_heartbeat: Optional[Callable] = None

    def connect(self) -> bool:
        """连接到 VCMI 服务器"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(SEND_TIMEOUT)
            self.sock.setsockopt(socket.IPPROTO_TCP, socket.IP_TOS, 0x18)  # no_delay
            self.sock.connect((self.host, self.port))
            self._connected = True
            self._recv_buffer = bytearray()
            print(f"[CONN] 已连接 {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"[CONN] 连接失败: {e}")
            self._connected = False
            return False

    def disconnect(self):
        """断开连接"""
        self._connected = False
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
            self.sock = None

    @property
    def connected(self) -> bool:
        return self._connected and self.sock is not None

    def send_frame(self, payload: bytes) -> bool:
        """
        发送一个帧: [uint32 length] [payload]
        """
        with self._lock:
            if not self.connected:
                print("[CONN] 未连接, 无法发送")
                return False
            try:
                header = struct.pack('<I', len(payload))
                self.sock.sendall(header + payload)
                return True
            except Exception as e:
                print(f"[CONN] 发送失败: {e}")
                return False

    def send_heartbeat(self) -> bool:
        """发送心跳 (空包)"""
        return self.send_frame(b'')

    def recv_frame(self) -> Optional[bytes]:
        """
        接收一个帧, 返回 payload (不含 header)
        返回 None 如果超时或连接断开
        """
        if not self.connected:
            return None

        try:
            self.sock.settimeout(RECV_TIMEOUT)
            header_data = self._recv_exact(4)
            if header_data is None:
                return None

            length = struct.unpack('<I', header_data)[0]

            if length == 0:
                # heartbeat
                if self.on_heartbeat:
                    self.on_heartbeat()
                return b''  # empty payload

            if length > MAX_PACKET_SIZE:
                print(f"[CONN] 包过大: {length} bytes")
                return None

            payload = self._recv_exact(length)
            return payload
        except socket.timeout:
            return None
        except Exception as e:
            print(f"[CONN] 接收失败: {e}")
            return None

    def _recv_exact(self, n: int) -> Optional[bytes]:
        """从缓冲区精确接收 n 字节"""
        while len(self._recv_buffer) < n:
            try:
                chunk = self.sock.recv(4096)
                if not chunk:
                    print("[CONN] 连接已关闭")
                    self._connected = False
                    return None
                self._recv_buffer.extend(chunk)
            except socket.timeout:
                return None
            except Exception:
                return None

        data = bytes(self._recv_buffer[:n])
        del self._recv_buffer[:n]
        return data

    def send_pack(self, pack) -> bool:
        """发送一个网络包 (自动序列化)"""
        if hasattr(pack, 'to_bytes'):
            data = pack.to_bytes()
        elif hasattr(pack, 'serialize'):
            from .serialization import BinarySerializer
            ser = BinarySerializer()
            pack.serialize_full(ser)
            data = ser.get_bytes()
        else:
            data = pack  # already bytes
        return self.send_frame(data)
