# [DIAG-0829] P1 重编崩溃根因调查: 给 MLClient.cpp 加阶段插桩 + GAME-null 守卫
# 用法: python3 patch_diag_0829.py apply|revert
# - apply:   MLClient.cpp -> MLClient.cpp (打补丁, 已备份 .bak_diag20260829)
# - revert:  从 .bak_diag20260829 恢复
import os
import sys, shutil

SRC = os.environ.get("SRC", "/home/administrator/vcmi-native/ML/MLClient.cpp")
BAK = SRC + ".bak_diag20260829"

GUARD_OLD = """    void shutdown_vcmi() {
        auto l = std::lock_guard(mutex_shutdown);
        if (flag_shutdown) return;
        cond_shutdown.notify_all();
        flag_shutdown = true;
"""
GUARD_NEW = """    void shutdown_vcmi() {
        auto l = std::lock_guard(mutex_shutdown);
        if (flag_shutdown) return;
        // [DIAG-0829] GAME-null 守卫: init 未完成时 shutdown 原本在 GAME->server() 段错误 (踩坑 #105 core dump), 改为安全 no-op
        if (!GAME) {
            fprintf(stderr, "[MMAI-DIAG] shutdown_vcmi: GAME is null (init incomplete) - safe no-op\\n"); fflush(stderr);
            flag_shutdown = true;
            cond_shutdown.notify_all();
            return;
        }
        cond_shutdown.notify_all();
        flag_shutdown = true;
"""

# (anchor, stage label) — 在 anchor 行后插入 DIAG 日志
STAGES = [
    ("        auto& a = *static_cast<InitArgs*>(initargs_ptr);", "init: entry"),
    ("        console->start();", "init: console started"),
    ("        logConfig->configureDefault();", "init: logConfig default"),
    ("        LIBRARY->initializeFilesystem(false);", "init: initializeFilesystem done"),
    ("        processArguments(leftModel, rightModel, a);", "init: processArguments done"),
    ("        logConfig->configure();", "init: logConfig configured"),
    ("        ENGINE = std::make_unique<GameEngine>(headless);", "init: ENGINE created"),
    ("        GAME = std::make_unique<GameInstance>(aco);", "init: GAME created"),
    ("        loading.join();", "init: initializeLibrary thread joined"),
    ("            ENGINE->cursor().show();\n        }\n    }", "init_vcmi COMPLETE"),
]

START_OLD = """        auto &si = GAME->server();
        if (headless) {"""
START_NEW = """        auto &si = GAME->server();
        fprintf(stderr, "[MMAI-DIAG] start_vcmi: past GAME->server(), launching debugStartTest\\n"); fflush(stderr);
        if (headless) {"""

def diag_line(label, indent="        "):
    return f'{indent}fprintf(stderr, "[MMAI-DIAG] {label}\\n"); fflush(stderr);\n'

def apply():
    with open(SRC) as f:
        src = f.read()
    if "[MMAI-DIAG] init: entry" in src:
        print("ALREADY PATCHED"); return
    assert src.count(GUARD_OLD) == 1, "guard anchor not unique/found"
    src = src.replace(GUARD_OLD, GUARD_NEW)
    for anchor, label in STAGES:
        assert src.count(anchor) == 1, f"anchor not unique: {label} ({src.count(anchor)})"
        src = src.replace(anchor, anchor + "\n" + diag_line(label).rstrip("\n"))
    assert src.count(START_OLD) == 1, "start anchor not unique"
    src = src.replace(START_OLD, START_NEW)
    with open(SRC, "w") as f:
        f.write(src)
    print("PATCH_APPLIED")

def revert():
    shutil.copy(BAK, SRC)
    print("REVERTED")

if __name__ == "__main__":
    {"apply": apply, "revert": revert}[sys.argv[1]]()
