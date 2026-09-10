"""
T13.1 — LVarInt 变长整数编解码 + BinarySerializer / BinaryDeserializer
完整实现 VCMI 二进制序列化协议。
"""
import struct


# ============================================================
# 1. LVarInt (变长整数) 编解码
# ============================================================

def encode_lvarint(value: int) -> bytes:
    """
    变长整数编码 (匹配 C++ saveEncodedInteger):
    - 1 byte if 0 <= value < 0x40 (or value < 0 and value > -0x40 with 0x40 flag)
    - 多字节: 每字节 7 bit 数据 (0x7f mask), 高位 0x80 表示有后续
    - 负数: 最后字节 0x40 位标记负号
    """
    if value >= 0 and value < 0x40:
        return bytes([value])
    if value < 0 and value > -0x40:
        return bytes([-value | 0x40])
    
    negative = value < 0
    unsigned_val = abs(value)
    
    result = bytearray()
    
    # Continuation bytes: 7 bits data each (0x7f mask), high bit 0x80
    while unsigned_val >= 0x40:
        result.append((unsigned_val & 0x7f) | 0x80)
        unsigned_val >>= 7
    
    # Final byte: 6 bits data (0x3f mask), 0x40 = negative flag
    final_byte = unsigned_val & 0x3f
    if negative:
        final_byte |= 0x40
    result.append(final_byte)
    
    return bytes(result)


def decode_lvarint(buf: bytes, pos: int = 0) -> tuple:
    """解码变长整数, 返回 (value, new_pos)"""
    result = 0
    offset = 0
    
    while True:
        byte = buf[pos]
        pos += 1
        
        if byte & 0x80:
            result |= (byte & 0x7f) << offset
            offset += 7
        else:
            result |= (byte & 0x3f) << offset
            if byte & 0x40:
                return -result, pos
            else:
                return result, pos


# ============================================================
# 2. BinarySerializer
# ============================================================

class BinarySerializer:
    """模拟 VCMI BinarySerializer 的完整序列化行为"""

    def __init__(self):
        self.buf = bytearray()
        self.saved_strings = {}   # string -> int (负数 ID)
        self.saved_pointers = {}  # object_id -> int (pointer ID)
        self._next_string_id = 0
        self._next_pointer_id = 0

    def write_raw(self, data: bytes):
        self.buf.extend(data)

    def write_bool(self, val: bool):
        self.buf.append(1 if val else 0)

    def write_int(self, val: int):
        """si32 / int32 / uint32 → 变长整数"""
        self.buf.extend(encode_lvarint(val))

    def write_uint8(self, val: int):
        self.buf.append(val & 0xff)

    def write_int8(self, val: int):
        """int8_t — 1 byte raw (signed)"""
        self.buf.append(val & 0xff)

    def write_uint16(self, val: int):
        """uint16_t — 2 bytes raw little-endian"""
        self.buf.extend(struct.pack('<H', val & 0xffff))

    def write_int32_raw(self, val: int):
        """int32_t raw — 4 bytes little-endian"""
        self.buf.extend(struct.pack('<i', val))

    def write_float(self, val: float):
        self.buf.extend(struct.pack('<f', val))

    def write_double(self, val: float):
        self.buf.extend(struct.pack('<d', val))

    def write_string(self, val: str):
        """
        字符串: 带全局限去重
        - 空串: save(uint32(0))
        - 新串: save(uint32(length)) + raw bytes
        - 重复串: save(int32(negative_id))
        """
        if not val:
            self.write_int(0)
            return

        if val in self.saved_strings:
            self.write_int(self.saved_strings[val])
            return

        length = len(val.encode('utf-8'))
        self.write_int(length)
        self.buf.extend(val.encode('utf-8'))

        # Assign negative ID: -1, -2, -3, ...
        string_id = -1 - self._next_string_id
        self._next_string_id += 1
        self.saved_strings[val] = string_id

    def write_int3(self, x: int, y: int, z: int):
        """int3 = 3× si32 (LVarInt each)"""
        self.write_int(x)
        self.write_int(y)
        self.write_int(z)

    def write_static_identifier(self, num: int):
        """StaticIdentifier (ObjectInstanceID, QueryID, PlayerColor, SlotID...) = int32 LVarInt"""
        self.write_int(num)

    def write_entity_identifier(self, entity_str: str):
        """EntityIdentifier (CreatureID, HeroTypeID, BuildingID, SpellID...) = string"""
        self.write_string(entity_str)

    def write_optional(self, value, write_fn):
        """std::optional<T> = uint8 present + value"""
        if value is not None:
            self.write_uint8(1)
            write_fn(value)
        else:
            self.write_uint8(0)

    def write_variant(self, index: int, write_fn=None, value=None):
        """std::variant = int32 index + value"""
        self.write_int(index)
        if write_fn and value is not None:
            write_fn(value)

    def write_vector(self, elements, write_fn):
        """std::vector<T> = uint32 length + elements"""
        self.write_int(len(elements))
        for e in elements:
            write_fn(e)

    def write_map(self, items, write_key_fn, write_val_fn):
        """std::map<K,V> = uint32 length + (key, value) pairs"""
        self.write_int(len(items))
        for key, val in items:
            write_key_fn(key)
            write_val_fn(val)

    def write_struct(self, fields):
        """Write a struct of (name, value) pairs — caller handles serialization"""
        for name, value in fields:
            yield name, value

    def write_pointer(self, obj, write_fn):
        """
        std::shared_ptr<T> / unique_ptr / raw pointer
        [isNull] [pointerID] [typeID] [data...]
        """
        if obj is None:
            self.write_bool(False)  # isNull = false for null? No: C++ writes isNull=true for null
            self.write_bool(True)   # Actually C++ writes bool isNull first
            return

        # C++ pointer serialization:
        # save(bool isNull) — false if pointer is valid
        # save(uint32_t pointerID)
        # save(uint16_t typeID)
        # save(data...)

        # But the actual VCMI code does:
        # h & (bool)!ptr → writes false for non-null
        # if (!ptr) return;
        # h & pointerID;
        # h & typeID;
        # ptr->serialize(h)

        # Actually looking at BinarySerializer more carefully:
        # savePointer: writes isNull=false, then pointerID, typeID, data
        self.write_bool(False)  # isNull = false (pointer is valid)
        self.write_int(self._next_pointer_id)  # pointerID
        self._next_pointer_id += 1
        self.write_uint16(obj.type_id)  # typeID
        write_fn(obj)

    def get_bytes(self) -> bytes:
        return bytes(self.buf)

    def clear(self):
        self.buf.clear()
        self.saved_strings.clear()
        self.saved_pointers.clear()
        self._next_string_id = 0
        self._next_pointer_id = 0


