# ==============================================================
# run_faceid_plusv2_eval.py — IP-Adapter FaceID PlusV2 升级评测（HANDOFF 35.4 P1）
# 背景：PLUS FACE 三轴配置优化全部证伪（recal-20260930），生产域 100% 拒绝率
#   根因为其场景叙事域身份保持能力边界；本脚本按同口径评测 FaceID PlusV2
#   （insightface 人脸嵌入注入 + 配套 lora 自动装配，官方推荐 512 身份保持路线）。
# 口径对齐：
#   离线域 = run_lora_plusface_combo 同参（4 漂移种子 25 步 euler/normal/cfg7/512，
#   PORTRAIT+DRIFT 提示词，insightface 余弦 vs hero_base）——可与 v2 组合基线
#   （combo w0.15 mean 0.8669 / min 0.778）直接对照；
#   生产域 = run_anchor_domain_recal 同参（生产分镜 2 镜 1024、种子 sid*7+1000、
#   负向 adapter 默认）——可与 PLUS FACE 基线（w0.15 mean 0.7423）直接对照。
# 前置：ip-adapter-faceid-plusv2_sd15.bin 在 models/ipadapter/、配套 lora 在
#   models/loras/（UnifiedLoaderFaceID 自动装配 lora_strength=0.6）、ComfyUI 在线。
# 运行：yyc3-ai-manju-studio/.venv/bin/python scripts/run_faceid_plusv2_eval.py
# ==============================================================
import argparse
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MANJU = REPO / "yyc3-ai-manju-studio"
sys.path.insert(0, str(MANJU / "backend"))
sys.path.insert(0, str(REPO / "scripts"))

from app.modules.consistency_engine.face_encoder import FaceEncoder  # noqa: E402 # pyright: ignore[reportMissingImports]
from run_lora_plusface_combo import (  # noqa: E402 # pyright: ignore[reportMissingImports]
    CKPT, DRIFT_SUFFIX, HERO, NEGATIVE, PORTRAIT, SEEDS, comfy_generate)
from run_anchor_domain_recal import prod_shots  # noqa: E402 # pyright: ignore[reportMissingImports]

OUT_DIR = Path("/tmp/kohya_out")
# 对照基线（历史留证：tc-m3-lora-v2-sweep / tc-anchor-recal-20260930）
BASELINES = {
    "plusface_prod_w015_mean": 0.7423,
    "plusface_offline_ipa_only_mean": 0.67,
    "combo_v2_offline_w015_mean": 0.8669,
    "combo_v2_offline_w015_min": 0.778,
    "no_anchor_mean": 0.5157,
}
# 官方 FaceID 工作流默认（examples/ipadapter_faceid.json）：
# weight_type=linear / combine_embeds=concat / embeds_scaling=V only / end_at=1.0


