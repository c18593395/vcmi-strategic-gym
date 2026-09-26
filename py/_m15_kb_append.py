# -*- coding: utf-8 -*-
"""M1.5 收尾: 知识库待整理区追加 09-27 T13.11 M1.5 记录。"""

TEXT = '''
### 09-27 T13.11 M1.5 Nullkiller2.dll 补编（vs 真 NK2 对战底座）

**背景**: T13.11（模型 vs NK2 + 用户观战）M1 拓扑闭环后发现蓝方现役 = PpoModelAI 非 NK2；bin/AI 缺 Nullkiller2.dll（历史坑: build.ninja 只有 NK2 obj 编译规则无链接目标, LoadLibraryW error 126）。

**补编全记录（踩坑 #68 BattleAI 手链范式同款）**:
1. Nullkiller2 是 OBJECT 库（libFacade 把其 obj 静态吸收进 VCMI_lib.dll, 但 CDynLibHandler::getNewAI 走 LoadLibrary 需要 bin/AI/Nullkiller2.dll 独立文件）。
2. 恢复官方 main.cpp 入口（fork 删了; 37 行: GetGlobalAiVersion/GetAiName/GetNewAI 三 C 导出, GetNewAI = make_shared<NK2AI::AIGateway>）。
3. 手工链接: 70 obj（69 NK2 + main）+ libFacade/.../server/strategic_state.cpp.obj（解析 adventure_capture_turn 钩子; 蓝方 playerID!=0 不进采集路径, 状态副本无实际影响, VCMI_lib.dll 不动 = ModelAI/训练实验面零影响）+ -lVCMI_lib -ltbb12 -lboost_filesystem-mt -static-libstdc++。脚本 py/_m15_extract_link_cmd.py。
4. settings.json adventureEnemyAI: ModelAI→Nullkiller2（只切 Enemy, Allied 保持 ModelAI; 备份 .bak_pre_nk2_0927）。
5. 验证: M1 探针复跑 PASS — 蓝方身份=Nullkiller2, 动作包 281, 3 场真实战斗（BattleStart+BattleResult）, 8 轮交替, 无崩。

**新踩坑①**: mingw GCC「编译零输出 exit=1」（hello world 都挂）= PATH 污染——默认 PATH 有冲突 dll 使 cc1plus 加载失败无声死; 解法 = 前置 C:/msys64/mingw64/bin（ninja 的 cmd /c 继承, 构建前 export）。
**新踩坑②**: CMake 4.4.2 re-run 生成 build.ninja 漏求值 genex（LINK_LIBRARIES 出现字面 $<LINK_ONLY:ws2_32>）→ ninja bad $-escape 全构建瘫痪; 解法 = python 删三个 genex（py/_m15_fix_ninja_genex.py; -lws2_32 等明文仍在命令行, 功能等价）; 每次 cmake re-run 复发。
**附带**: .d 依赖文件全丢（0911 后清过）→ ninja 强制重编; re-run CMake 再生 Version.h 触发 AIGateway 重编——修 PATH 后正常可编, depfile hack 不再需要。

**回切口径**: 要回 PpoModelAI 蓝方 = 还原 settings.json.bak_pre_nk2_0927; Nullkiller2.dll 留 bin/AI 无副作用（不被加载）。

'''

with open(r'docs/WSL知识库.md', 'a', encoding='utf-8', newline='') as f:
    f.write(TEXT)
print('appended to WSL知识库.md 待整理区')
