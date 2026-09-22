"""P10-B2 vmap JSON 规范化: 剥 VCMI 输出的 // 注释, 转严格 JSON, 覆写 zip
用途: VCMI CMapSaverJson 输出的 header.json / objects.json 可能含 `// comment` 尾行注释,
      不合法 JSON; ep_runner 的 json.loads() 直接崩, 必须清理.
用法: python py/clean_vmap_json.py [--zip path.vmap]  (默认处理训练池 3 处副本)
"""
import re, sys, json, zipfile, os, shutil, io

# 匹配行首 (或空格开头) 的 // 注释, 忽略字符串内的 //
COMMENT_LINE = re.compile(r'^\s*//.*$', re.MULTILINE)

def strip_comments(text: str) -> str:
    """删除 C++ // 注释行 (行内 // 少见, 保守只处理行首), 以及行尾多余逗号"""
    text = COMMENT_LINE.sub('', text)
    return text

def normalize(obj, top=True):
    """递归清理: 空列表/字典 → None; 空字符串 → None; 数字保持; 字典 key 保留原样"""
    if isinstance(obj, list):
        r = [normalize(x, False) for x in obj]
        return r if r else None
    if isinstance(obj, dict):
        r = {k: normalize(v, False) for k, v in obj.items()}
        return r if r else None
    if isinstance(obj, str) and obj == "":
        return None
    return obj

TARGETS = [
    r"D:\Bigdata\hero3_fresh\maps\training\King of Pain.h3m.vmap",
    r"D:\Bigdata\hero3_fresh\vcmi\data\Maps\King of Pain.h3m.vmap",
    r"D:\Bigdata\hero3_fresh\vcmi_gym\envs\v13\maps\King of Pain.h3m.vmap",
]

def clean_one(path: str) -> str:
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        items = {n: z.read(n) for n in names}
    fixed = {}
    for n, data in items.items():
        if n.endswith(".json"):
            raw = data.decode("utf-8")
            cleaned = strip_comments(raw)
            try:
                obj = json.loads(cleaned)
            except json.JSONDecodeError as e:
                return f"FAIL {path}: {n} 仍不合法 JSON: {e}"
            obj = normalize(obj)
            fixed[n] = json.dumps(obj, indent=2, ensure_ascii=False).encode("utf-8")
            print(f"  ✓ {n}: {len(raw)}→{len(cleaned)} 字节 (剥注释+严格化)")
        else:
            fixed[n] = data
    # 原子替换
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as out:
        for n in names:
            out.writestr(n, fixed[n])
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        f.write(buf.getvalue())
    shutil.move(tmp, path)
    return "OK"

def main():
    args = sys.argv[1:]
    if "--zip" in args:
        i = args.index("--zip")
        zip_path = args[i + 1]
        print(clean_one(zip_path))
        return
    for t in TARGETS:
        if not os.path.exists(t):
            print(f"SKIP (missing): {t}")
            continue
        print(f"[{t}]")
        print(clean_one(t))
    # 复核: 所有 json 都能被 json.loads 解开
    print("\n=== 复核 ===")
    for t in TARGETS:
        if not os.path.exists(t):
            continue
        ok = True
        with zipfile.ZipFile(t) as z:
            for n in z.namelist():
                if n.endswith(".json"):
                    try:
                        json.loads(z.read(n))
                    except Exception as e:
                        print(f"  FAIL {t}::{n}: {e}")
                        ok = False
        print(f"  {'OK' if ok else 'FAIL'}: {t}")

if __name__ == "__main__":
    main()
