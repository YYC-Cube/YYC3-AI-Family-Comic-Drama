# ==============================================================
# run_anchor_domain_recal.py — 生产域锚定再校准（HANDOFF 34.4 P1）
# 背景：生产 1024 场景域拒绝率 100%（历史 9/9 + 本轮 4/4 双证），离线 512
#   肖像域指标不可外推。三轴校准（纯 IPA 链，无 LoRA——combo 生产域负交互
#   已证伪）：
#   轴A 权重窗：w ∈ {0.50, 0.85, 1.00} × 生产分镜 2 镜 @1024
#       （w0.15 基线复用 combo-ctrl-001 manifest 实测 0.7793/0.7053）
#   轴B 构图约束：权重窗最优 w + 肖像构图后缀 × 2 镜 @1024
#   轴C 分辨率衰减：同 w 同 seed 512 vs 1024 对照（量化分布偏移）
# 口径：生产链同参——drama_stage_adapter 工作流（1024 默认、负向空）、
#   分镜 prompt = REF_STYLE + shot.description、镜头稳定种子 sid*7+1000、
#   insightface 512 维余弦 vs hero_base.png。
# 运行：yyc3-ai-manju-studio/.venv/bin/python scripts/run_anchor_domain_recal.py \
#   --out /tmp/kohya_out/recal_report.json
# ==============================================================
import argparse
import json
import os
import sys
import time
from pathlib import Path

# 单镜超时提额：1024 场景域实测最长 ~15 分钟（首战 900s 触发超时中断，续跑防复发）
os.environ.setdefault("COMFYUI_TIMEOUT", "1800")

REPO = Path(__file__).resolve().parents[1]
MANJU = REPO / "yyc3-ai-manju-studio"
COMPONENTS = REPO / "yyc3-ai-agent-archive" / "components"
SCRIPT_ENGINE = MANJU / "backend" / "app" / "modules" / "script_engine"
LIBRARY = MANJU / "backend" / "face_library_sd"

import types  # noqa: E402
_m = types.ModuleType("milvus_retriever")


class _S:
    def __init__(self, *_args, **_kwargs):
        pass

    def search(self, *_args, **_kwargs):
        raise ConnectionError("stub")


setattr(_m, "MilvusRetriever", _S)
sys.modules["milvus_retriever"] = _m
for p in (COMPONENTS, MANJU / "backend", SCRIPT_ENGINE):
    sys.path.insert(0, str(p))

from drama_stage_adapter import DramaToolGateway  # type: ignore
from app.modules.consistency_engine.face_encoder import FaceEncoder  # type: ignore
from splitter import split_chapters  # type: ignore
from episode_planner import plan_episodes  # type: ignore
from extractor import extract_elements  # type: ignore
from storyboard_schema import draft_storyboard  # type: ignore
from run_batch_shots import NOVEL, REF_STYLE  # type: ignore  生产 prompt 单一事实源

HERO = Path("/tmp/comfy_out/hero_base.png")
OUT_DIR = Path("/tmp/kohya_out")
# 轴A 权重窗（w0.15 由 combo-ctrl-001 留证覆盖，不重跑）
WEIGHTS_A = [0.50, 0.85, 1.00]
# 轴B 构图约束后缀（降"场景叙事→肖像"分布偏移，负向保持空隔离变量）
COMPOSITION_SUFFIX = ", upper body portrait, facing viewer, centered composition"
SHOTS_N = 2  # 生产分镜取样镜头数（与 combo-ctrl-001 同两镜可直接对照）
CTRL_BASELINE = {"source": "combo-ctrl-001 manifest（纯 IPA w0.15 @1024）",
                 "shot-ep01-001": 0.7793, "shot-ep01-002": 0.7053}


