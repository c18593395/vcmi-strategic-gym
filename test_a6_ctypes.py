"""
Phase A6.2 验证: ctypes 直读 g_strategic_state
测试 strategic_reader.py 能正确加载 libmlclient.so 并读取状态
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from strategic_reader import StrategicReader

# 测试1: 加载库
print("=== Test 1: Load libmlclient.so ===")
lib_path = os.path.join(os.path.dirname(__file__), "vcmi/rel/bin/libmlclient.so")
print(f"Library path: {lib_path}")
print(f"Exists: {os.path.exists(lib_path)}")

try:
    reader = StrategicReader(lib_path)
    print(f"g_strategic_state pointer: {reader._ptr.value:#x}")
except Exception as e:
    print(f"ERROR loading: {e}")
    sys.exit(1)

# 测试2: 读取状态（此时VCMI未运行，指针应该为空或零初始化）
print("\n=== Test 2: Read state (VCMI not running) ===")
state = reader.read()
if state is None:
    print("state is None (expected — VCMI not running, pointer is null)")
else:
    print(f"state: day={state['day']}, players={len(state['players'])}")

print("\n=== A6.2 ctypes load test: PASS ===")
print("(Full validation requires VCMI game running)")
