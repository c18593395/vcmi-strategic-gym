import zipfile
z = zipfile.ZipFile('/mnt/d/vcmi_model_ai/onnxruntime.zip')
names = z.namelist()
print(f"total {len(names)}")
for n in names[:20]:
    print(n)
# 找 .so 文件
sos = [n for n in names if n.endswith('.so') or '.so.' in n]
print("--- .so files:", len(sos))
for n in sos[:10]:
    print(n)
