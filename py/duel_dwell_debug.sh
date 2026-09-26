#!/bin/bash
# 冒烟日志深挖: 局末原因 + winner + capture + 城镇字段核对
for i in 1 2 3; do
  LOG=/tmp/rfix_$i.log
  echo "===== run$i ====="
  grep -E 'force game_over|winner|TOWN_CAPTURE|capture|GUARD_DONE|guard|END.*ep|end ep' "$LOG" 2>/dev/null | head -6
  grep 'EP_TIME' "$LOG" | tail -1
  echo
done
echo "===== judgement_day town 完整 options (找 day-1 兵源字段) ====="
/home/administrator/vcmi-workspace/venv/bin/python - <<'PY'
import json, zipfile, re
z = zipfile.ZipFile('/home/administrator/vcmi-native/rel/bin/data/Maps/judgement_day_h3m.vmap')
raw = z.read('objects.json').decode('utf-8', 'ignore')
# 去 // 注释后解析
clean = re.sub(r'//[^\n]*', '', raw)
objs = json.loads(clean)
lst = objs if isinstance(objs, list) else []
for o in lst:
    if isinstance(o, dict) and 'town' in str(o.get('instanceName', o.get('type', ''))).lower():
        opts = o.get('options', {})
        print(f"[{o.get('instanceName')}] owner={opts.get('owner')}")
        for kk in sorted(opts.keys()):
            s = json.dumps(opts[kk], ensure_ascii=False)
            print(f"    {kk}: {s[:300]}")
        break
PY
echo
echo "===== 修复后 T06 duel town options (确认 buildings 落盘) ====="
/home/administrator/vcmi-workspace/venv/bin/python - <<'PY'
import json, zipfile
z = zipfile.ZipFile('/home/administrator/vcmi-native/rel/bin/data/Maps/T06_adventure_108X108_02_duel.vmap')
objs = json.loads(z.read('objects.json').decode('utf-8', 'ignore'))
for k, o in objs.items():
    if 'town' in str(o.get('type', '')).lower():
        print(f"[{k}]", json.dumps(o.get('options', {}), ensure_ascii=False)[:400])
PY
