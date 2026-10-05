# ==============================================================
# run_sdxl_prod_domain_reval.py — SDXL 阶段 3① 生产域复验（G4 §三十二前置）
# 背景：SD15 生产 1024 场景域拒绝率 100%（纯 IPA w0.15 基线 0.7793/0.7053，
#   mean 0.7423，G4 §二十 tc-anchor-recal 实证）；阶段 2 离线冠军
#   lora0.6×iid0.6（mean 0.9324/min 0.9265）须过「场景叙事 prompt 域」
#   复验方可接线生产（评测先行纪律，faceid 档先例）。
# 口径：与 SD15 生产链同参——分镜 prompt = REF_STYLE + shot.description
#   （run_batch_shots 单一事实源）、镜头稳定种子 sid*7+1000、1024、
#   insightface 512 维余弦 vs hero_base.png 设定图本体；
#   采样档 = Lightning（steps8/cfg1.8/sgm_uniform，阶段 1/2 同参）。
# 门槛：生产判定 per-shot ≥ 0.85（anchor_guard accept 线，SD15 时代从未达标）
# 运行：yyc3-ai-manju-studio/.venv/bin/python scripts/run_sdxl_prod_domain_reval.py \
#   [--lora sd-hero-xl-v1.safetensors] [--lora-s 0.6] [--iid-w 0.6] [--out x.json]
# ==============================================================
import argparse
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MANJU = REPO / "yyc3-ai-manju-studio"
SCRIPT_ENGINE = MANJU / "backend" / "app" / "modules" / "script_engine"
sys.path.insert(0, str(MANJU / "backend"))
sys.path.insert(0, str(SCRIPT_ENGINE))
sys.path.insert(0, str(REPO / "scripts"))

from run_batch_shots import NOVEL, REF_STYLE  # type: ignore # noqa: E402 生产 prompt 单一事实源
from run_sdxl_combo_sweep import (  # type: ignore # noqa: E402
    CKPT, HERO, comfy_generate)
from app.modules.consistency_engine.face_encoder import FaceEncoder  # type: ignore # noqa: E402
from splitter import split_chapters  # type: ignore # noqa: E402
from episode_planner import plan_episodes  # type: ignore # noqa: E402
from extractor import extract_elements  # type: ignore # noqa: E402
from storyboard_schema import draft_storyboard  # type: ignore # noqa: E402

OUT_DIR = Path("/tmp/sdxl_prod")
GATE_PER_SHOT = 0.85  # anchor_guard accept 线（生产判定）
CTRL_BASELINE = {"source": "SD15 纯 IPA w0.15 @1024（combo-ctrl-001/recal 留证）",
                 "shot-ep01-001": 0.7793, "shot-ep01-002": 0.7053, "mean": 0.7423}
# 稳定性补测种子（生产 sid-seed 主口径之外的双种户证）
EXTRA_SEEDS = [42]


