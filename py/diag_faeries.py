#!/usr/bin/env python3
"""诊断 Faeries header.json 解析失败点"""
import zipfile

p = "/tmp/h3m_pipeline/faeries.raw.vmap"
z = zipfile.ZipFile(p)
raw = z.read("header.json").decode("utf-8")
print("总长:", len(raw))
print("=== char 7250-7550 ===")
print(repr(raw[7250:7550]))
print("=== line 345-352 ===")
lines = raw.split("\n")
for i in range(344, min(352, len(lines))):
    print(f"{i+1}: {lines[i][:120]}")
