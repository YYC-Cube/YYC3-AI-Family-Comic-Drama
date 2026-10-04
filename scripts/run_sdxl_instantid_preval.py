# ==============================================================
# run_sdxl_instantid_preval.py — SDXL 基模迁移阶段 1 预验（YYC3-62 §五）
# 路线：DreamShaper XL Lightning（纯基模，零 LoRA）+ InstantID（cubiq 节点）
#   单独评测——SD15 族内 0.85 无一达标（FaceID 组合最优 0.8248）后的破局路径。
# 门槛：单独 mean ≥ 0.80（参照：SD15 PLUS FACE 单独 0.67 / FaceID 单独 0.7926）
# 口径（零变更复用）：4 漂移种子 × insightface 512 维余弦 vs hero_base 设定图
#   本体（ComfyUI/input/，2026-10-02 参考系漂移治理规则；/tmp 仅回落并告警）。
# 采样参数说明（诚实标注与 SD15 协议的差异）：DreamShaperXL_Lightning 为蒸馏
#   少步模型，25步/cfg7 会过曝——按 Lightning 档适配 steps=8/cfg=1.8/euler/
#   sgm_uniform/1024²；SDXL 原生 1024，不降 512。评分协议不变，仅采样档适配。
# 前置：checkpoints/DreamShaperXL_Lightning.safetensors · instantid/ip-adapter.bin ·
#   controlnet/instantid/controlnet.safetensors · insightface/models/antelopev2/*.onnx
#   ComfyUI@41888（需已重启装载 ComfyUI_InstantID 节点）。
# 运行：yyc3-ai-manju-studio/.venv/bin/python scripts/run_sdxl_instantid_preval.py \
#   [--weight 0.8] [--steps 8] [--cfg 1.8] [--out path.json]
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
CKPT = "DreamShaperXL_Lightning.safetensors"
PORTRAIT = ("portrait of a young chinese wuxia heroine, delicate face, "
            "ancient hanfu, ink wash background, upper body, highly detailed")
DRIFT_SUFFIX = ", smiling, night lantern lighting, different angle"
NEGATIVE = "低质量、变形、多余手指、水印"
SEEDS = [777, 888, 999, 1111]
GATE_MEAN = 0.80  # YYC3-62 §五 阶段 1 门槛：单独 mean ≥ 0.80

# 参考系锚定历史设定图本体（唯一可信锚点，规则同 run_lora_plusface_combo）
HERO = Path("/Users/yanyu/YYC-Cube/tools/ComfyUI/input/hero_base.png")
if not HERO.exists():
    HERO = Path("/tmp/comfy_out/hero_base.png")
    print(f"[warn] 历史设定图缺失，回落 /tmp 参考系（有漂移风险）：{HERO}")

BASELINES = {"sd15_plusface_only": 0.67, "sd15_faceid_only": 0.7926,
             "sd15_v2_combo_prod": 0.8672}


def build_workflow(prompt: str, seed: int, weight: float,
                   steps: int, cfg: float) -> dict:
    """DreamShaper XL + InstantID 基础工作流（examples/InstantID_basic 同构）。

    与 SD15 combo 工作流的差异：无 LoraLoader/IPAdapter（纯 InstantID 三件套）；
    SDXL 原生 1024²；Lightning 少步档。
    """
    return {
        "4": {"class_type": "CheckpointLoaderSimple",
              "inputs": {"ckpt_name": CKPT}},
        "31": {"class_type": "InstantIDModelLoader",
               "inputs": {"instantid_file": "ip-adapter.bin"}},
        "38": {"class_type": "InstantIDFaceAnalysis",
               "inputs": {"provider": "CPU"}},
        "16": {"class_type": "ControlNetLoader",
               "inputs": {"control_net_name": "instantid/controlnet.safetensors"}},
        "13": {"class_type": "LoadImage", "inputs": {"image": HERO.name}},
        "5": {"class_type": "EmptyLatentImage",
              "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
        "39": {"class_type": "CLIPTextEncode",
               "inputs": {"text": prompt + DRIFT_SUFFIX, "clip": ["4", 1]}},
        "40": {"class_type": "CLIPTextEncode",
               "inputs": {"text": NEGATIVE, "clip": ["4", 1]}},
        "60": {"class_type": "ApplyInstantID", "inputs": {
            "instantid": ["31", 0], "insightface": ["38", 0],
            "control_net": ["16", 0], "image": ["13", 0], "model": ["4", 0],
            "positive": ["39", 0], "negative": ["40", 0],
            "weight": weight, "start_at": 0.0, "end_at": 1.0}},
        "3": {"class_type": "KSampler", "inputs": {
            "seed": seed, "steps": steps, "cfg": cfg,
            "sampler_name": "euler", "scheduler": "sgm_uniform", "denoise": 1.0,
            "model": ["60", 0], "positive": ["60", 1],
            "negative": ["60", 2], "latent_image": ["5", 0]}},
        "8": {"class_type": "VAEDecode",
              "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {
            "images": ["8", 0], "filename_prefix": "yyc3/sdxl_preval"}},
    }


