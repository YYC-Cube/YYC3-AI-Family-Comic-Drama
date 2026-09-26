# ==============================================================
# run_comfy_real.py — 真实 ComfyUI 生成本体联调（替换 Mock）+ TC-G3-006 耗时基线
#                      + SD 漂移分布标定（真实角色素材集 ③）
# 前置：ComfyUI 已启动（默认 http://localhost:41888，模型 dreamshaper_8）
# 链路：seed 锁定建库 → 身份锁定重生成（accept）→ 漂移种子（redraw→锁定重绘 accept）
# 运行：yyc3-ai-manju-studio/.venv/bin/python scripts/run_comfy_real.py
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
os.environ.setdefault("COMFYUI_MODEL", "dreamshaper_8.safetensors")
os.environ.setdefault("COMFYUI_TIMEOUT", "600")

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

SEED_BASE = 42          # 角色 IP 锁定种子
SEEDS_DRIFT = [777, 888, 999, 1111]


def gen(gw, seed, prompt=PORTRAIT, name="gen", w=512, h=512):
    """生成 + 计时（TC-G3-006 基线口径：提交→取回全墙钟）"""
    out = OUT / f"{name}.png"
    t0 = time.perf_counter()
    r = gw.text_to_image(prompt, ref_assets=["sd-hero"], out_path=str(out),
                         seed=seed)
    dt = time.perf_counter() - t0
    assert r["status"] == "ok", f"生成失败：{r}"
    return str(out), round(dt, 1)


def main():
    OUT.mkdir(exist_ok=True)
    gw = DramaToolGateway()
    assert gw.comfy.enabled, "COMFYUI_URL 未配置"

    enc = FaceEncoder(library_root=str(LIBRARY))
    if LIBRARY.exists():
        shutil.rmtree(LIBRARY)

    results = {"latency_s": {}, "sims": {}, "chain": []}

    # ── 角色 IP 素材：seed=42 建库（真实 SD 产物即角色设定图）──
    base_path, dt = gen(gw, SEED_BASE, name="hero_base")
    results["latency_s"]["base"] = dt
    enc.save_character("sd-hero", "sd-hero", base_path)
    guard = AnchorGuard(library_root=str(LIBRARY))
    assert guard.encoder.mode == "insightface"

    # ── A. 身份锁定重生成（同种子同图 → 应 ACCEPT）──
    regen_path, dt = gen(gw, SEED_BASE, name="hero_regen")
    results["latency_s"]["regen_locked"] = dt
    chk = guard.post_check("sd-hero", regen_path, attempts=1)
    results["chain"].append({"case": "身份锁定重生成(seed=42)",
                             "sim": chk.get("similarity"), "action": chk["action"]})

    # ── B. 漂移种子（身份漂移 → 应 REDRAW；随后锁定重绘 → ACCEPT）──
    drift_path, dt = gen(gw, 777, prompt=PORTRAIT + DRIFT_SUFFIX, name="hero_drift")
    results["latency_s"]["drift_gen"] = dt
    chk2 = guard.post_check("sd-hero", drift_path, attempts=1)
    results["chain"].append({"case": "漂移种子(seed=777+变体提示词)",
                             "sim": chk2.get("similarity"), "action": chk2["action"]})
    if chk2["action"] == "redraw":
        lock_path, dt = gen(gw, SEED_BASE, name="hero_relock")
        results["latency_s"]["relock"] = dt
        chk3 = guard.post_check("sd-hero", lock_path, attempts=2)
        results["chain"].append({"case": "锁定重绘(seed=42)",
                                 "sim": chk3.get("similarity"), "action": chk3["action"]})

    # ── C. SD 漂移分布标定（无 LoRA 基线，③真实素材集）──
    for sd_ in SEEDS_DRIFT:
        p, dt = gen(gw, sd_, prompt=PORTRAIT + DRIFT_SUFFIX, name=f"drift_{sd_}")
        results["latency_s"][f"drift_{sd_}"] = dt
        c = guard.post_check("sd-hero", p, attempts=1)
        results["sims"][f"seed_{sd_}"] = c.get("similarity")

    # ── 判定 ──
    a_ok = results["chain"][0]["action"] == "accept"
    b_redraw = results["chain"][1]["action"] in ("redraw", "escalate")
    b_close = len(results["chain"]) < 3 or results["chain"][-1]["action"] == "accept"
    drift_sims = [v for v in results["sims"].values() if v is not None]
    lat = [v for v in results["latency_s"].values()]
    results["checks"] = {
        "身份锁定重生成 ACCEPT": a_ok,
        "漂移种子被检出（redraw/escalate）": b_redraw,
        "打回后锁定重绘收束 ACCEPT": b_close,
        "TC-G3-006 Mac 预览基线（单镜 ≤120s）": max(lat) <= 120,
    }
    results["g3_006"] = {"max_s": max(lat), "min_s": min(lat),
                         "target": "Mac 预览 ≤120s（YYC3-06 §4.1）；DGX NF4 ≤300s 待硬件"}
    results["drift_distribution"] = {
        "min": min(drift_sims) if drift_sims else None,
        "max": max(drift_sims) if drift_sims else None,
        "note": "无 LoRA/IPAdapter 的同提示词跨种子漂移分布（真实 SD）"}

    ok = all(results["checks"].values())
    for k, v in results["checks"].items():
        print(f"  {'PASS' if v else 'FAIL'}  {k}")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    Path("/tmp/comfy_real_results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
