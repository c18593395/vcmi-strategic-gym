import os
# [DIAG-0829] 修复 COMPLETE 标记错位 v2 (按行处理, 空白免疫)
SRC = os.environ.get("SRC", "/home/administrator/vcmi-native/ML/MLClient.cpp")
with open(SRC) as f:
    lines = f.readlines()

idx_complete = [i for i, l in enumerate(lines) if "init_vcmi COMPLETE" in l]
assert len(idx_complete) == 1, f"complete markers: {idx_complete}"
i = idx_complete[0]
line = lines.pop(i)  # 移除错位行
# 找 show(); 行 (标记在闭合括号后, show 行在其上方 3~4 行)
j = next(k for k in range(max(0, i - 6), i) if "ENGINE->cursor().show();" in lines[k])
lines.insert(j + 1, '            fprintf(stderr, "[MMAI-DIAG] init_vcmi COMPLETE\\n"); fflush(stderr);\n')

with open(SRC, "w") as f:
    f.writelines(lines)
print("FIX_OK")