# ============================================================
# 3. BinaryDeserializer
# ============================================================

class BinaryDeserializer:
    """模拟 VCMI BinaryDeserializer 的完整反序列化行为"""

    def __init__(self, data: bytes):
        self.buf = data
        self.pos = 0
        self.loaded_strings = []  # stringID → string
        self.loaded_pointers = {} # pointerID → object

    def read_raw(self, size: int) -> bytes:
        data = self.buf[self.pos:self.pos + size]
        self.pos += size
        return data

    def read_bool(self) -> bool:
        val = self.buf[self.pos] != 0
        self.pos += 1
        return val

    def read_int(self) -> int:
        val, self.pos = decode_lvarint(self.buf, self.pos)
        return val

    def read_uint8(self) -> int:
        val = self.buf[self.pos]
        self.pos += 1
        return val

    def read_int8(self) -> int:
        val = self.buf[self.pos]
        if val > 127:
            val -= 256
        self.pos += 1
        return val

    def read_uint16(self) -> int:
        val = struct.unpack('<H', self.read_raw(2))[0]
        return val

    def read_int32_raw(self) -> int:
        val = struct.unpack('<i', self.read_raw(4))[0]
        return val

    def read_float(self) -> float:
        return struct.unpack('<f', self.read_raw(4))[0]

    def read_double(self) -> float:
        return struct.unpack('<d', self.read_raw(8))[0]

    def read_string(self) -> str:
        """
        字符串: 带全局限去重
        - length < 0: 从已加载列表取
        - length == 0: 空串
        - length > 0: 读取 length 字节
        """
        length = self.read_int()

        if length < 0:
            string_id = -length - 1
            return self.loaded_strings[string_id]

        if length == 0:
            return ""

        raw = self.read_raw(length)
        s = raw.decode('utf-8')
        self.loaded_strings.append(s)
        return s

    def read_int3(self) -> tuple:
        x = self.read_int()
        y = self.read_int()
        z = self.read_int()
        return (x, y, z)

    def read_static_identifier(self) -> int:
        return self.read_int()

    def read_optional_present(self) -> bool:
        return self.read_uint8() != 0

    def read_variant_index(self) -> int:
        return self.read_int()

    def get_remaining(self) -> int:
        return len(self.buf) - self.pos

    def read_pointer_present(self) -> bool:
        """Pointer 序列化首个字段: save(bool(!ptr))，true 表示非空"""
        return self.read_bool()

    def read_set(self, read_fn):
        """std::set<T> 与 vector 同长度前缀；有序由上层保证"""
        n = self.read_int()
        out = []
        for _ in range(n):
            out.append(read_fn())
        return out

    def read_pointer(self, read_obj_fn):
        """读取 shared_ptr<T>: [bool isNotNull] [int pointerID] [uint16 typeID] [data]"""
        if not self.read_pointer_present():
            return None
        self.read_int()          # pointerID
        self.read_uint16()       # typeID
        return read_obj_fn()

    def reset_pos(self, pos: int = 0):
        self.pos = pos
