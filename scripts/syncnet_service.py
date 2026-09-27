# ==============================================================
# syncnet_service.py — SyncNet 评分独立服务（M4 · OpenAI 风格内网服务）
# 后端：直接 import 上游 SyncNetInstance.evaluate（零上游改动、零 subprocess）
# 输入：POST /v1/sync/score {"clip_dir": "..."} → 对 crop_dir/*.avi 逐轨评分
#       （裁切轨由 run_pipeline.py 产脸裁切产出——编排侧经 runbook/bash 触发）
# 运行：yyc3-ai-manju-studio/.venv/bin/python scripts/syncnet_service.py
# 端口：42218（AI 服务 4xxxx 段）
# ==============================================================
import glob
import os
import sys
from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

SYNCNET_REPO = Path(os.getenv(
    "SYNCNET_REPO", "/Users/yanyu/YYC-Cube/tools/syncnet/syncnet_python"))
MODEL = os.getenv("SYNCNET_MODEL", "data/syncnet_v2.model")

app = FastAPI(title="YYC³ SyncNet Score Service")
_s = None


def get_scorer():
    global _s
    if _s is None:
        sys.path.insert(0, str(SYNCNET_REPO))
        os.chdir(SYNCNET_REPO)  # 上游内部相对路径（data/、tmp/）依赖 cwd
        from SyncNetInstance import SyncNetInstance
        _s = SyncNetInstance()
        _s.loadParameters(MODEL)
    return _s


class ScoreRequest(BaseModel):
    clip_dir: str
    batch_size: int = 32
    vshift: int = 15


@app.get("/healthz")
def healthz():
    return {"status": "ok", "backend": "syncnet_v2", "repo": str(SYNCNET_REPO)}


@app.post("/v1/sync/score")
def score(req: ScoreRequest):
    crop = Path(req.clip_dir)
    if not crop.is_dir():
        raise HTTPException(404, f"clip_dir 不存在：{req.clip_dir}")
    tracks = sorted(glob.glob(str(crop / "*.avi")))
    if not tracks:
        raise HTTPException(422, "clip_dir 内无 .avi 裁切轨（先跑 run_pipeline 裁切）")

    scorer = get_scorer()
    results = []
    for fname in tracks:
        opt = SimpleNamespace(  # 轻命名空间（上游 evaluate 仅用这几个属性）
            reference=crop.stem, tmp_dir="/tmp/syncnet_work/pytmp",
            work_dir="/tmp/syncnet_work/pywork",
            batch_size=req.batch_size, vshift=req.vshift)
        import numpy as _np
        offset, conf, dist = scorer.evaluate(opt, videofile=fname)
        f = lambda x: float(_np.asarray(x).reshape(-1)[0])  # noqa: E731
        conf_f = f(conf)
        results.append({
            "track": Path(fname).name, "offset": f(offset),
            "conf": round(conf_f, 4), "dist": round(f(dist), 4),
            "verdict": "达标(≥0.75)" if conf_f >= 0.75 else "打回(<0.75)",
        })
    passed = all(r["verdict"].startswith("达标") for r in results)
    return {"status": "ok", "passed": passed, "results": results}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1",
                port=int(os.getenv("SYNCNET_PORT", "42218")), log_level="warning")
