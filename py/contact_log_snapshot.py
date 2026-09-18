#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""贴脸局日志快照器 (09-18 B+C 验证窗): 主日志出现 BHERO_CONTACT 时, 立即复制当前最新
/tmp/hermes_ep_*.log 为 /tmp/hermes_snap_<时刻>.log, 供单局归因 (主日志交织无法归属事件行)。
用法: nohup venv-python py/contact_log_snapshot.py >/tmp/snapshot.log 2>&1 &"""
import glob
import shutil
import time

LOG = "/mnt/d/Bigdata/hero3_fresh/train_loop.log"
seen = 0
_ring = 0
last_ring = 0.0
while True:
    try:
        # 环形快照: 每 240s 保留最新 hermes log 到 snap_ring_0..4 (5 槽 ≈ 20 分钟覆盖, 一局 8-16 分钟)
        now = time.time()
        if now - last_ring >= 240:
            last_ring = now
            cands = sorted(glob.glob("/tmp/hermes_ep_*.log"), key=lambda p: -__import__("os").path.getmtime(p))
            if cands and __import__("os").path.getsize(cands[0]) > 1000:
                shutil.copy(cands[0], f"/tmp/hermes_snap_ring_{_ring % 5}.log")
                _ring += 1
        with open(LOG, errors="replace") as f:
            f.seek(seen)
            new = f.read()
            seen = f.tell()
        if "[BHERO_CONTACT]" in new:
            ts = time.strftime("%H%M%S")
            cands = sorted(glob.glob("/tmp/hermes_ep_*.log"), key=lambda p: -__import__("os").path.getmtime(p))
            if cands:
                dst = f"/tmp/hermes_snap_{ts}.log"
                try:
                    shutil.copy(cands[0], dst)
                    with open("/tmp/snapshot.log", "a") as sf:
                        sf.write(f"{ts} snapshotted {cands[0]} -> {dst}\n")
                except Exception as e:
                    with open("/tmp/snapshot.log", "a") as sf:
                        sf.write(f"{ts} FAIL {e}\n")
    except Exception:
        pass
    time.sleep(5)
