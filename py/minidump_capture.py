#!/usr/bin/env python3
"""ctypes MiniDumpWriteDump 抓进程 dump (Normal+ThreadInfo, 含栈)
用法: python minidump_capture.py <pid> <out.dmp>
"""
import ctypes, sys, os

pid = int(sys.argv[1])
out = sys.argv[2]

dbghelp = ctypes.WinDLL("dbghelp.dll")
kernel32 = ctypes.WinDLL("kernel32.dll")

PROCESS_ALL_ACCESS = 0x1F0FFF
h = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
if not h:
    print("OpenProcess fail", ctypes.GetLastError()); sys.exit(1)

hf = ctypes.windll.kernel32.CreateFileW(out, 0x40000000, 0, None, 2, 0x80, None)
if hf == -1 or hf == 0xFFFFFFFFFFFFFFFF:
    print("CreateFile fail", ctypes.GetLastError()); sys.exit(1)

class EXCEP_INFO(ctypes.Structure):
    _fields_ = [("ThreadId", ctypes.c_uint32), ("__alignment", ctypes.c_uint32 * 2)]

# MiniDumpNormal(0) | MiniDumpWithThreadInfo(0x1000) | MiniDumpIgnoreInaccessibleMemory(0x20000)
flags = 0x0 | 0x1000 | 0x20000
ok = dbghelp.MiniDumpWriteDump(
    ctypes.c_void_p(h), ctypes.c_uint32(pid), ctypes.c_void_p(hf),
    ctypes.c_int(flags), None, None, None)
err = ctypes.GetLastError()
ctypes.windll.kernel32.CloseHandle(hf)
ctypes.windll.kernel32.CloseHandle(h)
print("dump ok" if ok else f"dump fail err={err}", os.path.getsize(out) if os.path.exists(out) else 0)
