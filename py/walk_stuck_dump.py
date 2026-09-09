# -*- coding: utf-8 -*-
# 标准 Windows full minidump 线程栈扫描器 (x64)
# CONTEXT 偏移: Rsp=+0x98, Rip=+0xF8 (与 analyze_vcmi_dump.py 同口径)
# 用法: python walk_stuck_dump.py <dump.dmp> [--tid 13848]
import sys, struct
from minidump.minidumpfile import MinidumpFile

def main():
    path = sys.argv[1]
    want_tid = None
    if "--tid" in sys.argv:
        want_tid = int(sys.argv[sys.argv.index("--tid") + 1])

    mf = MinidumpFile.parse(path)
    f = open(path, "rb")
    reader = None

    # ---- 手动解析 Memory64ListStream (type=9) — minidump 库对 full dump 栈内存支持差 ----
    f.seek(0)
    hdr = f.read(32)
    num_streams, dir_rva = struct.unpack_from("<II", hdr, 8)
    mem64 = []  # (start, size, rva)
    for i in range(num_streams):
        f.seek(dir_rva + i * 12)
        st, sz, rva = struct.unpack("<III", f.read(12))
        if st == 9:  # Memory64ListStream
            f.seek(rva)
            n_ranges, base_rva = struct.unpack("<QQ", f.read(16))
            data_rva = base_rva
            for j in range(n_ranges):
                start, dsize = struct.unpack("<QQ", f.read(16))
                mem64.append((start, dsize, data_rva))
                data_rva += dsize
            break
    mem64.sort()
    print("mem64 ranges=%d total=%.1fMB" % (len(mem64), sum(s for _, s, _ in mem64) / 1048576.0))

    import bisect
    starts = [m[0] for m in mem64]

    def read_mem(addr, size):
        idx = bisect.bisect_right(starts, addr) - 1
        if idx < 0:
            return b""
        start, dsize, rva = mem64[idx]
        off = addr - start
        if off >= dsize:
            return b""
        n = min(size, dsize - off)
        f.seek(rva + off)
        return f.read(n)

    modules = []
    for m in mf.modules.modules:
        name = str(m.name).split("\\")[-1]
        modules.append((name, m.baseaddress, m.size))

    def sym(addr):
        for name, base, size in modules:
            if base <= addr < base + size:
                return "%s+0x%x" % (name, addr - base)
        return "0x%x" % addr

    threads = mf.threads.threads
    print("modules=%d threads=%d" % (len(modules), len(threads)))

    # 找最底层(栈低地址)的段用于直接读 — 用 memory segments
    for t in threads:
        tid = t.ThreadId
        if want_tid and tid != want_tid:
            continue
        lc = t.ThreadContext  # LOCATION_DESCRIPTOR(DataSize, Rva)
        f.seek(lc.Rva)
        ctx = f.read(lc.DataSize)
        if not ctx or len(ctx) < 0x100:
            print("TID=%d no context" % tid)
            continue
        rsp = struct.unpack_from("<Q", ctx, 0x98)[0]
        rip = struct.unpack_from("<Q", ctx, 0xF8)[0]
        line = ["TID=%d RIP=%s RSP=0x%x" % (tid, sym(rip), rsp)]

        # 栈内存: 从 Memory64List 段读 [rsp, rsp+32KB) 中已存在的部分
        try:
            data = read_mem(rsp, 0x8000)
        except Exception:
            data = b""
        if data:
            rets = []
            for off in range(0, min(len(data), 0x8000) - 8, 8):
                val = struct.unpack_from("<Q", data, off)[0]
                for name, base, size in modules:
                    if base <= val < base + size:
                        # 粗过滤: 代码内返回地址, 跳过纯数据; 保守只收 .text 通常在模块前部
                        if val - base < size:
                            rets.append("%s+0x%x" % (name, val - base))
                        break
                if len(rets) >= 40:
                    break
            if rets:
                line.append("STACK: " + " <- ".join(rets[:40]))
            else:
                line.append("STACK: (no module rets, %d bytes read)" % len(data))
        else:
            line.append("STACK: (unreadable)")
        print(" | ".join(line))

if __name__ == "__main__":
    main()
