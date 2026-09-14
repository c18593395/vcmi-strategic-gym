#!/bin/bash
# 09-14 sync 脚本负向测试 (不污染真实源图)
set -u
cd /mnt/d/Bigdata/hero3_fresh
PY=/home/administrator/vcmi-workspace/venv/bin/python
MAP=T06_adventure_108X108_02_duel.vmap
DST=/home/administrator/vcmi-native/rel/bin/data/Maps/$MAP

echo "======== 测 A: 运行时副本被篡改 -> --check 必须检出 rc=1 ========"
cp "$DST" /tmp/A_good.vmap.bak
printf 'X' >> "$DST"                       # 模拟陈旧/损坏副本
$PY py/sync_maps_to_runtime.py --check "$MAP" > /tmp/A_check.log 2>&1
rc=$?
grep -E "不一致|FAIL" /tmp/A_check.log | head -3
echo "  --check rc=$rc (期望 1)"

echo "======== 测 A2: 正式 sync 修复 -> 恢复一致 ========"
$PY py/sync_maps_to_runtime.py "$MAP" > /tmp/A_sync.log 2>&1
grep -E "SYNC|OK|FAIL" /tmp/A_sync.log | head -4
$PY py/sync_maps_to_runtime.py --check "$MAP" >/dev/null 2>&1
echo "  修复后 --check rc=$? (期望 0)"
cmp -s /tmp/A_good.vmap.bak "$DST" && echo "  字节级还原一致" || echo "  注意: 与篡改前备份不同(应为原始干净版)"

echo "======== 测 B: 源侧坏图 (players=[] + orange owner) 必须被拒绝, 且不碰运行时 ========"
$PY - "$MAP" <<'EOF'
import json, sys, zipfile, importlib.util
spec = importlib.util.spec_from_file_location("syncer", "py/sync_maps_to_runtime.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
src = m.SRC_DIR / sys.argv[1]
# 在 /tmp 构造两张坏图喂 inspect_vmap, 不动真实源
def make_bad(path, mutate_header, mutate_objs=None):
    z = zipfile.ZipFile(src)
    names = z.namelist()
    data = {n: z.read(n) for n in names}; z.close()
    h = json.loads(data["header.json"]); mutate_header(h)
    data["header.json"] = json.dumps(h).encode()
    if mutate_objs:
        o = json.loads(data["objects.json"]); mutate_objs(o)
        data["objects.json"] = json.dumps(o).encode()
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zo:
        for n in names: zo.writestr(n, data[n])
# B1 players=[]
p1 = "/tmp/B_players_empty.vmap"
make_bad(p1, lambda h: h.__setitem__("players", []))
errs, warns, info = m.inspect_vmap(m.Path(p1), (None, None))
print("B1 players=[] ->", "拦截" if any("players" in e for e in errs) else "漏网!!!", errs[:2])
# B2 orange owner (取第一个 town 改橙)
def to_orange(o):
    for v in o.values():
        if v.get("type") == "town":
            v["options"]["owner"] = "orange"; break
p2 = "/tmp/B_orange.vmap"
make_bad(p2, lambda h: None, to_orange)
errs2, _, _ = m.inspect_vmap(m.Path(p2), (None, None))
print("B2 orange owner ->", "拦截" if any("orange" in e for e in errs2) else "漏网!!!", [e for e in errs2 if "orange" in e][:1])
# B3 red 无城 (把唯一 red town 改 blue)
def steal_red(o):
    for v in o.values():
        if v.get("type") == "town" and v["options"].get("owner") == "red":
            v["options"]["owner"] = "blue"; break
p3 = "/tmp/B_no_red.vmap"
make_bad(p3, lambda h: None, steal_red)
errs3, _, _ = m.inspect_vmap(m.Path(p3), (None, None))
print("B3 red无城 ->", "拦截" if any("red 方无城镇" in e for e in errs3) else "漏网!!!")
# B4 好图 strict 对照 (真实源, dragon 注册表)
reg = m.load_core_registry()
errs4, w4, info4 = m.inspect_vmap(src, reg)
print("B4 真实源 strict ->", "通过" if not errs4 else errs4, info4)
EOF
echo "======== 测 C: --dry-run 不写盘 ========"
printf 'X' >> "$DST"
$PY py/sync_maps_to_runtime.py --dry-run "$MAP" > /tmp/C.log 2>&1
tail -c 2 "$DST" | xxd | tail -1
$PY py/sync_maps_to_runtime.py "$MAP" >/dev/null 2>&1   # 收尾恢复
$PY py/sync_maps_to_runtime.py --check >/dev/null 2>&1 && echo "收尾: 三端全一致 rc=0"
