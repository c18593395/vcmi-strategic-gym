# -*- coding: utf-8 -*-
"""Parse VCMI minidump: exception stream (code/address/thread) + module list + PE image base.
Usage: py parse_crash_dmp.py [dump_path]
"""
import struct, sys, os

DMP = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\Administrator\Documents\My Games\vcmi\logs\VCMI_client.exe_crashinfo.dmp"

with open(DMP, "rb") as f:
    data = f.read()

if data[:4] != b"MDMP":
    print("Not a minidump")
    sys.exit(1)

_, _, nstreams, dir_rva = struct.unpack_from("<IIII", data, 0)

streams = {}
for i in range(nstreams):
    st, size, rva = struct.unpack_from("<III", data, dir_rva + 12 * i)
    streams.setdefault(st, (size, rva))

# --- Exception stream (type 6) ---
exc = None
if 6 in streams:
    _, rva = streams[6]
    thread_id = struct.unpack_from("<I", data, rva)[0]
    code, flags, rec, addr = struct.unpack_from("<IIQQ", data, rva + 8)
    nparams = struct.unpack_from("<I", data, rva + 32)[0]
    params = struct.unpack_from("<15Q", data, rva + 40)
    print(f"[Exception] ThreadId={thread_id}")
    print(f"  Code=0x{code:08X}  Flags=0x{flags:08X}  Address=0x{addr:016X}")
    print(f"  NumberParameters={nparams}")
    for i in range(nparams):
        print(f"    param[{i}]=0x{params[i]:X}")
    exc = addr

# --- Module list (type 4) ---
target = None
if 4 in streams and exc:
    _, rva = streams[4]
    nmod = struct.unpack_from("<I", data, rva)[0]
    off = rva + 4
    for i in range(nmod):
        base, sizeofimg, cksum, tds, name_rva = struct.unpack_from("<QIIII", data, off)
        mlen = struct.unpack_from("<I", data, name_rva)[0]
        name = data[name_rva + 4 : name_rva + 4 + mlen].decode("utf-16-le", "replace")
        if base <= exc < base + sizeofimg:
            rva_off = exc - base
            print(f"[Module] {name}")
            print(f"  base=0x{base:X} size=0x{sizeofimg:X}  ExceptionRVA=0x{rva_off:X}")
            # PE ImageBase on disk -> addr2line address (handle ASLR)
            try:
                with open(name, "rb") as pe:
                    pe.seek(0x3C)
                    e_lfanew = struct.unpack("<I", pe.read(4))[0]
                    pe.seek(e_lfanew + 4 + 20)  # optional header start
                    opt_magic = struct.unpack("<H", pe.read(2))[0]
                    ib_off = e_lfanew + 4 + 20 + (24 if opt_magic == 0x20B else 28)
                    fmt = "<Q" if opt_magic == 0x20B else "<I"
                    pe.seek(ib_off)
                    image_base = struct.unpack(fmt, pe.read(8 if opt_magic == 0x20B else 4))[0]
                delta = image_base - base
                target = exc + delta
                print(f"  PE ImageBase=0x{image_base:X}  ASLR delta=0x{delta:X}")
                print(f"  addr2line address: 0x{target:X}")
            except OSError as e:
                print(f"  PE header read failed: {e}")
        off += 108  # sizeof(MINIDUMP_MODULE)

if not exc:
    print("No exception stream found")
