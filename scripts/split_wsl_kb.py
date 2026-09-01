import re, os, sys, shutil, bisect
from collections import OrderedDict

P   = r'D:\Bigdata\hero3_fresh\docs\WSL知识库.md'
OUT = r'D:\Bigdata\hero3_fresh\docs'
LOG = os.path.join(OUT, 'WSL日志')
DRY = '--write' not in sys.argv

SUB = {
    'overview': 'WSL知识库-概述与决策.md',
    'train':    'WSL知识库-训练状态.md',
    'ref':      'WSL知识库-参考速查.md',
}
SUB_TITLE = {'overview': '概述与决策', 'train': '训练状态', 'ref': '参考速查'}

lines = open(P, encoding='utf-8').readlines()
N = len(lines)

def h2_list():
    out = []
    for i, l in enumerate(lines, 1):
        m = re.match(r'^##\s+(.*)$', l.rstrip('\n'))
        if m:
            out.append((i, m.group(1).strip()))
    return out

H2 = h2_list()
def find_start(prefix):
    for i, t in H2:
        if t.startswith(prefix):
            return i
    return None

four     = find_start('四、')
five     = find_start('五、')
seven    = find_start('七、内存')
fourteen = find_start('十四、')
assert all([four, five, seven, fourteen]), (four, five, seven, fourteen)

# ---- 稳定参考三份 ----
overview_body = ''.join(lines[14:four - 1])          # 从 "## 一、" 起，丢弃旧 H1+blockquote
train_body    = ''.join(lines[five - 1:seven - 1])
ref_body      = ''.join(lines[seven - 1:fourteen - 1])

# 训练状态文档：原 8 个 `# 标题` 实为 ```bash 代码围栏内的 shell 注释分隔符，
# 非 Markdown 标题，不会污染目录层级，故保留原样（可整体复制执行）。

train_body = train_body

# 参考速查：修正过期自引用
ref_body = ref_body.replace('docs/知识库.md', 'WSL知识库.md')
ref_body = ref_body.replace('踩坑记录.md', 'WSL踩坑点.md')

# ---- 日志区按日期分桶（十四 起到 EOF）----
log_h2 = [(i, t) for (i, t) in H2 if i >= fourteen]
boundaries = [i for (i, _) in log_h2]
h2date = {}
prev = None
for i, t in log_h2:
    m = re.search(r'(\d{4}-\d{2}-\d{2})', t)
    d = m.group(1) if m else prev
    h2date[i] = d
    prev = d

def date_of_line(ln):
    pos = bisect.bisect_right(boundaries, ln) - 1
    return h2date[boundaries[pos]] if pos >= 0 else None

buckets = OrderedDict()
cur = None
buf = []
for off in range(fourteen - 1, N):
    ln = off + 1
    d = date_of_line(ln)
    if d is None:
        continue
    if d != cur:
        if cur is not None:
            buckets.setdefault(cur, []).append(''.join(buf))
        cur, buf = d, []
    buf.append(lines[off])
if cur is not None:
    buckets.setdefault(cur, []).append(''.join(buf))

# 每个日期文件的首个 H2 标题，作为日志列表描述
log_desc = {}
for d, blk in buckets.items():
    first = d
    for seg in blk:
        for l in seg.splitlines():
            if l.startswith('## '):
                first = l.strip('# \n')
                break
        if first != d:
            break
    log_desc[d] = first

# ---- dry-run 报告 ----
print('总行数', N, '| DRY=', DRY)
print(f'概述与决策 : 行 {1}-{four-1} -> {SUB["overview"]}')
print(f'训练状态   : 行 {five}-{seven-1} -> {SUB["train"]} (H1降级已应用)')
print(f'参考速查   : 行 {seven}-{fourteen-1} -> {SUB["ref"]} (引用已修正)')
print(f'四、踩坑大全 : 行 {four}-{five-1} -> 丢弃, 改为总索引链接表')
print(f'日志分桶   : {len(buckets)} 个日期文件 -> {LOG}/')
for d in buckets:
    print(f'   {d}.md  ({len("".join(buckets[d]).splitlines())} 行) {log_desc[d][:40]}')
print('\n[DRY] 确认后加 --write 执行。')
if DRY:
    sys.exit(0)

# ===== 实际写入 =====
os.makedirs(LOG, exist_ok=True)

def write_doc(path, title, note, body):
    head = f'# WSL知识库 — {title}\n\n{note}\n\n---\n\n'
    open(path, 'w', encoding='utf-8', newline='').write(head + body)
    print('写出', os.path.basename(path), len(body.splitlines()), '行')

