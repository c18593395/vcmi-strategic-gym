"""pool 37张逐一检查 has_underground / water_touched / has_island
key匹配: 直接 lowercase 查 name (survey name lower == h3m名去后缀 lower)
"""
import json, re, os

BASE = r"d:\Bigdata\hero3_fresh"
pool_dir = f"{BASE}\\maps\\training\\h3m_pool"
survey = json.load(open(f"{BASE}/py/h3m_type_survey.json", encoding="utf-8"))
rank   = json.load(open(f"{BASE}/maps/h3m_to_vmap/_pool_rank.json", encoding="utf-8"))

def _key(s):
    """h3m名 → 匹配 survey name.lower() 的 key (小写,空格保留)"""
    return s.replace(".h3m","").replace(".H3M","").lower()

# survey: name.lower() 直接做 key
name2row = {row["name"].lower(): row for row in survey["rows"]}

print(f"pool实存vmap数: {len([f for f in os.listdir(pool_dir) if f.endswith('.vmap')])}")
print(f"\n=== pool 37张逐一检查 (h3m, include, risk, UG, WATER, ISLAND) ===")
for h3m_name, info in rank.items():
    k = _key(h3m_name)
    row = name2row.get(k)
    if row is None:
        print(f"  {h3m_name:45s} include={info['include']:.2f} risk={info['risk_tag']:20s} [未匹配]")
        continue
    ug  = row.get("has_underground", 0)
    wt  = row.get("water_touched", False)
    il  = row.get("has_island", False)
    risk = info["risk_tag"]
    flags = ("UG " if ug else "-- ") + ("WTR" if wt else "---") + (" ISL" if il else "---")
    print(f"  {h3m_name:45s} include={info['include']:.2f} risk={risk:20s} {flags}")
