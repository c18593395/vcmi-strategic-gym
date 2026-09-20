import ast, sys
with open("/mnt/d/Bigdata/hero3_fresh/py/h3m_batch_pipeline.py", encoding="utf-8") as f:
    src = f.read()
ast.parse(src)
print("syntax OK")