def build_faceid_workflow(prompt: str, negative: str, seed: int,
                          width: int, height: int,
                          weight: float, weight_faceidv2: float) -> dict:
    """FaceID PlusV2 工作流（采样器与 adapter 生产工作流逐参一致）。"""
    return {
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": CKPT}},
        # UnifiedLoaderFaceID：加载 FaceID 模型 + 自动装配配套 lora（0.6 官方推荐）
        "10": {"class_type": "IPAdapterUnifiedLoaderFaceID", "inputs": {
            "model": ["4", 0], "preset": "FACEID PLUS V2",
            "lora_strength": 0.6, "provider": "CPU"}},
        "11": {"class_type": "LoadImage", "inputs": {"image": HERO.name}},
        "12": {"class_type": "IPAdapterFaceID", "inputs": {
            "model": ["10", 0], "ipadapter": ["10", 1], "image": ["11", 0],
            "weight": weight, "weight_faceidv2": weight_faceidv2,
            "weight_type": "linear", "combine_embeds": "concat",
            "start_at": 0.0, "end_at": 1.0, "embeds_scaling": "V only"}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {
            "width": width, "height": height, "batch_size": 1}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {
            "text": prompt, "clip": ["4", 1]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {
            "text": negative, "clip": ["4", 1]}},
        "3": {"class_type": "KSampler", "inputs": {
            "seed": seed, "steps": 25, "cfg": 7.0,
            "sampler_name": "euler", "scheduler": "normal", "denoise": 1.0,
            "model": ["12", 0], "positive": ["6", 0],
            "negative": ["7", 0], "latent_image": ["5", 0]}},
        "8": {"class_type": "VAEDecode", "inputs": {
            "samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {
            "images": ["8", 0], "filename_prefix": "yyc3/faceid_v2"}},
    }


def gen_score(enc, ref, tag: str, prompt: str, negative: str, seed: int,
              width: int, height: int, weight: float, fv2: float) -> dict:
    out = OUT_DIR / f"faceid_v2_{tag}.png"
    t0 = time.perf_counter()
    comfy_generate(build_faceid_workflow(prompt, negative, seed, width, height,
                                         weight, fv2), out, timeout=1500)
    dt = round(time.perf_counter() - t0, 1)
    f = enc.extract_feature(str(out))
    sim = None if f is None else round(float(ref @ f), 4)
    print(f"[faceid-v2] {tag}: sim={sim} mode={enc.last_mode}  [{dt}s]",
          flush=True)
    return {"cell": tag, "sim": sim, "mode": enc.last_mode, "latency_s": dt}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline-weights", default="0.6,0.8,1.0",
                    help="离线域 weight 扫描（逗号分隔；weight_faceidv2 固定 1.0）")
    ap.add_argument("--prod-weight", type=float, default=0.8,
                    help="生产域采用配置（默认取离线最优前预置 0.8）")
    ap.add_argument("--skip-offline", action="store_true")
    ap.add_argument("--skip-prod", action="store_true")
    ap.add_argument("--out", default=str(OUT_DIR / "faceid_v2_report.json"))
    args = ap.parse_args()

    enc = FaceEncoder(library_root=str(MANJU / "backend" / "face_library_sd"))
    ref = enc.extract_feature(str(HERO))
    assert enc.last_mode == "insightface", "参考特征必须真实模型提取"

    rows = []
    # ── 离线域：weight 扫描 × 4 漂移种子（512，与 combo 基线同参）──
    if not args.skip_offline:
        for w in (float(x) for x in args.offline_weights.split(",")):
            for s in SEEDS:
                rows.append(gen_score(
                    enc, ref, f"off_w{int(w * 100):03d}_s{s}",
                    PORTRAIT + DRIFT_SUFFIX, NEGATIVE, s, 512, 512, w, 1.0))

    # ── 生产域：生产分镜 2 镜 @1024（与 recal 基线同参）──
    if not args.skip_prod:
        for sh in prod_shots():
            sid = sh["shot_id"]
            seed = int(sid.split("-")[-1]) * 7 + 1000
            from run_batch_shots import REF_STYLE
            rows.append(gen_score(
                enc, ref, f"prod_w{int(args.prod_weight * 100):03d}_{sid}",
                f"{REF_STYLE}, {sh['description']}",
                "低质量、变形、多余手指、水印", seed, 1024, 1024,
                args.prod_weight, 1.0))

    def cells(prefix):
        vals = [r["sim"] for r in rows
                if r["cell"].startswith(prefix) and r["sim"] is not None]
        return round(sum(vals) / len(vals), 4) if vals else None

    sweep = {f"w{int(w * 100):03d}": cells(f"off_w{int(w * 100):03d}_")
             for w in (float(x) for x in args.offline_weights.split(","))}
    report = {
        "testcase": "TC-M3-升级 FaceID PlusV2 双域同口径评测（35.4 P1）",
        "config": {"preset": "FACEID PLUS V2", "lora_strength": 0.6,
                   "weight_faceidv2": 1.0, "weight_type": "linear",
                   "embeds_scaling": "V only", "end_at": 1.0},
        "rows": rows,
        "offline_means": sweep,
        "prod_mean": cells("prod_"),
        "baselines": BASELINES,
        "target": "生产域 mean >= 0.85（PLUS FACE 基线 0.7423）",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    print(json.dumps({k: report[k] for k in
                      ("offline_means", "prod_mean", "baselines")},
                     ensure_ascii=False, indent=2))
    Path(args.out).write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[faceid-v2] 报告已落盘 {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
