import re, os, sys, shutil

P = r'D:\Bigdata\hero3_fresh\docs\WSL踩坑点.md'
DRY = '--write' not in sys.argv
SKIP = set(range(2130, 2196)) | set(range(1068, 1084))  # #80第一份 / #57第二份 损坏副本

SUB = {
    'env':    r'D:\Bigdata\hero3_fresh\docs\WSL踩坑点-环境-WSL与进程.md',
    'build':  r'D:\Bigdata\hero3_fresh\docs\WSL踩坑点-构建-编译与部署.md',
    'engine': r'D:\Bigdata\hero3_fresh\docs\WSL踩坑点-引擎-VCMI-API.md',
    'train':  r'D:\Bigdata\hero3_fresh\docs\WSL踩坑点-训练-奖励与策略.md',
    'map':    r'D:\Bigdata\hero3_fresh\docs\WSL踩坑点-地图-vmap生成.md',
}
SUB_TITLE = {'env':'环境-WSL与进程','build':'构建-编译与部署','engine':'引擎-VCMI-API',
             'train':'训练-奖励与策略','map':'地图-vmap生成'}

# 精确映射：块起始行 -> 桶（基于标题语义人工判定）
MAPPING = {
 # env
 112:'env',120:'env',128:'env',350:'env',358:'env',366:'env',392:'env',402:'env',504:'env',512:'env',
 520:'env',528:'env',536:'env',1310:'env',1582:'env',1596:'env',1958:'env',2016:'env',2542:'env',2663:'env',2624:'env',
 # build
 32:'build',44:'build',52:'build',60:'build',70:'build',78:'build',94:'build',102:'build',420:'build',440:'build',
 450:'build',460:'build',470:'build',488:'build',570:'build',588:'build',608:'build',620:'build',674:'build',684:'build',
 722:'build',730:'build',964:'build',1012:'build',1172:'build',1218:'build',1232:'build',1334:'build',1398:'build',1408:'build',
 1550:'build',1812:'build',1888:'build',1908:'build',1928:'build',2196:'build',2600:'build',
 # engine
 144:'engine',154:'engine',164:'engine',174:'engine',184:'engine',194:'engine',248:'engine',256:'engine',274:'engine',284:'engine',
 294:'engine',302:'engine',310:'engine',320:'engine',328:'engine',336:'engine',430:'engine',554:'engine',562:'engine',580:'engine',
 640:'engine',658:'engine',792:'engine',902:'engine',912:'engine',922:'engine',932:'engine',978:'engine',990:'engine',1002:'engine',
 1026:'engine',1046:'engine',1084:'engine',1096:'engine',1114:'engine',1128:'engine',1142:'engine',1154:'engine',1242:'engine',1252:'engine',
 1264:'engine',1292:'engine',1346:'engine',1358:'engine',1386:'engine',1422:'engine',1434:'engine',1446:'engine',1460:'engine',1476:'engine',
 1528:'engine',1560:'engine',1610:'engine',1648:'engine',1692:'engine',1714:'engine',1792:'engine',1864:'engine',1972:'engine',2430:'engine',
 2512:'engine',2520:'engine',2528:'engine',2552:'engine',2558:'engine',2564:'engine',2582:'engine',2612:'engine',2618:'engine',2632:'engine',2576:'engine',
 # train
 266:'train',374:'train',544:'train',890:'train',1198:'train',1278:'train',1322:'train',1372:'train',1488:'train',1500:'train',
 1990:'train',2004:'train',2028:'train',2040:'train',2054:'train',2092:'train',2264:'train',2310:'train',2464:'train',2502:'train',
 2534:'train',2640:'train',2646:'train',2652:'train',2669:'train',2675:'train',2681:'train',2688:'train',
 # map
 212:'map',222:'map',232:'map',2364:'map',2376:'map',2388:'map',2398:'map',2408:'map',2420:'map',2440:'map',
 2454:'map',2476:'map',2588:'map',2594:'map',2657:'map',
}

def is_title(l): return bool(re.match(r'^#{2,4}\s', l))
def is_section(l):
    if re.match(r'^##\s*[一二三四五六七八九十]+、', l): return True
    if re.match(r'^##\s*2026-\d', l): return True
    return False
