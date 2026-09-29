# ==============================================================
# run_lora_plusface_combo.py — LoRA + IPAdapter PLUS FACE 组合评测（M3 二轮 · k4）
# 路线：ComfyUI 工作流（LoraLoader + IPAdapterUnifiedLoader PLUS FACE 脸区域
#   嵌入）——一轮实证 diffusers 整图路线与漂移提示词冲突（0.6→0.5443 /
#   1.0→0.1964），历史 0.670 基线即本工作流路线，组合归因必须同路线。
# 口径：与 run_ipadapter_identity.py 一致——4 漂移种子 × 25 步采样
#   （euler/normal/cfg7/512），insightface 512 维余弦 vs hero_base。
# 前置：sd-hero-v2.safetensors 已拷 ComfyUI/models/loras/；hero_base.png
#   已在 ComfyUI/input/；ComfyUI 服务 localhost:41888。
# 运行：
#   yyc3-ai-manju-studio/.venv/bin/python scripts/run_lora_plusface_combo.py \
#     --lora sd-hero-v2.safetensors --weight 0.85
# ==============================================================
import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MANJU = REPO / "yyc3-ai-manju-studio"
sys.path.insert(0, str(MANJU / "backend"))

from app.modules.consistency_engine.face_encoder import FaceEncoder  # noqa: E402 # pyright: ignore[reportMissingImports]

COMFYUI_URL = "http://localhost:41888"
CKPT = "DreamShaper_8_pruned.safetensors"
PORTRAIT = ("portrait of a young chinese wuxia heroine, delicate face, "
            "ancient hanfu, ink wash background, upper body, highly detailed")
DRIFT_SUFFIX = ", smiling, night lantern lighting, different angle"
NEGATIVE = "低质量、变形、多余手指、水印"
SEEDS = [777, 888, 999, 1111]
HERO = Path("/tmp/comfy_out/hero_base.png")

# 基线（见 tc-m3-lora-crosseed-eval.json / G4 首验记录）
BASELINES = {"no_anchor_mean": 0.5157, "lora_only_v1_best_mean": 0.6441,
             "ipadapter_only_plusface_mean": 0.67}


def build_workflow(prompt: str, seed: int, lora: str, weight: float) -> dict:
    """LoRA + PLUS FACE 组合工作流（KSampler 25 步与历史基线同参）。"""
    return {
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": CKPT}},
        # LoRA：二轮训练产物（KSampler 与 CLIP 编码均注入）
        "13": {"class_type": "LoraLoader", "inputs": {
            "lora_name": lora, "strength_model": 1.0, "strength_clip": 1.0,
            "model": ["4", 0], "clip": ["4", 1]}},
        # PLUS FACE：脸区域身份嵌入（与历史 0.670 基线同路线同预设）
        "10": {"class_type": "IPAdapterUnifiedLoader", "inputs": {
            "model": ["13", 0], "preset": "PLUS FACE (portraits)"}},
        "11": {"class_type": "LoadImage", "inputs": {"image": HERO.name}},
        "12": {"class_type": "IPAdapter", "inputs": {
            "model": ["10", 0], "ipadapter": ["10", 1], "image": ["11", 0],
            "weight": weight, "start_at": 0.0, "end_at": 0.9,
            "weight_type": "standard"}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {
            "width": 512, "height": 512, "batch_size": 1}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {
            "text": prompt + DRIFT_SUFFIX, "clip": ["13", 1]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {
            "text": NEGATIVE, "clip": ["13", 1]}},
        "3": {"class_type": "KSampler", "inputs": {
            "seed": seed, "steps": 25, "cfg": 7.0,
            "sampler_name": "euler", "scheduler": "normal", "denoise": 1.0,
            "model": ["12", 0], "positive": ["6", 0],
            "negative": ["7", 0], "latent_image": ["5", 0]}},
        "8": {"class_type": "VAEDecode", "inputs": {
            "samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {
            "images": ["8", 0], "filename_prefix": "yyc3/combo_v2"}},
    }


def comfy_generate(workflow: dict, out_path: Path, timeout: int = 600) -> None:
    """提交 ComfyUI 任务并轮询取回产物（与网关同协议）。"""
    client_id = uuid.uuid4().hex
    body = json.dumps({"prompt": workflow, "client_id": client_id}).encode()
    req = urllib.request.Request(f"{COMFYUI_URL}/prompt", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        prompt_id = json.loads(resp.read().decode())["prompt_id"]

    deadline = time.time() + timeout
    while time.time() < deadline:
        with urllib.request.urlopen(f"{COMFYUI_URL}/history/{prompt_id}",
                                    timeout=30) as resp:
            entry = json.loads(resp.read().decode()).get(prompt_id)
        if entry and entry.get("status", {}).get("completed", False):
            for _node, out in (entry.get("outputs") or {}).items():
                for img in out.get("images", []):
                    q = urllib.parse.urlencode({
                        "filename": img["filename"],
                        "subfolder": img.get("subfolder", ""),
                        "type": img.get("type", "output")})
                    with urllib.request.urlopen(
                            f"{COMFYUI_URL}/view?{q}", timeout=60) as r:
                        out_path.write_bytes(r.read())
                    return
        time.sleep(2)
    raise TimeoutError(f"ComfyUI 任务 {prompt_id} 超时（{timeout}s）")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lora", default="sd-hero-v2.safetensors",
                    help="ComfyUI/models/loras/ 内文件名")
    ap.add_argument("--weight", type=float, default=0.85,
                    help="IPAdapter 权重（历史基线 0.85）")
    ap.add_argument("--out", default=None, help="留证 JSON 落盘路径")
    args = ap.parse_args()

    enc = FaceEncoder(library_root=str(MANJU / "backend" / "face_library_sd"))
    ref = enc.extract_feature(str(HERO))
    assert enc.last_mode == "insightface", "参考特征必须真实模型提取"

    out_dir = Path("/tmp/kohya_out")
    rows = []
    for s in SEEDS:
        out = out_dir / f"combo_v2_w{int(args.weight * 100):03d}_{s}.png"
        t0 = time.perf_counter()
        comfy_generate(build_workflow(PORTRAIT, s, args.lora, args.weight), out)
        dt = round(time.perf_counter() - t0, 1)
        f = enc.extract_feature(str(out))
        sim = None if f is None else round(float(ref @ f), 4)
        rows.append({"seed": s, "sim": sim, "mode": enc.last_mode, "latency_s": dt})
        print(f"[combo-v2] seed={s} sim={sim} mode={enc.last_mode}  [{dt}s]")

    sims = [r["sim"] for r in rows if r["sim"] is not None]
    report = {
        "testcase": "M3 二轮 LoRA + IPAdapter PLUS FACE 组合评测（ComfyUI 脸区域路线）",
        "lora": args.lora, "ipadapter_weight": args.weight,
        "rows": rows,
        "mean": round(sum(sims) / len(sims), 4),
        "min": min(sims), "max": max(sims),
        "baseline": BASELINES,
        "target_ge_0.85": min(sims) >= 0.85,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.out:
        Path(args.out).write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
