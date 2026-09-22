# -*- coding: utf-8 -*-
"""诊断证书图片质量并生成对比样张（仅诊断用，不覆盖原图）"""
import sys
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

SRC = r"D:\【工程项目】\【bak】\一造\造价工程师证书(1)\造价工程师证书_01 - 副本.jpg"
OUT = Path(__file__).parent / "cert_diag"
OUT.mkdir(exist_ok=True)

src = SRC
img = Image.open(src)
print(f"[原图] {img.size[0]}x{img.size[1]}, mode={img.mode}, bits={img.bits}")

# 1) 原图缩略图
thumb = img.copy()
thumb.thumbnail((600, 600))
thumb.save(OUT / "01_original_thumb.jpg", quality=90)

# 2) 自动对比度 (autocrop 后)
auto = ImageOps.autocontrast(img)
auto.thumbnail((600, 600))
auto.save(OUT / "02_autocontrast.jpg", quality=90)

# 3) 锐化 (UnsharpMask)
sharp = img.filter(ImageFilter.UnsharpMask(radius=2, percent=120, threshold=3))
sharp.thumbnail((600, 600))
sharp.save(OUT / "03_sharpened.jpg", quality=90)

# 4) 亮度+对比度+锐化 组合
combo = img
combo = ImageEnhance.Brightness(combo).enhance(1.05)
combo = ImageEnhance.Contrast(combo).enhance(1.15)
combo = ImageEnhance.Color(combo).enhance(1.1)
combo = combo.filter(ImageFilter.UnsharpMask(radius=2, percent=100, threshold=3))
combo.thumbnail((600, 600))
combo.save(OUT / "04_combo.jpg", quality=90)

# 5) 灰度（看是否彩色证书）
gray = img.convert("L")
gray.save(OUT / "05_gray_thumb.jpg", quality=90)

print(f"[完成] 样张已输出到 {OUT}")
print("  01_original_thumb.jpg   原图")
print("  02_autocontrast.jpg     自动对比度")
print("  03_sharpened.jpg        锐化")
print("  04_combo.jpg            亮度+对比度+彩色+锐化 组合")
print("  05_gray_thumb.jpg       灰度")