def prod_shots():
    """重建生产分镜（与 run_batch_shots 同链同 seed 派生，保证可比性）。"""
    els = extract_elements(NOVEL)
    eps = plan_episodes(split_chapters(NOVEL))
    sb = draft_storyboard("anchor-recal", eps[0], els, trace_id="trace-RECAL-EP01")
    return sb["shots"][:SHOTS_N]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref-image", default="hero_base.png")
    ap.add_argument("--timeout", type=int, default=900, help="单镜生成超时（秒）")
    ap.add_argument("--out", default=str(OUT_DIR / "recal_report.json"))
    args = ap.parse_args()

    gw = DramaToolGateway()
    assert gw.comfy.enabled, "ComfyUI 未在线（localhost:41888）"
    enc = FaceEncoder(library_root=str(LIBRARY))
    ref = enc.extract_feature(str(HERO))
    assert enc.last_mode == "insightface", "参考特征必须真实模型提取"

    shots = prod_shots()
    print(f"[recal] 生产分镜取样 {len(shots)} 镜："
          f"{[s['shot_id'] for s in shots]}")

    def gen_and_score(tag: str, prompt: str, seed: int, weight: float,
                      width: int, height: int) -> dict:
        out = OUT_DIR / f"recal_{tag}.png"
        # 可续跑：已有产物直接评分（首战 6/10 中断，不重复占用产线）
        if out.exists() and out.stat().st_size > 0:
            f = enc.extract_feature(str(out))
            sim = None if f is None else round(float(ref @ f), 4)
            print(f"[recal] {tag}: sim={sim}（续跑复用已有产物）")
            return {"cell": tag, "sim": sim, "mode": enc.last_mode,
                    "latency_s": None, "reused": True}
        t0 = time.perf_counter()
        try:
            r = gw.comfy.generate_image(prompt, str(out), width=width,
                                        height=height, seed=seed,
                                        ref_image=args.ref_image,
                                        lora=None, ipa_weight=weight)
            assert r.get("status") == "ok", f"生成失败：{r}"
        except Exception as e:  # noqa: BLE001  单镜失败记录不中断（网格完整性优先）
            print(f"[recal] {tag}: 生成异常 {e}")
            return {"cell": tag, "sim": None, "mode": "error",
                    "latency_s": round(time.perf_counter() - t0, 1),
                    "error": str(e)[:160]}
        dt = round(time.perf_counter() - t0, 1)
        f = enc.extract_feature(str(out))
        sim = None if f is None else round(float(ref @ f), 4)
        print(f"[recal] {tag}: sim={sim} mode={enc.last_mode}  [{dt}s]", flush=True)
        return {"cell": tag, "sim": sim, "mode": enc.last_mode, "latency_s": dt}

    rows = []
    # 轴A：纯 IPA 权重窗 @1024（生产原生分辨率）
    for w in WEIGHTS_A:
        for s in shots:
            sid = s["shot_id"]
            seed = int(sid.split("-")[-1]) * 7 + 1000
            rows.append(gen_and_score(
                f"w{int(w * 100):03d}_{sid}", f"{REF_STYLE}, {s['description']}",
                seed, w, 1024, 1024))

    # 轴A 判定：均值最优权重
    def w_mean(w):
        vals = [r["sim"] for r in rows
                if r["cell"].startswith(f"w{int(w * 100):03d}_")
                and r["sim"] is not None]
        return sum(vals) / len(vals) if vals else 0.0

    ctrl_mean = (CTRL_BASELINE["shot-ep01-001"]
                 + CTRL_BASELINE["shot-ep01-002"]) / 2
    best_w = max(WEIGHTS_A, key=w_mean)
    best_mean = w_mean(best_w)
    print(f"[recal] 轴A 最优权重 w={best_w}（mean {best_mean:.4f}）；"
          f"对照 w0.15 ctrl={ctrl_mean:.4f}")

    # 轴B：构图约束（最优权重 vs w0.15 双测，隔离"约束×权重"交互）
    b_weights = sorted({0.15, best_w})
    for w in b_weights:
        for s in shots:
            sid = s["shot_id"]
            seed = int(sid.split("-")[-1]) * 7 + 1000
            rows.append(gen_and_score(
                f"comp_w{int(w * 100):03d}_{sid}",
                f"{REF_STYLE}{COMPOSITION_SUFFIX}, {s['description']}",
                seed, w, 1024, 1024))

    # 轴C：分辨率衰减（w0.15 同 seed 512 对照，量化 512→1024 偏移）
    for s in shots:
        sid = s["shot_id"]
        seed = int(sid.split("-")[-1]) * 7 + 1000
        rows.append(gen_and_score(
            f"res512_{sid}", f"{REF_STYLE}, {s['description']}",
            seed, 0.15, 512, 512))

    def cells(prefix):
        return {r["cell"].split("_", 1)[1]: r["sim"] for r in rows
                if r["cell"].startswith(prefix)}

    comp_best = cells(f"comp_w{int(best_w * 100):03d}_")
    comp_015 = cells("comp_w015_")
    res512 = cells("res512_")

    def mean_of(d):
        vals = [v for v in d.values() if v is not None]
        return round(sum(vals) / len(vals), 4) if vals else None

    mean_512 = mean_of(res512)

    report = {
        "testcase": "TC-G5-预研 生产域锚定再校准（HANDOFF 34.4 P1，纯 IPA 三轴）",
        "protocol": "生产链同参（adapter 工作流 1024/负向空/分镜 prompt/种子 sid*7+1000），"
                    "insightface 余弦 vs hero_base.png，2 生产镜头",
        "axis_a_weight_window": {
            "w015_ctrl_manifest": CTRL_BASELINE, "w050": cells("w050_"),
            "w085": cells("w085_"), "w100": cells("w100_"),
            "means": {"w0.15": ctrl_mean, "w0.50": w_mean(0.50),
                      "w0.85": w_mean(0.85), "w1.00": w_mean(1.00)},
            "best_w": best_w},
        "axis_b_composition": {
            "suffix": COMPOSITION_SUFFIX,
            f"comp_w{int(best_w * 100):03d}": comp_best, "comp_w015": comp_015,
            "means": {f"w{best_w}": mean_of(comp_best), "w0.15": mean_of(comp_015)}},
        "axis_c_resolution_decay": {
            "res512_w015": res512, "res1024_w015_ctrl": CTRL_BASELINE,
            "mean_512": mean_512, "mean_1024": ctrl_mean,
            "decay": None if mean_512 is None
            else round(ctrl_mean - mean_512, 4)},
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    Path(args.out).write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[recal] 报告已落盘 {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
