#!/usr/bin/env python3
"""
VCMI 战略 AI — WIN RATE 结果中枢 (172.16.2.40:8088)
接收 WSL2 训练侧推送的新模型评测结果, 落地为可查询历史, 供一处查看"每轮训练新模型 WIN RATE".

与 :8080 推理服务解耦:
  - :8080 = 模型加载 / 推理 (SB3/ONNX, 旧架构 256 维)
  - :8088 = WIN RATE 评测历史中枢 (新架构 3464+terrain 模型在 WSL2 跑完回传)

API:
  GET  /health            -> {"status":"ok","count":N}
  POST /results           -> 接收一条评测结果 JSON, 追加到历史 + 落盘 jsonl, 返回 {"ok":true,"id":N}
  GET  /results           -> 最近 N 条 (默认 50)
  GET  /results/latest    -> 最新一条 (含 win_rate / games / ts / model)
  GET  /results/<model>   -> 某模型的所有历史条 (按 ts 升序)

落盘: /DATA/hero3/output/winrate_history.jsonl  (每行一条)
内存: 全量驻留 (评测条数有限, 可接受)
"""
import os
import json
import time
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

OUTPUT_DIR = "/DATA/hero3/output"
HISTORY_FILE = os.path.join(OUTPUT_DIR, "winrate_history.jsonl")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---- 内存历史 (进程重启后从 jsonl 恢复) ----
HISTORY: List[Dict[str, Any]] = []


def _load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        HISTORY.append(json.loads(line))
                    except Exception:
                        pass
        except Exception:
            pass


_load_history()

app = FastAPI(title="VCMI WIN RATE Hub", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "count": len(HISTORY)}


@app.post("/results")
async def post_result(payload: Dict[str, Any]):
    # 基本字段校验
    required = ("model", "win_rate")
    for k in required:
        if k not in payload:
            raise HTTPException(400, f"missing field: {k}")
    rec = dict(payload)
    rec.setdefault("ts", time.strftime("%Y-%m-%dT%H:%M:%S"))
    rec.setdefault("games", 0)
    rec.setdefault("wins", 0)
    rec.setdefault("losses", 0)
    rec.setdefault("draws", 0)
    rec.setdefault("errors", 0)
    rec.setdefault("maps", [])
    rec.setdefault("blue", "MMAI_RANDOM")
    rec["_id"] = len(HISTORY) + 1
    HISTORY.append(rec)
    # 落盘
    try:
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
    except Exception as e:
        # 落盘失败不影响内存, 但记录
        rec["_write_err"] = str(e)
    return {"ok": True, "id": rec["_id"]}


@app.get("/results")
async def list_results(limit: int = 50):
    return HISTORY[-limit:]


@app.get("/results/latest")
async def latest_result():
    if not HISTORY:
        raise HTTPException(404, "no results yet")
    return HISTORY[-1]


@app.get("/results/{model}")
async def model_results(model: str):
    out = [r for r in HISTORY if r.get("model") == model]
    if not out:
        raise HTTPException(404, f"no results for model: {model}")
    return out


@app.get("/models")
async def list_models_with_results():
    """聚合: 每个模型最新一条结果"""
    latest_by_model: Dict[str, Dict] = {}
    for r in HISTORY:
        m = r.get("model")
        if m is None:
            continue
        cur = latest_by_model.get(m)
        if cur is None or r.get("ts", "") >= cur.get("ts", ""):
            latest_by_model[m] = r
    return list(latest_by_model.values())


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8088, workers=1)