def comfy_generate(workflow: dict, out_path: Path, timeout: int = 1200) -> None:
    """提交 ComfyUI 任务并轮询取回产物（协议同 run_lora_plusface_combo）。

    超时 1200s：SDXL 1024 + InstantID 首镜含模型加载，M4 Max 预估 60-180s/张，
    按 37 轮「队列高峰超时」教训给足预算（复跑走 --reuse 现有产物）。
    """
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
        # 执行失败（节点报错）即时暴露，不空转到超时
        if entry and entry.get("status", {}).get("status_str") == "error":
            raise RuntimeError(f"ComfyUI 执行失败：{entry['status'].get('messages')}")
        time.sleep(2)
    raise TimeoutError(f"ComfyUI 任务 {prompt_id} 超时（{timeout}s）")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--weight", type=float, default=0.8,
                    help="InstantID 权重（节点默认 0.8）")
    ap.add_argument("--steps", type=int, default=8,
                    help="采样步数（Lightning 蒸馏档默认 8）")
    ap.add_argument("--cfg", type=float, default=1.8,
                    help="CFG（Lightning 档默认 1.8）")
    ap.add_argument("--out", default=None, help="留证 JSON 落盘路径")
    ap.add_argument("--reuse", action="store_true",
                    help="复用既有产物仅重评分（断点续跑口径）")
    args = ap.parse_args()

    out_dir = Path("/tmp/sdxl_preval")
    out_dir.mkdir(parents=True, exist_ok=True)

    enc = FaceEncoder(library_root=str(MANJU / "backend" / "face_library_sd"))
    ref = enc.extract_feature(str(HERO))
    assert enc.last_mode == "insightface", "参考特征必须真实模型提取"

    rows = []
    for s in SEEDS:
        out = out_dir / f"sdxl_w{int(args.weight * 100):02d}_{s}.png"
        if args.reuse and out.exists():
            dt = 0.0
        else:
            t0 = time.perf_counter()
            comfy_generate(build_workflow(PORTRAIT, s, args.weight,
                                          args.steps, args.cfg), out)
            dt = round(time.perf_counter() - t0, 1)
        f = enc.extract_feature(str(out))
        sim = None if f is None else round(float(ref @ f), 4)
        rows.append({"seed": s, "sim": sim, "mode": enc.last_mode,
                     "latency_s": dt, "reused": bool(args.reuse and out.exists())})
        print(f"[sdxl-preval] seed={s} sim={sim} mode={enc.last_mode}  [{dt}s]")

    sims = [r["sim"] for r in rows if r["sim"] is not None]
    mean = round(sum(sims) / len(sims), 4) if sims else None
    report = {
        "testcase": "SDXL 基模迁移阶段 1 预验（DreamShaperXL_Lightning + InstantID 单独）",
        "ckpt": CKPT, "instantid_weight": args.weight,
        "sampling": {"steps": args.steps, "cfg": args.cfg, "size": "1024x1024",
                     "note": "Lightning 蒸馏档适配；评分协议（4 漂移种子 × "
                             "insightface 512d 余弦 vs 设定图本体）零变更复用"},
        "rows": rows, "mean": mean,
        "min": min(sims) if sims else None, "max": max(sims) if sims else None,
        "baseline": BASELINES,
        "gate_mean_ge_0.80": bool(mean is not None and mean >= GATE_MEAN),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.out:
        Path(args.out).write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