note_o = '> 本文件是 `WSL知识库.md` 总索引下的稳定参考子文档（项目概述与关键技术决策）。\n> 结论性内容，按需就地修订；内容截至 2026-08-29。'
note_t = '> 本文件是 `WSL知识库.md` 总索引下的稳定参考子文档（当前训练参数与环境搭建/部署）。\n> 结论性内容，按需就地修订；内容截至 2026-08-29。'
note_r = '> 本文件是 `WSL知识库.md` 总索引下的稳定速查子文档（内存偏移/ABI/文件索引/数据流/双目录陷阱）。\n> 纯查表，极少改动。'
write_doc(os.path.join(OUT, SUB['overview']), SUB_TITLE['overview'], note_o, overview_body)
write_doc(os.path.join(OUT, SUB['train']),    SUB_TITLE['train'],    note_t, train_body)
write_doc(os.path.join(OUT, SUB['ref']),      SUB_TITLE['ref'],      note_r, ref_body)

for d, blk in buckets.items():
    body = ''.join(blk)
    head = f'# 工作日志 {d}\n\n> 本文件是 `WSL知识库.md` 体系下的日期工作日志（append-only，每轮会话一份）。\n> 原始章节标题保留为 H2，便于回溯。\n\n---\n\n'
    open(os.path.join(LOG, d + '.md'), 'w', encoding='utf-8', newline='').write(head + body)
    print('写出日志', d + '.md', len(body.splitlines()), '行')

# ===== 总索引 =====
idx = '# 知识库 — HoMM3 全盘操盘 AI（体系总索引）\n\n'
idx += '> 本文件是项目文档体系的**总索引**（2026-08-31 重构）。知识库内容分三层，请按需取读，勿在单文件内堆砌。\n'
idx += '> - **稳定参考**：结论性内容，就地修订，标注截至日期。\n'
idx += '> - **问题登记册**：踩坑点，每条带状态字段（✅/⚠️/❌/🔄）。\n'
idx += '> - **日期工作日志**：每轮会话一份，append-only，永不回编。\n'
idx += '>\n'
idx += '> **约定（AI 必读）**：收到“保存踩坑点”写 `WSL踩坑点.md`（或对应主题子文档）；收到“记日志/今天进展”写 `WSL日志/YYYY-MM-DD.md`；稳定结论变更时更新对应参考子文档。模型读取本索引后应**自动取读下方子文档与日志目录**获取完整内容。\n\n'
idx += '---\n\n'
idx += '## 一、稳定参考\n\n'
idx += f'- [概述与决策]({SUB["overview"]}) — 项目目标、双轨架构、关键技术决策（Passability / 两段式 / Nullkiller2 / VMAP / 观测动作 / step 机制）\n'
idx += f'- [训练状态]({SUB["train"]}) — 当前训练参数、环境搭建与部署（截至 2026-08-29）\n'
idx += f'- [参考速查]({SUB["ref"]}) — 内存偏移表、StrategicState ABI、关键文件索引、数据流、WSL 双目录构建陷阱\n\n'
idx += '## 二、问题登记册（踩坑点）\n\n'
idx += '- [WSL踩坑点.md](WSL踩坑点.md) — 总索引，下含 5 个主题子文档：环境-WSL与进程 / 构建-编译与部署 / 引擎-VCMI-API / 训练-奖励与策略 / 地图-vmap生成\n\n'
idx += '### 踩坑大全速查（原“四、踩坑大全”已改为链接，不再复述）\n\n'
idx += '| 主题 | 归属子文档 |\n| --- | --- |\n'
idx += '| 4.1 step2 挂死（SEND→WAIT 顺序） | 引擎-VCMI-API |\n'
idx += '| 4.2 MMAI core dump（切 Nullkiller2） | 构建-编译与部署 |\n'
idx += '| 4.3 ABI 不兼容（三件套重编） | 构建-编译与部署 |\n'
idx += '| 4.4 .pyc 缓存（NTFS） | 环境-WSL与进程 |\n'
idx += '| 4.5 subprocess 僵尸（os._exit） | 引擎-VCMI-API |\n'
idx += '| 4.6 DummyVecEnv 短路 | 训练-奖励与策略 |\n'
idx += '| 4.7 子 agent 401（provider→deepseek） | 环境-WSL与进程 |\n'
idx += '| 4.8 vmap 跑战略训练（见 #84-90） | 地图-vmap生成 |\n\n'
idx += '## 三、日期工作日志\n\n'
for d in buckets:
    idx += f'- [{d}.md](WSL日志/{d}.md) — {log_desc[d]}\n'
idx += '\n---\n\n> 注：原单文件 2546 行已重构为「1 总索引 + 3 稳定子文档 + 5 踩坑子文档 + N 日期日志」。编号撞车（七/八/九 复用）、H1 泛滥、自引用过期等问题已随拆分消除。\n'

open(P, 'w', encoding='utf-8', newline='').write(idx)
print('重写总索引 ->', P, len(idx.splitlines()), '行')
