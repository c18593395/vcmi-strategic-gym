# -*- coding: utf-8 -*-
"""读取 VCMI Crashhandler 对话框的所有控件文本 (09-10 gui4 启动即崩诊断)"""
import ctypes
from ctypes import wintypes
import sys

user32 = ctypes.windll.user32
EnumWindows = user32.EnumWindows
EnumChildWindows = user32.EnumChildWindows
GetWindowTextW = user32.GetWindowTextW
GetClassNameW = user32.GetClassNameW
GetWindowThreadProcessId = user32.GetWindowThreadProcessId

buf = ctypes.create_unicode_buffer(512)

def get_text(h):
    n = GetWindowTextW(h, buf, 512)
    return buf.value if n else ''

def get_cls(h):
    n = GetClassNameW(h, buf, 512)
    return buf.value if n else ''

target_pid = int(sys.argv[1]) if len(sys.argv) > 1 else 26352

results = []

@ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
def top_cb(h, l):
    pid = wintypes.DWORD()
    GetWindowThreadProcessId(h, ctypes.byref(pid))
    if pid.value == target_pid:
        results.append(('TOP', h, get_cls(h), get_text(h)))
    return True

@ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
def child_cb(h, l):
    pid = wintypes.DWORD()
    GetWindowThreadProcessId(h, ctypes.byref(pid))
    if pid.value == target_pid:
        results.append(('CHILD', h, get_cls(h), get_text(h)))
    return True

EnumWindows(top_cb, 0)
for tag, h, cls, txt in [r for r in results if r[0] == 'TOP']:
    print(f'[{tag}] hwnd=0x{h:X} class={cls} text={txt!r}')
    EnumChildWindows(h, child_cb, 0)

for tag, h, cls, txt in results:
    if tag == 'CHILD':
        print(f'  [{tag}] hwnd=0x{h:X} class={cls} text={txt!r}')
