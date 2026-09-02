# C++ 补丁镜像 — 取兵链路修复 (2026-09-02, T7.6)

本目录是 WSL 侧 vcmi-native 打补丁源码的**仓库镜像**（真实构建源在 WSL `/home/administrator/vcmi-native/`，构建树 = `vcmi-native/rel/`）。

| 文件 | 部署路径 (WSL) | 内容 |
|------|----------------|------|
| AAI.cpp | `~/vcmi-native/AI/MMAI/AAI/AAI.cpp` | P1: case16-18 招兵前 visit 块 + 邻接守卫; P1b: dst 显式 getVisitingHero(); 临时诊断 (rl_recruit_diag, 验证后删) |
| strategic_state.cpp | `~/vcmi-native/ML/strategic_state.cpp` | P3: towns 段 garrison[7] 填充 (getUpperArmy) |

双目录同步副本: `~/vcmi-native-build/` 同名文件已 cp 同步。

重编与部署 (须停训, -j4, 见踩坑 #131):
```
systemctl --user stop homm3-train-v5
cd ~/vcmi-native/rel && cmake --build . --target MMAI mlclient -j4
cp bin/AI/libMMAI.so ~/vcmi-workspace/vcmi/rel/bin/AI/   # 运行时副本 2
cp bin/libmlclient.so ~/vcmi-workspace/vcmi/rel/bin/
cp bin/AI/libMMAI.so ~/vtest/bin/AI/                     # 副本 3
cp bin/libmlclient.so ~/vtest/bin/
cp bin/libmlclient.so ~/vcmi-native/build/bin/           # 副本 4
```
备份: `~/vcmi-native/**/**.bak_taketroops_0902_0433`
