# -*- coding: utf-8 -*-
"""知识库去重 + 追加 M2/M3 记录。"""
import re

P = r'docs/WSL知识库.md'
text = open(P, encoding='utf-8').read()

marker = '### 09-27 T13.11 M1.5 Nullkiller2.dll 补编（vs 真 NK2 对战底座）'
first = text.find(marker)
second = text.find(marker, first + 1)
if second != -1:
    tail = text[second:]
    text = text[:second]
    print(f'removed duplicate M1.5 block ({len(tail)} chars)')

ADD = '''
### 09-27 T13.11 M2 红方真实决策环 PASS + M3 观战半程

**M2 ✅（py/p11_m2_model_play.py PASS）**: Twins 红方资产 SRV-DIAG 实锤（HERO OI=350 @(1,8,0) + TOWN OI=347, 蓝方 HERO 732/TOWN 740 在 z=1 地下）。决策链 Build(DWELL_LVL_1=30) 受理 → RecruitCreatures(pikeman 试探) 发出 → **MoveHero (1,8)→(2,8) TryMoveHero SUCCESS**（后续 3 次 FAILED = 地形校验真实工作, 换向逻辑触发; v2 待改: FAILED 回滚 pos——乐观更新会漂移）。9 轮 vs Nullkiller2 无崩。**模型推理受数据源墙限制留 S-2**（外挂 client 建 3464 obs 不全, 备料已确认; 规则驱动现状）。

**M3 🔄 半程（py/p11_m3_spectate_probe.py v2）**:
- **第 3 连接协议层全通**: Python(红)+client1(蓝NK2)+client3(testmap 同款第 3 连接) 三 CC 全成 → 14LobbyStartGame → 对局正常开始红蓝交替。**P8-E (09-15) 的 server NEW_GAME 崩已不复现**（09-16 #205 robustness 副作用/时序差异）。
- **剩 client spectate 界面崩溃**: client3 无 slot → Client.cpp L238-249 hasHumanPlayer=false 自动 spectate → 装界面后 `Attempt to read from 0x98` 空指针崩（fork client SPECTATOR 路径又一处未判空; 与 09-10 已修 `getPlayerState()->quests` 0x6d8 同族）。dmp: `My Games/vcmi/logs/VCMI_client.exe_crashinfo.dmp`。候选 7 处: NetPacksClient.cpp L410-411 / CPlayerInterface.cpp L373 / CResDataBar L110 / AdventureMapShortcuts L652 / CKingdomInterface L649-650（getPlayerState 直链）。
- **无 --testmap 的 client 不连 server**（headless 空转主菜单, 无 CLI 直连 lobby 参数）→ 观战位必须 testmap 同款形态 join。
- 深修路径: 定位 0x98 → 判空修 → 重编 VCMI_client.exe（链接链未验证, client 依赖 VCMI_lib.dll 链接同 NK2 手链范式可参考）。
'''

if 'M2 红方真实决策环 PASS' not in text:
    text += ADD
    print('appended M2/M3 record')

open(P, 'w', encoding='utf-8', newline='').write(text)
print('done')
