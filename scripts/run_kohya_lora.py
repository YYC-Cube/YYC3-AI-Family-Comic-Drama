# ==============================================================
# run_kohya_lora.py — kohya 正规 LoRA：数据集准备 + 训练后评测（M3 ①）
# 模式：
#   prep  — 组装 kohya 标准数据集（<dir>/<repeat>_<concept>/*.png+.txt）
#   eval  — diffusers load_lora_weights 加载训练产物 → 4 漂移种子 sim 复测
#   combo — LoRA + IPAdapter PLUS FACE 组合锚定评测（HANDOFF §19 定论：
#           「IPAdapter 兜底 + LoRA 训练」组合是 0.85+ 唯一路径）
# 训练本体由 Bash 直接调 train_network.py（kohya CLI），不经本脚本。
# 运行：
#   ComfyUI.venv/bin/python scripts/run_kohya_lora.py prep
#   ComfyUI.venv/bin/python scripts/run_kohya_lora.py eval --lora /tmp/kohya_out/sd-hero.safetensors
#   ComfyUI.venv/bin/python scripts/run_kohya_lora.py combo --lora /tmp/kohya_out/sd-hero-prod.safetensors --ipa-scale 0.6
# ==============================================================
import argparse
import os
import sys
from pathlib import Path

import numpy as np  # noqa: F401  (PIL 转换用)

# 参考图锚定历史设定图本体（2026-10-02 参考系漂移治理：/tmp 纯生成图随 ComfyUI
# 环境更新漂移（实证 sim 0.5675）禁止作跨日参考系；设定图本体逐字节稳定为唯一
# 锚点；/tmp 产物仅作回落并告警——对齐 run_lora_plusface_combo.py 修复模式）
HERO = Path("/Users/yanyu/YYC-Cube/tools/ComfyUI/input/hero_base.png")
if not HERO.exists():
    HERO = Path("/tmp/comfy_out/hero_base.png")
    print(f"[warn] 历史设定图缺失，回落 /tmp 参考系（有漂移风险）：{HERO}")
TRAIN_ROOT = Path("/tmp/kohya_train/train")
OUT_DIR = Path("/tmp/kohya_out")
LORA_PATH = OUT_DIR / "sd-hero.safetensors"
SEEDS = [777, 888, 999, 1111]
BASELINE_NOANCHOR_MEAN = 0.5157
BASELINE_IPADAPTER_MEAN = 0.670
# LoRA 单锚定最优实测（2026-09-29 四检查点评测：step2000 mean 最高，
# 见 docs/attachments/G4-20260929/tc-m3-lora-crosseed-eval.json）
BASELINE_LORA_S2000_MEAN = 0.6441
IPA_WEIGHT_NAME = "ip-adapter-plus-face_sd15.safetensors"

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

    img = Image.open(HERO).convert("RGB").resize((512, 512), Image.Resampling.LANCZOS)
    variants = {
        "orig": img,
        "flip": img.transpose(Image.Transpose.FLIP_LEFT_RIGHT),
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

    import torch  # pyright: ignore[reportMissingImports]

    from diffusers import StableDiffusionPipeline  # pyright: ignore[reportMissingImports]

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
    from app.modules.consistency_engine.face_encoder import FaceEncoder  # noqa: E402 # pyright: ignore[reportMissingImports]

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


def eval_combo(lora_path: str, ipa_scale: float):
    """LoRA + IPAdapter PLUS FACE 组合锚定评测（0.85+ 唯一路径实测）。

    与 eval_lora 同管线同 4 漂移种子，唯一差异：额外加载 IPAdapter
    PLUS FACE 并以 hero_base 为 IP 设定图（ip_adapter_image），
    scale 由 --ipa-scale 控制（LoRA 主导 + IPAdapter 身份兜底）。
    """
    import json

    import torch  # pyright: ignore[reportMissingImports]
    from PIL import Image

    from diffusers import StableDiffusionPipeline  # pyright: ignore[reportMissingImports]

    os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
    ckpt = "/Users/yanyu/YYC-Cube/tools/ComfyUI/models/checkpoints/DreamShaper_8_pruned.safetensors"
    pipe = StableDiffusionPipeline.from_single_file(
        ckpt, config="Lykon/DreamShaper",
        torch_dtype=torch.float32, safety_checker=None,
        requires_safety_checker=False)
    pipe.set_progress_bar_config(disable=True)
    pipe.load_lora_weights(lora_path)
    pipe.load_ip_adapter("h94/IP-Adapter", subfolder="models",
                         weight_name=IPA_WEIGHT_NAME)
    pipe.set_ip_adapter_scale(ipa_scale)
    print(f"[combo] LoRA 已加载：{lora_path}；IPAdapter scale={ipa_scale}")

    sys.path.insert(0, "/Users/yanyu/YYC-Cube/YYC3 AI Family-Comic Drama/"
                       "yyc3-ai-manju-studio/backend")
    from app.modules.consistency_engine.face_encoder import FaceEncoder  # noqa: E402 # pyright: ignore[reportMissingImports]

    enc = FaceEncoder(library_root="/tmp/lora_lib")
    ref = enc.extract_feature(str(HERO))
    assert enc.last_mode == "insightface", "参考特征必须真实模型提取"

    ip_image = Image.open(HERO).convert("RGB")
    out_dir = Path("/tmp/kohya_out")
    rows = []
    for s in SEEDS:
        g = torch.Generator().manual_seed(s)
        img = pipe(EVAL_PROMPT, num_inference_steps=20, guidance_scale=7.0,
                   generator=g, height=512, width=512,
                   ip_adapter_image=ip_image).images[0]
        p = out_dir / f"combo_s{int(ipa_scale * 100):03d}_{s}.png"
        img.save(p, "JPEG", quality=92)
        f = enc.extract_feature(str(p))
        sim = round(float(ref @ f), 4)
        rows.append({"seed": s, "sim": sim, "mode": enc.last_mode})
        print(f"[combo] seed={s} sim={sim} mode={enc.last_mode}")

    sims = [r["sim"] for r in rows]
    report = {
        "lora": lora_path, "ipadapter": IPA_WEIGHT_NAME,
        "ipadapter_scale": ipa_scale, "rows": rows,
        "mean": round(sum(sims) / len(sims), 4),
        "min": min(sims), "max": max(sims),
        "baseline": {"no_anchor_mean": BASELINE_NOANCHOR_MEAN,
                     "ipadapter_only_mean": BASELINE_IPADAPTER_MEAN,
                     "lora_only_s2000_mean": BASELINE_LORA_S2000_MEAN},
        "target_ge_0.85": min(sims) >= 0.85,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    out_dir.mkdir(exist_ok=True)
    (out_dir / f"combo_eval_scale{int(ipa_scale * 100):03d}.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["prep", "eval", "combo"])
    ap.add_argument("--lora", default=str(LORA_PATH))
    ap.add_argument("--ipa-scale", type=float, default=0.6,
                    help="IPAdapter 身份锚定强度（combo 模式）")
    args = ap.parse_args()
    if args.mode == "prep":
        return prep()
    if args.mode == "combo":
        return eval_combo(args.lora, args.ipa_scale)
    return eval_lora(args.lora)


if __name__ == "__main__":
    sys.exit(main())
