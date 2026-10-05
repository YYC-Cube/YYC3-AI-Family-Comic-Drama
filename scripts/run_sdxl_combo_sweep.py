# ==============================================================
# run_sdxl_combo_sweep.py — SDXL 阶段 2 组合扫描（YYC3-62 §五）
# 路线：DreamShaperXL_Lightning + LoraLoader(sd-hero-xl-v1) + InstantID
#   权重网格（LoRA strength × InstantID weight），对齐 M3 二轮方法论
#   （SD15 实证：组合权重是第一杠杆，必须扫描定峰，禁止单点结论）。
# 门槛（阶段 3 触发条件）：mean ≥ 0.85 且 min ≥ 0.8036（SD15 min 冠军）
#   → production_switch_review = true
# 口径：4 漂移种子 × insightface 512d 余弦 vs hero_base 设定图本体（零变更）；
#   采样 Lightning 档（steps8/cfg1.8/1024²，与阶段 1 预验同参）。
# 运行：manju-venv python scripts/run_sdxl_combo_sweep.py \
#   --lora /tmp/kohya_out_sdxl/sd-hero-xl-v1.safetensors \
#   [--lora-strengths 0.6,0.8,1.0] [--iid-weights 0.6,0.8,1.0] [--out x.json]
# ==============================================================
import argparse
import json
import shutil
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
CKPT = "DreamShaperXL_Lightning.safetensors"
PORTRAIT = ("portrait of a young chinese wuxia heroine, delicate face, "
            "ancient hanfu, ink wash background, upper body, highly detailed")
DRIFT_SUFFIX = ", smiling, night lantern lighting, different angle"
NEGATIVE = "低质量、变形、多余手指、水印"
SEEDS = [777, 888, 999, 1111]
GATE_MEAN, GATE_MIN = 0.85, 0.8036  # YYC3-62 §五 阶段 3 双门槛

HERO = Path("/Users/yanyu/YYC-Cube/tools/ComfyUI/input/hero_base.png")
if not HERO.exists():
    HERO = Path("/tmp/comfy_out/hero_base.png")
    print(f"[warn] 历史设定图缺失，回落 /tmp 参考系（有漂移风险）：{HERO}")

BASELINES = {"sdxl_instantid_only(阶段1)": 0.8446,
             "sd15_v2_combo_prod": 0.8672, "sd15_min_champion": 0.8036}


def build_workflow(prompt: str, seed: int, lora: str, lora_s: float,
                   iid_w: float, steps: int, cfg: float) -> dict:
    """LoraLoader → ApplyInstantID 组合工作流（与阶段 1 唯一差异=LoRA 注入）。

    LoRA 挂 model/clip 双通道（KSampler 与正负提示词编码全链生效，
    对齐 drama_stage_adapter v1.3 combo 口径）。
    """
    return {
        "4": {"class_type": "CheckpointLoaderSimple",
              "inputs": {"ckpt_name": CKPT}},
        "13": {"class_type": "LoraLoader", "inputs": {
            "lora_name": lora, "strength_model": lora_s, "strength_clip": lora_s,
            "model": ["4", 0], "clip": ["4", 1]}},
        "31": {"class_type": "InstantIDModelLoader",
               "inputs": {"instantid_file": "ip-adapter.bin"}},
        "38": {"class_type": "InstantIDFaceAnalysis",
               "inputs": {"provider": "CPU"}},
        "16": {"class_type": "ControlNetLoader",
               "inputs": {"control_net_name": "instantid/controlnet.safetensors"}},
        "13i": {"class_type": "LoadImage", "inputs": {"image": HERO.name}},
        "5": {"class_type": "EmptyLatentImage",
              "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
        "39": {"class_type": "CLIPTextEncode",
               "inputs": {"text": prompt + DRIFT_SUFFIX, "clip": ["13", 1]}},
        "40": {"class_type": "CLIPTextEncode",
               "inputs": {"text": NEGATIVE, "clip": ["13", 1]}},
        "60": {"class_type": "ApplyInstantID", "inputs": {
            "instantid": ["31", 0], "insightface": ["38", 0],
            "control_net": ["16", 0], "image": ["13i", 0], "model": ["13", 0],
            "positive": ["39", 0], "negative": ["40", 0],
            "weight": iid_w, "start_at": 0.0, "end_at": 1.0}},
        "3": {"class_type": "KSampler", "inputs": {
            "seed": seed, "steps": steps, "cfg": cfg,
            "sampler_name": "euler", "scheduler": "sgm_uniform", "denoise": 1.0,
            "model": ["60", 0], "positive": ["60", 1],
            "negative": ["60", 2], "latent_image": ["5", 0]}},
        "8": {"class_type": "VAEDecode",
              "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {
            "images": ["8", 0], "filename_prefix": "yyc3/sdxl_combo"}},
    }


