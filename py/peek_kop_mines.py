"""探查 King of Pain 精简 vmap 中 mine 对象的 subtype 分布"""
import zipfile, json, re
from collections import Counter

def strip_json_comments(s):
    s = re.sub(r"//[^\n]*", "", s)
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    return s

src = "vcmi/data/Maps/King_of_Pain_h3m.vmap"
with zipfile.ZipFile(src) as z:
    objs = json.loads(strip_json_comments(z.read("objects.json").decode('utf-8')))

mine_types = Counter()
mine_owner = Counter()
for k, v in objs.items():
    if not isinstance(v, dict): continue
    if "mine" not in k: continue
    mine_types[str(v.get("subtype"))] += 1
    mine_owner[str(v.get("owner"))] += 1

print("mine subtype 分布:", mine_types)
print("mine owner 分布:", mine_owner)

# 对照 T06 训练图看看正常 mine subtype 长什么样
print("\n--- T06 对照 ---")
src2 = "vcmi/data/Maps/T06_adventure_72X72_02_duel.vmap"
with zipfile.ZipFile(src2) as z:
    objs2 = json.loads(strip_json_comments(z.read("objects.json").decode('utf-8')))
mine_types2 = Counter()
for k, v in objs2.items():
    if not isinstance(v, dict): continue
    if "mine" not in k: continue
    mine_types2[str(v.get("subtype"))] += 1
print("T06 mine subtype:", mine_types2)

# 也检查 town 修补效果
print("\n--- King of Pain town subtype (修补后) ---")
town_types = Counter()
for k, v in objs.items():
    if not isinstance(v, dict): continue
    if "town" not in k: continue
    town_types[str(v.get("subtype"))] += 1
print("town subtype:", town_types)
