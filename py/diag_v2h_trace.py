#!/usr/bin/env python3
"""逐对象跟踪 h3m 对象流 pos, 定位 vmap2h3m 写出与 reader 期望的漂移"""
import sys

sys.path.insert(0, '/mnt/d/Bigdata/hero3_fresh/scripts')
import h3m_tool  # noqa: E402
import gzip, struct  # noqa: E402

for path in sys.argv[1:]:
    print(f"== {path}")
    with open(path, 'rb') as fh:
        raw = gzip.decompress(fh.read())
    r = h3m_tool.R(raw)
    ver = r.u32()
    f = h3m_tool._features(ver)
    info = h3m_tool.parse_header(path)
    r.pos = info['terrain_end']
    def_count = r.u32()
    tstart = r.pos
    for _ in range(def_count):
        ln = struct.unpack_from('<I', raw, r.pos)[0]
        r.skip(4 + ln + 12 + 4 + 8 + 2 + 16)
    tend = r.pos
    print(f"   templates: n={def_count} span={tend-tstart}")
    obj_count = r.u32()
    print(f"   obj_count={obj_count} start@{r.pos}")
    prev_end = None
    for i in range(obj_count):
        p0 = r.pos
        x, y, z = r.int3()
        def_idx = r.u32()
        r.skip(5)
        t = None
        # 找模板
        # (从 tstart 重新解析拿 id/subid)
        q = tstart
        for _ in range(def_idx + 1):
            ln = struct.unpack_from('<I', raw, q)[0]
            anim = raw[q+4:q+4+ln].decode('latin1')
            oid = struct.unpack_from('<I', raw, q + 4 + ln + 12 + 4)[0]
            subid = struct.unpack_from('<I', raw, q + 4 + ln + 12 + 4 + 4)[0]
            q += 4 + ln + 12 + 4 + 8 + 2 + 16
        name = h3m_tool.OBJ_NAMES.get(oid, f'OBJ_{oid}')
        # 手动分派读数据 (镜像 h3m_tool)
        if oid in (62, 70):
            h3m_tool._read_hero(r, f, (x, y, z))
        elif oid in (98, 77):
            h3m_tool._read_town(r, f, (x, y, z), oid, subid)
        elif oid in (79, 76):
            h3m_tool._read_message_and_guards(r, f)
            r.u32(); r.skip(4)
        elif oid == 53:
            if subid < 7:
                r.u32()
            else:
                h3m_tool._read_bitmask(r, f, 'resources')
        elif oid in (54, 72, 73, 74, 75, 162, 163):
            r.u32(); r.u16(); r.i8()
            if h3m_tool._bool(r):
                r.lstr(); r.skip(28); h3m_tool._read_artifact(r, f)
            h3m_tool._bool(r); h3m_tool._bool(r)
            r.skip(2)
        else:
            print(f"   UNHANDLED {name}")
            break
        gap_note = ''
        if prev_end is not None and p0 != prev_end:
            gap_note = f"  <<< GAP {p0 - prev_end:+d}B"
        print(f"   #{i} {name:15s} sub={subid:3d} head@{p0} data_end@{r.pos}{gap_note}")
        prev_end = r.pos
    print(f"   stream_end@{r.pos} raw_len={len(raw)} tail={raw[r.pos:r.pos+16].hex(' ')}")
