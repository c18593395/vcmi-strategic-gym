import os, shutil, datetime

P = r'D:\Bigdata\hero3_fresh\docs\WSL踩坑点.md'

# 以 Windows 原生视图为准（用户真实编辑的文件）
lines = open(P, encoding='utf-8').read().splitlines(keepends=True)
n = len(lines)
assert n > 2000, f"文件行数异常({n})，疑似非用户真实版本，已中止以防写错文件"

# 备份（同目录，带日期后缀，不污染 git 跟踪内容）
bak = P + '.' + datetime.date.today().strftime('%Y%m%d') + '.bak'
if not os.path.exists(bak):
    shutil.copy2(P, bak)
    print('已备份 ->', bak)
else:
    print('备份已存在，跳过:', bak)

HEADER = """# 踩坑点文档约定（AI 必读）

> 本文件 `docs/WSL踩坑点.md` 是踩坑点总文档，长期保留。
> 收到“保存踩坑点”指令时，模型仍写入本文件，不新建、不分散到其他文件。
>
> 内容按主题拆分为以下 5 个分区（相当于 5 个文档）。新增条目请归入对应分区的一级标题下，不要再堆在文件末尾：
> 1. **环境-WSL与进程** —— WSL / 路径 / 进程 / 信号量 / 权限 / 文件系统
> 2. **构建-编译与部署** —— 三副本同步 / 部署 .so / 编译链 / CMake
> 3. **引擎-VCMI-API** —— VCMI 引擎 API 语义 / 调用约定 / 枚举
> 4. **训练-奖励与策略** —— RL 训练 / 奖励信号 / 策略 / ctypes 接口
> 5. **地图-vmap生成** —— vmap 地图生成 / 加载 / 地形
>
> 每条踩坑点必须带状态字段（四选一）：✅ 已解决 / ⚠️ 待查 / ❌ 已证伪(见 #X) / 🔄 绕过中
> 引用其他条目统一用 `见 #X` 形式，避免模糊指代。
>
> 已知损坏段（按用户决定未恢复，待补）：#57–#62 一带（MMAI battle hang 等行内代码曾丢失）；#80 有重复副本，以完整副本为准。

---

"""

new = HEADER + ''.join(lines)
open(P, 'w', encoding='utf-8', newline='').write(new)
print('写入完成：原行数', n, '-> 新行数', new.count(chr(10)) + (0 if new.endswith(chr(10)) else 1))
print('新首行:', repr(new.splitlines()[0][:30]))
