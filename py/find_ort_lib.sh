#!/bin/bash
# 定位 pip onnxruntime C 库
P=$(pip3 show onnxruntime 2>/dev/null | grep Location | awk '{print $2}')
echo "LOC=$P"
if [ -z "$P" ]; then
  P=$(find /usr/lib/python3/dist-packages /usr/local/lib/python3* -maxdepth 1 -name "onnxruntime*" -type d 2>/dev/null | head -1)
  echo "FALLBACK=$P"
fi
ls -la "$P/onnxruntime/capi/" 2>/dev/null | head -12