def is_entry(l):
    if re.match(r'^###\s+\d+\.', l): return True
    if re.match(r'^###\s+#\d', l): return True
    if re.match(r'^##\s*踩坑\s*#\d', l): return True
    if re.match(r'^##\s*十二、', l): return True
    return False

L = open(P, encoding='utf-8').read().splitlines(keepends=True)
N = len(L)
buckets = {k: [] for k in SUB}
order = []
cur = []
cur_start = None

def flush():
    global cur, cur_start
    if cur:
        bucket = MAPPING.get(cur_start, 'engine')
        buckets[bucket].append(''.join(cur))
        order.append((bucket, cur[0].strip(), cur_start))
        cur = []
        cur_start = None

for i, l in enumerate(L, 1):
    if i in SKIP:
        flush(); cur = []; cur_start = None; continue
    if is_title(l):
        if is_section(l):
            flush(); cur = []; cur_start = None; continue
        if is_entry(l):
            flush(); cur = [l]; cur_start = i; continue
        # 其他标题（### 现象 / ### 修复链 等）
        if cur:
            cur.append(l)          # 嵌套子标题，归入当前块
        else:
            cur = [l]; cur_start = i   # 章节总结性标题，开启新块
    else:
        if cur_start is None and not cur:
            continue
        cur.append(l)
flush()

# dry-run 报告
print('总行数', N, '| DRY=', DRY, '| 跳过', len(SKIP))
unmapped = [s for s in [cur_start] if s and s not in MAPPING]
for k in SUB:
    items = [(t, s) for (bk, t, s) in order if bk == k]
    print(f'\n===== {SUB_TITLE[k]} ({k}) : {len(items)} 条 =====')
    for t, s in items:
        print(f'  {s:5d} | {t[:58]}')
print('\n[DRY] 确认后加 --write 执行。')
if DRY: sys.exit(0)

# 实际写入
bak = P + '.split_bak'
if not os.path.exists(bak):
    shutil.copy2(P, bak); print('备份 ->', bak)
for k, path in SUB.items():
    head = f'# WSL踩坑点 — {SUB_TITLE[k]}\n\n> 本文件是 `docs/WSL踩坑点.md` 拆分出的主题子文档。新增本主题踩坑点请归入此处；主文件仅作索引。\n\n---\n\n'
    open(path, 'w', encoding='utf-8', newline='').write(head + ''.join(buckets[k]))
    print('写出', os.path.basename(path), len(buckets[k]), '条')
idx = '# 踩坑点文档索引（AI 必读）\n\n'
idx += '> 本文件 `docs/WSL踩坑点.md` 是踩坑点总索引，长期保留。\n'
idx += '> 收到“保存踩坑点”指令时，模型仍写入本文件（方式1），或自动归入下方对应子文档（方式2）。\n'
idx += '> 不论哪种方式，模型读取本文件后，应**自动读取下方 5 个子文档**获取完整内容。\n\n'
idx += '> 内容已拆分为以下 5 个主题文档（相当于 5 个分区）：\n'
for i, k in enumerate(['env','build','engine','train','map'], 1):
    idx += f'> {i}. **{SUB_TITLE[k]}** —— `{os.path.basename(SUB[k])}`\n'
idx += '>\n> 每条踩坑点必须带状态字段（四选一）：✅ 已解决 / ⚠️ 待查 / ❌ 已证伪(见 #X) / 🔄 绕过中\n'
idx += '> 引用其他条目统一用 `见 #X` 形式。\n\n---\n\n'
idx += '## 条目归属速查（按原文档出现顺序）\n\n| 条目 | 归属文档 |\n| --- | --- |\n'
def _short(t):
    t = re.sub(r'^#{2,4}\s*', '', t).strip()
    t = t.replace('|', '\\|')
    return (t[:48] + '…') if len(t) > 49 else t
for bucket, title, _ in order:
    idx += f'| {_short(title)} | {SUB_TITLE[bucket]} |\n'
idx += '\n> 注：#57 有重复，以“信号量通信修复”为准，另一份（MMAI_USER battle hang）损坏未恢复已剔除；#80 有重复，以完整副本为准，损坏副本已剔除。\n'
open(P, 'w', encoding='utf-8', newline='').write(idx)
print('重写主文件索引 ->', P, '| 归属表', len(order), '条')