def build_prod_workflow(prompt: str, seed: int, lora: str, lora_s: float,
                        iid_w: float) -> dict:
    """SDXL 生产域工作流——与阶段 2 扫描同构，仅 prompt 换生产场景叙事源。"""
    return {
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": CKPT}},
        "13": {"class_type": "LoraLoader", "inputs": {
            "lora_name": lora, "strength_model": lora_s, "strength_clip": lora_s,
            "model": ["4", 0], "clip": ["4", 1]}},
        "31": {"class_type": "InstantIDModelLoader",
               "inputs": {"instantid_file": "ip-adapter.bin"}},
        "38": {"class_type": "InstantIDFaceAnalysis", "inputs": {"provider": "CPU"}},
        "16": {"class_type": "ControlNetLoader",
               "inputs": {"control_net_name": "instantid/controlnet.safetensors"}},
        "13i": {"class_type": "LoadImage", "inputs": {"image": HERO.name}},
        "5": {"class_type": "EmptyLatentImage",
              "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
        "39": {"class_type": "CLIPTextEncode",
               "inputs": {"text": prompt, "clip": ["13", 1]}},
        "40": {"class_type": "CLIPTextEncode",
               "inputs": {"text": "低质量、变形、多余手指、水印", "clip": ["13", 1]}},
        "60": {"class_type": "ApplyInstantID", "inputs": {
            "instantid": ["31", 0], "insightface": ["38", 0],
            "control_net": ["16", 0], "image": ["13i", 0], "model": ["13", 0],
            "positive": ["39", 0], "negative": ["40", 0],
            "weight": iid_w, "start_at": 0.0, "end_at": 1.0}},
        "3": {"class_type": "KSampler", "inputs": {
            "seed": seed, "steps": 8, "cfg": 1.8,
            "sampler_name": "euler", "scheduler": "sgm_uniform", "denoise": 1.0,
            "model": ["60", 0], "positive": ["60", 1],
            "negative": ["60", 2], "latent_image": ["5", 0]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {
            "images": ["8", 0], "filename_prefix": "yyc3/sdxl_prod"}},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lora", default="sd-hero-xl-v1.safetensors")
    ap.add_argument("--lora-s", type=float, default=0.6, help="冠军档 LoRA 强度")
    ap.add_argument("--iid-w", type=float, default=0.6, help="冠军档 InstantID 权重")
    ap.add_argument("--out", default=None)
    ap.add_argument("--reuse", action="store_true")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    enc = FaceEncoder(library_root=str(MANJU / "backend" / "face_library_sd"))
    ref = enc.extract_feature(str(HERO))
    assert enc.last_mode == "insightface", "参考特征必须真实模型提取"

    # 生产分镜（与 run_anchor_domain_recal 同链，可直接对照 SD15 基线）
    els = extract_elements(NOVEL)
    eps = plan_episodes(split_chapters(NOVEL))
    sb = draft_storyboard("sdxl-prod-reval", eps[0], els, trace_id="trace-SDXLPROD-EP01")
    shots = sb["shots"][:2]
    print(f"[prod-reval] 生产分镜 {[s['shot_id'] for s in shots]} · "
          f"冠军档 lora={args.lora} s={args.lora_s} × iid={args.iid_w}")

    rows = []
    for s in shots:
        sid = s["shot_id"]
        sid_seed = int(sid.split("-")[-1]) * 7 + 1000  # 生产稳定种子（主口径）
        for tag, seed in [("sid", sid_seed)] + [(f"s{x}", x) for x in EXTRA_SEEDS]:
            out = OUT_DIR / f"prod_{sid}_{tag}.png"
            if args.reuse and out.exists():
                dt = 0.0
            else:
                t0 = time.perf_counter()
                comfy_generate(build_prod_workflow(
                    f"{REF_STYLE}, {s['description']}", seed,
                    args.lora, args.lora_s, args.iid_w), out)
                dt = round(time.perf_counter() - t0, 1)
            f = enc.extract_feature(str(out))
            sim = None if f is None else round(float(ref @ f), 4)
            rows.append({"shot": sid, "seed_tag": tag, "seed": seed,
                         "sim": sim, "mode": enc.last_mode, "latency_s": dt})
            print(f"[prod-reval] {sid}/{tag} seed={seed} sim={sim}  [{dt}s]")

    primary = [r for r in rows if r["seed_tag"] == "sid"]
    extra = [r for r in rows if r["seed_tag"] != "sid"]
    sims_p = [r["sim"] for r in primary if r["sim"] is not None]
    report = {
        "testcase": "SDXL 阶段 3① 生产域复验（场景叙事 prompt @1024，Lightning 档）",
        "config": {"ckpt": CKPT, "lora": args.lora, "lora_strength": args.lora_s,
                   "instantid_weight": args.iid_w,
                   "sampling": "steps8/cfg1.8/euler+sgm_uniform/1024"},
        "rows": rows,
        "primary_sid_seed": {"sims": sims_p,
                             "mean": round(sum(sims_p) / len(sims_p), 4) if sims_p else None,
                             "min": min(sims_p) if sims_p else None},
        "extra_seeds_stability": {"sims": [r["sim"] for r in extra]},
        "baseline": CTRL_BASELINE,
        "gate_per_shot_ge_0.85": bool(sims_p and all(v >= GATE_PER_SHOT for v in sims_p)),
        "production_wiring_unlocked": bool(sims_p and all(v >= GATE_PER_SHOT for v in sims_p)),
    }
    print(json.dumps({k: report[k] for k in
                      ("primary_sid_seed", "baseline", "gate_per_shot_ge_0.85",
                       "production_wiring_unlocked")}, ensure_ascii=False, indent=2))
    if args.out:
        Path(args.out).write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
