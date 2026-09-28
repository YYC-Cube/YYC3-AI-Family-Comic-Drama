# ==============================================================
# run_kohya_lora.py — kohya 正规 LoRA：数据集准备 + 训练后评测（M3 ①）
# 模式：
#   prep  — 组装 kohya 标准数据集（<dir>/<repeat>_<concept>/*.png+.txt）
#   eval  — diffusers load_lora_weights 加载训练产物 → 4 漂移种子 sim 复测
# 训练本体由 Bash 直接调 train_network.py（kohya CLI），不经本脚本。
# 运行：
#   ComfyUI.venv/bin/python scripts/run_kohya_lora.py prep
#   ComfyUI.venv/bin/python scripts/run_kohya_lora.py eval --lora /tmp/kohya_out/sd-hero.safetensors
# ==============================================================
import argparse
import shutil
import sys
from pathlib import Path

import numpy as np  # noqa: F401  (PIL 转换用)

HERO = Path("/tmp/comfy_out/hero_base.png")
TRAIN_ROOT = Path("/tmp/kohya_train/train")
OUT_DIR = Path("/tmp/kohya_out")
LORA_PATH = OUT_DIR / "sd-hero.safetensors"
SEEDS = [777, 888, 999, 1111]
BASELINE_NOANCHOR_MEAN = 0.5157
BASELINE_IPADAPTER_MEAN = 0.670

CAPTION = ("portrait of a young chinese wuxia heroine, delicate face, "
           "ancient hanfu, ink wash background, upper body, highly detailed")
EVAL_PROMPT = ("portrait of a young chinese wuxia heroine, delicate face, "
               "ancient hanfu, ink wash background, upper body, highly detailed"
               ", smiling, night lantern lighting, different angle")


def prep():
    """组装 kohya 数据集：<TRAIN_ROOT>/10_hero/*.png + 同名 .txt"""
    from PIL import Image

    concept = TRAIN_ROOT / "10_hero"
    concept.mkdir(parents=True, exist_ok=True)

    img = Image.open(HERO).convert("RGB").resize((512, 512), Image.LANCZOS)
    variants = {
        "orig": img,
        "flip": img.transpose(Image.FLIP_LEFT_RIGHT),
    }
    arr = np.array(img).astype(np.float32)
    warm = arr.copy()
    warm[..., 0] *= 1.12
    warm[..., 2] *= 0.9
    variants["warm"] = Image.fromarray(np.clip(warm, 0, 255).astype(np.uint8))
    cool = arr.copy()
    cool[..., 0] *= 0.9
    cool[..., 2] *= 1.12
    variants["cool"] = Image.fromarray(np.clip(cool, 0, 255).astype(np.uint8))

    n = 0
    for name, im in variants.items():
        p = concept / f"hero_{name}.png"
        im.save(p, "PNG")
        p.with_suffix(".txt").write_text(CAPTION, encoding="utf-8")
        n += 1
    print(f"[prep] {n} 图 + caption → {concept}")
    print("[prep] 下一步：Bash 直接调 train_network.py（见 HANDOFF §23 命令）")
    return 0


def eval_lora(lora_path: str):
    """diffusers 加载 kohya LoRA → 4 漂移种子生成 → insightface sim"""
    import json

    import torch
    from PIL import Image

    from diffusers import StableDiffusionPipeline

    os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
    ckpt = "/Users/yanyu/YYC-Cube/tools/ComfyUI/models/checkpoints/DreamShaper_8_pruned.safetensors"
    pipe = StableDiffusionPipeline.from_single_file(
        ckpt, config="Lykon/DreamShaper",
        torch_dtype=torch.float32, safety_checker=None,
        requires_safety_checker=False)
    pipe.set_progress_bar_config(disable=True)
    pipe.load_lora_weights(lora_path)
    print(f"[eval] LoRA 已加载：{lora_path}")

    sys.path.insert(0, "/Users/yanyu/YYC-Cube/YYC3 AI Family-Comic Drama/"
                       "yyc3-ai-manju-studio/backend")
    from app.modules.consistency_engine.face_encoder import FaceEncoder

    enc = FaceEncoder(library_root="/tmp/lora_lib")
    ref = enc.extract_feature(str(HERO))
    assert enc.last_mode == "insightface", "参考特征必须真实模型提取"

    out_dir = Path("/tmp/kohya_out")
    rows = []
    for s in SEEDS:
        g = torch.Generator().manual_seed(s)
        img = pipe(EVAL_PROMPT, num_inference_steps=20, guidance_scale=7.0,
                   generator=g, height=512, width=512).images[0]
        p = out_dir / f"kohya_{s}.png"
        img.save(p, "JPEG", quality=92)
        f = enc.extract_feature(str(p))
        sim = round(float(ref @ f), 4)
        rows.append({"seed": s, "sim": sim, "mode": enc.last_mode})
        print(f"[eval] seed={s} sim={sim} mode={enc.last_mode}")

    sims = [r["sim"] for r in rows]
    report = {
        "lora": lora_path,
        "rows": rows,
        "mean": round(sum(sims) / len(sims), 4),
        "min": min(sims), "max": max(sims),
        "baseline": {"no_anchor_mean": BASELINE_NOANCHOR_MEAN,
                     "ipadapter_mean": BASELINE_IPADAPTER_MEAN},
        "target_ge_0.85": min(sims) >= 0.85,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    out_dir.mkdir(exist_ok=True)
    (out_dir / "kohya_eval.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["prep", "eval"])
    ap.add_argument("--lora", default=str(LORA_PATH))
    args = ap.parse_args()
    if args.mode == "prep":
        return prep()
    return eval_lora(args.lora)


if __name__ == "__main__":
    sys.exit(main())
