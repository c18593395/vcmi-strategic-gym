# -*- coding: utf-8 -*-
# ctypes MiniDumpWriteDump 抓 full dump
# 用法: python take_dump.py <pid> <out.dmp>
import ctypes, sys
from ctypes import wintypes

pid = int(sys.argv[1])
out = sys.argv[2]

PROCESS_ALL_ACCESS = 0x1F0FFF
MiniDumpWithFullMemory = 0x2
MiniDumpWithHandleData = 0x4
MiniDumpWithUnloadedModules = 0x20
MiniDumpWithFullMemoryInfo = 0x800

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
dbh = ctypes.WinDLL("dbghelp", use_last_error=True)

hProc = k32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
if not hProc:
    print("OpenProcess failed err=%d" % ctypes.get_last_error())
    sys.exit(1)

hFile = k32.CreateFileW(out, 0x40000000, 0, None, 2, 0x80, None)  # GENERIC_WRITE, CREATE_ALWAYS
if hFile == -1 or hFile == 0xFFFFFFFFFFFFFFFF:
    print("CreateFile failed err=%d" % ctypes.get_last_error())
    sys.exit(1)

class _EXCEP(ctypes.Structure):
    _fields_ = [("_", ctypes.c_byte * 4096)]
class _USER(ctypes.Structure):
    _fields_ = [("_", ctypes.c_byte * 4096)]

class MINIDUMP_EXCEPTION_INFORMATION(ctypes.Structure):
    _fields_ = [("ThreadId", wintypes.DWORD),
                ("ExceptionPointers", ctypes.c_void_p),
                ("ClientPointers", wintypes.BOOL)]

exc = MINIDUMP_EXCEPTION_INFORMATION()
exc.ThreadId = 0
exc.ExceptionPointers = None
exc.ClientPointers = False

ok = dbh.MiniDumpWriteDump(
    wintypes.HANDLE(hProc), wintypes.DWORD(pid), wintypes.HANDLE(hFile),
    wintypes.DWORD(MiniDumpWithFullMemory | MiniDumpWithHandleData | MiniDumpWithFullMemoryInfo),
    ctypes.byref(exc) if False else None, None, None)
err = ctypes.get_last_error()
print("MiniDumpWriteDump ok=%s err=%d" % (bool(ok), err))
k32.CloseHandle(hFile)
k32.CloseHandle(hProc)
import os
if os.path.exists(out):
    print("dump size=%d" % os.path.getsize(out))
