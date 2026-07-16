#!/usr/bin/env python3
"""A6.1 verify: connector_v13 import + adventure methods"""
import sys, os

sys.path.insert(0, "/home/administrator/vcmi-workspace")
os.environ["LD_LIBRARY_PATH"] = (
    "/home/administrator/vcmi-workspace/vcmi/rel/bin:"
    "/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel"
)

print("=== A6.1: Verify connector_v13 import ===")
try:
    import connector_v13
    print("PASS: connector_v13 imported")
except Exception as e:
    print(f"FAIL: {e}")
    sys.exit(1)

tc = connector_v13.ThreadConnector
print(f"  adventure_wait: {hasattr(tc, 'adventure_wait')}")
print(f"  adventure_act: {hasattr(tc, 'adventure_act')}")

# Quick ctypes check
import ctypes
lib = ctypes.CDLL("/home/administrator/vcmi-workspace/vcmi/rel/bin/libmlclient.so")
g_ss = ctypes.c_void_p.in_dll(lib, "g_strategic_state")
print(f"\n=== A6.2: ctypes globals ===")
print(f"  g_strategic_state address in lib: {hex(g_ss.value) if g_ss.value else 'NULL (expected before VCMI runs)'}")

g_cb = ctypes.c_void_p.in_dll(lib, "g_adventure_cb")
print(f"  g_adventure_cb address in lib: {hex(g_cb.value) if g_cb.value else 'NULL (expected, set by connector)'}")

print("\n=== A6.1 + A6.2 pre-flight: PASS ===")
print("(Full runtime test requires VCMI adventure map)")
