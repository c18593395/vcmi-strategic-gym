#!/usr/bin/env python3
"""09-14 King_of_Pain_h3m.vmap 阵营重建 (1v3 + 1 中立城)
前置: dragon 已修 (patch_king_dragon_0914.py), header.players 已是 {blue:iona, red:edric}
问题:
  town_0(4,62) orange 非法玩家 -> SIGSEGV "Cannot find player 4 info!"
  09-13 补丁误把原 red 的 town_1(10,8)+hero_0(10,8) 送给 blue -> red 无城无英雄 (no_own_town 脏局)
  blue 仅 2 城且无 3 英雄
方案 (对齐 72X72_01 模板: 英雄 subtype=alchemist, options.type=人物, 城旁 3 格对角):
  town_0 orange->blue, town_1 blue->red, town_4 null->blue, town_2 保持 blue, town_3 留中立
  hero_0 -> red, 移到 town_1 旁 (13,11), edric/15 peasant
  新建 hero_1/2/3 blue @ (7,65)/(62,61)/(57,31), iona/edric/christian, 25 peasant
备份: .bak_rebuild_0914
"""
import json, zipfile, shutil, os, sys

SRC = sys.argv[1] if len(sys.argv) > 1 else \
    r"d:\Bigdata\hero3_fresh\maps\training\King_of_Pain_h3m.vmap"
BAK = SRC + ".bak_rebuild_0914"

HERO_TPL = {
    "l": 0,
    "options": {"army": [{}, {}, {}, {"amount": 25, "type": "core:peasant"}, {}, {}, {}],
                "experience": 0, "formation": "wide", "owner": "blue",
                "portrait": "core:edric", "type": "core:edric"},
    "subtype": "core:alchemist",
    "template": {"animation": "AH04_.def", "editorAnimation": "AH04_E.def",
                 "mask": ["VVV", "VAV"], "visitableFrom": ["+++", "+-+", "+++"]},
    "type": "hero", "x": 0, "y": 0,
}
# key, x, y, 英雄人物
NEW_BLUE = [
    ("hero_1", 7, 65, "core:iona"),       # town_0(4,62)
    ("hero_2", 62, 61, "core:edric"),     # town_2(65,64)
    ("hero_3", 57, 31, "core:christian"),# town_4(54,28)
]
RED_HERO_POS = (13, 11)                  # town_1(10,8)

if not os.path.exists(BAK):
    shutil.copy2(SRC, BAK)
    print("backup ->", BAK)

zin = zipfile.ZipFile(SRC, "r")
names = zin.namelist()
data = {n: zin.read(n) for n in names}
zin.close()
objs = json.loads(data["objects.json"])

# ---------- 城镇归属 ----------
changes = []
def set_owner(key, new):
    old = objs[key]["options"].get("owner")
    objs[key]["options"]["owner"] = new
    changes.append("%s %s: %r -> %s" % (key, (objs[key]["x"], objs[key]["y"]), old, new))

set_owner("town_0", "blue")   # orange
set_owner("town_1", "red")    # 还原
set_owner("town_4", "blue")   # 第3蓝城
# town_2 已 blue, town_3 保持 None(中立)

# ---------- red 英雄 ----------
h0 = objs["hero_0"]
old = (h0["options"].get("owner"), h0["x"], h0["y"])
h0["options"]["owner"] = "red"
h0["options"]["type"] = "core:edric"
h0["options"]["portrait"] = "core:edric"
h0["x"], h0["y"] = RED_HERO_POS
changes.append("hero_0 owner/pos: %r -> (red, %s)" % (old, RED_HERO_POS))

# ---------- 新建 3 蓝英雄 ----------
for key, x, y, who in NEW_BLUE:
    assert key not in objs, "%s 已存在" % key
    o = json.loads(json.dumps(HERO_TPL))
    o["x"], o["y"] = x, y
    o["options"]["type"] = who
    o["options"]["portrait"] = who
    objs[key] = o
    changes.append("NEW %s blue @(%d,%d) %s" % (key, x, y, who))

# ---------- 坐标冲突/越界断言 (切比雪夫距离, 同格或相邻=冲突) ----------
W = H = 72
positions = [(k, o["x"], o["y"], o.get("type")) for k, o in objs.items()]
hero_new = [("hero_0",) + RED_HERO_POS] + [(k, x, y) for k, x, y, _ in NEW_BLUE]
for hk, hx, hy in hero_new:
    assert 0 <= hx < W and 0 <= hy < H, "%s 越界" % hk
    for k, x, y, t in positions:
        if k == hk:
            continue
        d = max(abs(x - hx), abs(y - hy))
        if t == "town":
            # 驻守城镇距离3; 其他城镇必须 >=5; 距离4/2/1 都可疑
            if d != 3 and d < 5:
                raise AssertionError("%s(%d,%d) 与城镇 %s(%d,%d) 距离=%d 可疑" % (hk, hx, hy, k, x, y, d))
        elif d < 2:
            raise AssertionError("%s(%d,%d) 与 %s(%d,%d,%s) 距离=%d mask冲突" % (hk, hx, hy, k, x, y, t, d))
# 每个新英雄必须恰好有一个距离3的驻守城镇
for hk, hx, hy in hero_new:
    near = [k for k, x, y, t in positions if t == "town" and max(abs(x-hx), abs(y-hy)) == 3]
    assert len(near) == 1, "%s 驻守城镇异常: %s" % (hk, near)
    print("  %s(%d,%d) -> %s" % (hk, hx, hy, near[0]))
print("坐标冲突断言通过 (驻守城镇距离3, 其余安全)")

# ---------- 重写 zip ----------
data["objects.json"] = json.dumps(objs, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
tmp = SRC + ".tmp"
with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
    for n in names:
        z.writestr(n, data[n])
os.replace(tmp, SRC)

for c in changes:
    print(" ", c)
print("对象总数 ->", len(objs))