def comfy_generate(workflow: dict, out_path: Path, timeout: int = 1200) -> None:
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
        if entry and entry.get("status", {}).get("status_str") == "error":
            raise RuntimeError(f"ComfyUI 执行失败：{entry['status'].get('messages')}")
        time.sleep(2)
    raise TimeoutError(f"ComfyUI 任务 {prompt_id} 超时（{timeout}s）")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lora", required=True, help="训练产物 safetensors 路径")
    ap.add_argument("--lora-strengths", default="0.6,0.8,1.0")
    ap.add_argument("--iid-weights", default="0.6,0.8,1.0")
    ap.add_argument("--steps", type=int, default=8)
    ap.add_argument("--cfg", type=float, default=1.8)
    ap.add_argument("--out", default=None)
    ap.add_argument("--reuse", action="store_true", help="既有产物直接重评分")
    args = ap.parse_args()

    lora_path = Path(args.lora)
    assert lora_path.exists(), f"LoRA 不存在：{lora_path}"
    comfy_loras = Path("/Users/yanyu/YYC-Cube/tools/ComfyUI/models/loras")
    if lora_path.parent != comfy_loras:
        shutil.copy(lora_path, comfy_loras / lora_path.name)  # ComfyUI 白名单目录
    lora_name = lora_path.name

    enc = FaceEncoder(library_root=str(MANJU / "backend" / "face_library_sd"))
    ref = enc.extract_feature(str(HERO))
    assert enc.last_mode == "insightface", "参考特征必须真实模型提取"

    out_dir = Path("/tmp/sdxl_combo")
    out_dir.mkdir(parents=True, exist_ok=True)
    ls_list = [float(x) for x in args.lora_strengths.split(",")]
    iw_list = [float(x) for x in args.iid_weights.split(",")]

    grid = []
    for ls in ls_list:
        for iw in iw_list:
            rows = []
            for s in SEEDS:
                out = out_dir / f"l{int(ls*100):03d}_w{int(iw*100):03d}_{s}.png"
                if args.reuse and out.exists():
                    dt = 0.0
                else:
                    t0 = time.perf_counter()
                    comfy_generate(build_workflow(PORTRAIT, s, lora_name, ls,
                                                  iw, args.steps, args.cfg), out)
                    dt = round(time.perf_counter() - t0, 1)
                f = enc.extract_feature(str(out))
                sim = None if f is None else round(float(ref @ f), 4)
                rows.append({"seed": s, "sim": sim})
            sims = [r["sim"] for r in rows if r["sim"] is not None]
            cell = {"lora_strength": ls, "instantid_weight": iw, "rows": rows,
                    "mean": round(sum(sims) / len(sims), 4) if sims else None,
                    "min": min(sims) if sims else None}
            grid.append(cell)
            print(f"[combo] lora={ls} iid={iw} mean={cell['mean']} min={cell['min']}")

    best = max((g for g in grid if g["mean"] is not None), key=lambda g: g["mean"])
    report = {
        "testcase": "SDXL 阶段 2 组合扫描（DreamShaperXL_Lightning + LoRA + InstantID）",
        "lora": lora_name, "ckpt": CKPT,
        "sampling": {"steps": args.steps, "cfg": args.cfg, "size": "1024x1024"},
        "grid": grid, "best": best,
        "baseline": BASELINES,
        "gate": {"mean_ge_0.85": best["mean"] >= GATE_MEAN,
                 "min_ge_0.8036": best["min"] >= GATE_MIN},
        "production_switch_review": bool(best["mean"] >= GATE_MEAN
                                         and best["min"] >= GATE_MIN),
    }
    print(json.dumps({k: report[k] for k in
                      ("best", "baseline", "gate", "production_switch_review")},
                     ensure_ascii=False, indent=2))
    if args.out:
        Path(args.out).write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
