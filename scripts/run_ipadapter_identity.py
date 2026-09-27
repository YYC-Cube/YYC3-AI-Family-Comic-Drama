# ==============================================================
# run_ipadapter_identity.py — IPAdapter 身份锚定实验（M3 主线 · ①b）
# 问题：无锚定跨种子漂移 0.44-0.57（G3 v1.3）；IPAdapter PLUS FACE 能否
#       免训练拉到 0.85+？
# 设计：hero_base.png 为 IP 设定图（ComfyUI/input/ + 特征库参考）；
#       4 个漂移种子（与 v1.3 同种子集）× IPAdapter 锚定生成 → post_check
# 对照：v1.3 无锚定同种子集 0.4418/0.5306/0.5216/0.5687
# 运行：COMFYUI_MODEL=DreamShaper_8_pruned.safetensors \
#       yyc3-ai-manju-studio/.venv/bin/python scripts/run_ipadapter_identity.py
# ==============================================================
import json
import os
import shutil
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MANJU = REPO / "yyc3-ai-manju-studio"
COMPONENTS = REPO / "yyc3-ai-agent-archive" / "components"
LIBRARY = MANJU / "backend" / "face_library_sd"
OUT = Path("/tmp/comfy_out")

os.environ.setdefault("COMFYUI_URL", "http://localhost:41888")
os.environ.setdefault("COMFYUI_MODEL", "DreamShaper_8_pruned.safetensors")
os.environ.setdefault("COMFYUI_TIMEOUT", "900")

import types  # noqa: E402
_m = types.ModuleType("milvus_retriever")


class _S:
    def __init__(self, *a, **k):
        pass

    def search(self, *a, **k):
        raise ConnectionError("stub")


_m.MilvusRetriever = _S
sys.modules["milvus_retriever"] = _m
sys.path.insert(0, str(COMPONENTS))
sys.path.insert(0, str(MANJU / "backend"))

from drama_stage_adapter import DramaToolGateway  # noqa: E402
from app.modules.consistency_engine.face_encoder import FaceEncoder  # noqa: E402
from app.modules.consistency_engine.anchor_guard import AnchorGuard  # noqa: E402

PORTRAIT = ("portrait of a young chinese wuxia heroine, delicate face, "
            "ancient hanfu, ink wash background, upper body, highly detailed")
DRIFT_SUFFIX = ", smiling, night lantern lighting, different angle"
SEEDS = [777, 888, 999, 1111]
BASELINE = {777: 0.4418, 888: 0.5306, 999: 0.5216, 1111: 0.5687}


def main():
    gw = DramaToolGateway()
    assert gw.comfy.enabled

    enc = FaceEncoder(library_root=str(LIBRARY))
    if not (LIBRARY / "sd-hero" / "feature.npy").exists():
        shutil.rmtree(LIBRARY, ignore_errors=True)
        enc.save_character("sd-hero", "sd-hero", "/tmp/comfy_out/hero_base.png")
    guard = AnchorGuard(library_root=str(LIBRARY))

    rows = []
    for s in SEEDS:
        out = OUT / f"ipad_{s}.png"
        t0 = time.perf_counter()
        r = gw.text_to_image(PORTRAIT + DRIFT_SUFFIX, ref_assets=["sd-hero"],
                             out_path=str(out), seed=s, ref_image="hero_base.png")
        dt = round(time.perf_counter() - t0, 1)
        assert r["status"] == "ok", f"生成失败：{r}"
        c = guard.post_check("sd-hero", str(out), attempts=1)
        rows.append({"seed": s, "sim": c.get("similarity"), "action": c["action"],
                     "baseline_no_ipadapter": BASELINE[s], "latency_s": dt})
        print(f"seed={s}: sim={c.get('similarity')}（无锚定 {BASELINE[s]}）"
              f" → {c['action']}  [{dt}s]")

    sims = [r["sim"] for r in rows if r["sim"] is not None]
    report = {
        "rows": rows,
        "ipadapter_min": min(sims), "ipadapter_max": max(sims),
        "ipadapter_mean": round(sum(sims) / len(sims), 4),
        "baseline_mean": round(sum(BASELINE.values()) / 4, 4),
        "gain": round(sum(sims) / len(sims) - sum(BASELINE.values()) / 4, 4),
        "target_ge_0.85": min(sims) >= 0.85,
        "latency_note": "含 IPAdapter 加载与 25 步采样（MPS）",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    Path("/tmp/ipadapter_identity.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
