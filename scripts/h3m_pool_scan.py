#!/usr/bin/env python3
"""H3M 官方图池快扫 (2026-08-29, P10-A 选图用)
只解析 header 前几个字段 (version / size / has_underground), 输出 CSV。
header 布局 (VCMI MapFormatH3M::readHeader):
  u32 version | u8 are_any_players | u32 map_size | u8 has_underground | sstr name ...
用法: python h3m_pool_scan.py [maps_dir]
"""
import gzip, struct, sys, os, glob, json

def read_header(path):
    with open(path, 'rb') as f:
        raw = gzip.decompress(f.read())
    p = 0
    ver = struct.unpack_from('<I', raw, p)[0]; p += 4
    p += 1                                        # are_any_players
    size = struct.unpack_from('<I', raw, p)[0]; p += 4
    und = raw[p]; p += 1                          # has_underground
    # name / description (u32 len + bytes)
    for _ in range(2):
        l = struct.unpack_from('<I', raw, p)[0]; p += 4 + l
    diff = raw[p]; p += 1
    return {'version': ver, 'size': size, 'underground': und, 'difficulty': diff}

def main():
    d = sys.argv[1] if len(sys.argv) > 1 else 'vcmi/data/Maps'
    rows = []
    for fp in glob.glob(os.path.join(d, '*.h3m')):
        try:
            h = read_header(fp)
            h['name'] = os.path.splitext(os.path.basename(fp))[0]
            h['file'] = fp
            rows.append(h)
        except Exception as e:
            print(f"# FAIL {os.path.basename(fp)}: {e}", file=sys.stderr)
    rows.sort(key=lambda r: (r['underground'], r['size']))
    print("size,underground,version,difficulty,name")
    for r in rows:
        print(f"{r['size']},{r['underground']},{r['version']},{r['difficulty']},{r['name']}")
    ok = [r for r in rows if r['underground'] == 0]
    print(f"\n# 总计 {len(rows)} 张, 无地下层 {len(ok)} 张", file=sys.stderr)
    from collections import Counter
    print("# 尺寸分布(无地下): " + str(sorted(Counter(r['size'] for r in ok).items())), file=sys.stderr)

if __name__ == '__main__':
    main()
