import zipfile, json, glob
for p in sorted(glob.glob('/mnt/d/Bigdata/hero3_fresh/Maps/training/T05_*.vmap')):
    z = zipfile.ZipFile(p)
    hits = []
    for name in z.namelist():
        data = z.read(name).decode('utf-8', errors='ignore')
        if 'inham' in data.lower():
            # 定位具体位置
            o = json.loads(data)
            def walk(obj, path):
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        walk(v, f"{path}.{k}")
                elif isinstance(obj, list):
                    for i, v in enumerate(obj):
                        walk(v, f"{path}[{i}]")
                elif isinstance(obj, str) and 'inham' in obj.lower():
                    hits.append(f"{name}:{path} = {obj}")
            walk(o, name)
    print(p.split('/')[-1], "→", hits if hits else "无 inham")
