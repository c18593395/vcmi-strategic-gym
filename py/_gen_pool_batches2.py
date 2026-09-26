"""生成 _pool_batches.json — 入池节奏三批（09-21 定稿）
修正: ①逗号→下划线 ②survey匹配key与h3m文件名对齐（去后缀/小写/空格→下划线）
判定: water_touched OR has_island OR risk==open_water_isolation → batch4(水/岛图, WIN-5轴后)
      risk==ally_chaos → batch2(联盟图, 二批)
      其余 → batch1(安全图) 按include降序, 首批取前5
"""
import json, re, os

BASE = r"d:\Bigdata\hero3_fresh"
POOL_DIR = f"{BASE}\\maps\\training\\h3m_pool"
survey = json.load(open(f"{BASE}/py/h3m_type_survey.json", encoding="utf-8"))
rank   = json.load(open(f"{BASE}/maps/h3m_to_vmap/_pool_rank.json", encoding="utf-8"))

def _key(s):
    """h3m文件名(去.h3m) → 小写/去后缀 → 空格/逗号/撇号/括号/连字符→下划线 的标准化key"""
    s = s.replace(".h3m", "").replace(".H3M", "")
    s = s.lower()
    s = re.sub(r"[\s,'()\-]+", "_", s)
    return re.sub(r"_+", "_", s).strip("_")

def sanitize(h3m_name):
    """h3m名 → vmap文件名（匹配磁盘实存文件的命名规则: 小写下划线+_h3m.vmap）"""
    s = _key(h3m_name)
    return s + "_h3m.vmap"

name2row = {_key(row["name"]): row for row in survey["rows"]}

batches = {"batch1": [], "batch2": [], "batch4": [], "batch3": []}
unmatched_survey = []   # survey未匹配的h3m名

for h3m_name, info in rank.items():
    vmap = sanitize(h3m_name)
    k = _key(h3m_name)
    row = name2row.get(k)
    water  = row is not None and row.get("water_touched", False)
    island = row is not None and row.get("has_island", False)
    ug     = row is not None and row.get("has_underground", 0) == 1
    risk   = info.get("risk_tag", "unknown")
    if row is None:
        unmatched_survey.append(h3m_name)

    if water or island or risk == "open_water_isolation":
        # 水/岛图全部推后 WIN-5 轴后；有地下的也一并归入 batch3 标签
        reason = "water" if water else ("island" if island else "open_water_risk")
        entry = {"vmap": vmap, "h3m": h3m_name, "include": info["include"],
                 "risk": risk, "reason": reason}
        if ug:
            entry["ug"] = True
            batches["batch3"].append(entry)
        batches["batch4"].append(entry)
    elif ug:
        # 无水无岛但有地下层 → batch3（等 --keep-underground 轴落地）
        batches["batch3"].append({
            "vmap": vmap, "h3m": h3m_name, "include": info["include"],
            "risk": risk, "reason": "underground"
        })
    elif risk == "ally_chaos":
        batches["batch2"].append({
            "vmap": vmap, "h3m": h3m_name, "include": info["include"], "risk": risk
        })
    else:
        batches["batch1"].append({
            "vmap": vmap, "h3m": h3m_name, "include": info["include"],
            "risk": risk, "train_value": info.get("train_value", 0)
        })

batches["batch1"].sort(key=lambda x: -x["include"])
first5 = batches["batch1"][:5]
rest   = batches["batch1"][5:]

# 修正: manifest_destiny 等有水地下的图已在 batch4/batch3，首批5张应该只有纯水无岛无地下的
# 若首批里还有 UG 图（batch1 误入），在结果里标出
result = {
    "desc": "入池节奏四批（09-21 定稿）",
    "first5": first5,
    "batch1_rest": rest,
    "batch2_ally": batches["batch2"],
    "batch4_water_island": batches["batch4"],
    "batch3_underground": batches["batch3"],
    "mix_ratios": {
        "first5": 0.10,
        "after_first5_green": 0.15,
        "batch4": "WIN-5 轴后（需造船激励）",
        "batch3": "地下轴（--keep-underground）落地后",
    },
}

out = f"{BASE}/maps/h3m_to_vmap/_pool_batches.json"
json.dump(result, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

print(f"written: {out}")
print(f"\n=== 首批5张（HOMM3_H3M_MIX=0.10）===")
for i, m in enumerate(first5, 1):
    print(f"  {i}. {m['vmap']}  (src: {m['h3m']})  include={m['include']:.2f}  risk={m['risk']}")

print(f"\n=== 二批（首批绿后 MIX=0.15）: {len(rest)}安全 + {len(batches['batch2'])}联盟 ===")
for m in rest:
    print(f"    {m['vmap']}  include={m['include']:.2f}  risk={m['risk']}")
for m in batches["batch2"]:
    print(f"    [ALLY] {m['vmap']}  include={m['include']:.2f}")

print(f"\n=== 三批（WIN-5轴后，水/岛图 {len(batches['batch4'])} 张）===")
for m in batches["batch4"]:
    extra = " [+UG]" if m.get("ug") else ""
    print(f"    {m['vmap']}  reason={m['reason']}  include={m['include']:.2f}{extra}")

print(f"\n=== 地下层图（batch3，--keep-underground 轴落地后 {len(batches['batch3'])} 张）===")
for m in batches["batch3"]:
    print(f"    {m['vmap']}  reason={m['reason']}  include={m['include']:.2f}  risk={m['risk']}")

if unmatched_survey:
    print(f"\n[survey未匹配 {len(unmatched_survey)}张 需人工核对]: {unmatched_survey}")
