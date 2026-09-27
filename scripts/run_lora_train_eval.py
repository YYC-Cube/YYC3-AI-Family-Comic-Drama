# ==============================================================
# run_lora_train_eval.py — 角色 LoRA 训练 + 跨种子复测（M3 ①）
# 科学目标：LoRA 后跨种子身份 sim 从 0.67(IPAdapter) 冲 0.85+
# 设计：diffusers SD1.5 + peft LoRA（unet attn），数据=hero_base 变换族扩增，
#       触发词 <sd-hero>；训练后同漂移种子集复测（对照 v1.3/v1.4 基线）
# 导出：peft 目录 + kohya 键位 remap（ComfyUI models/loras/ 可加载性）
# 运行：/Users/yanyu/YYC-Cube/tools/ComfyUI/.venv/bin/python \
#       scripts/run_lora_train_eval.py [--steps 240]
# ==============================================================
import argparse
import json
import os
import random
import sys
import time
from pathlib import Path

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")  # HF 直连被阻断

import numpy as np  # noqa: E402
import torch  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
CKPT = "/Users/yanyu/YYC-Cube/tools/ComfyUI/models/checkpoints/DreamShaper_8_pruned.safetensors"
HERO = "/tmp/comfy_out/hero_base.png"
OUT_LORA = Path("/tmp/lora_sdhero")
OUT_KOHYA = Path("/Users/yanyu/YYC-Cube/tools/ComfyUI/models/loras/sd-hero_smoke.safetensors")

TRIGGER = "<sd-hero>"
PROMPT_T = ("portrait of a young chinese wuxia heroine, delicate face, "
            "ancient hanfu, ink wash background, upper body, highly detailed")
DRIFT_SUFFIX = ", smiling, night lantern lighting, different angle"
SEEDS = [777, 888, 999, 1111]
BASE_NOANCHOR = {"mean": 0.5157, "rows": [0.4418, 0.5306, 0.5216, 0.5687]}
BASE_IPADAPTER = {"mean": 0.670, "rows": [0.7154, 0.6484, 0.6671, 0.6490]}

sys.path.insert(0, str(REPO / "yyc3-ai-manju-studio" / "backend"))
from app.modules.consistency_engine.face_encoder import FaceEncoder  # noqa: E402


def build_dataset():
    from PIL import Image
    out = OUT_LORA / "dataset"
    out.mkdir(parents=True, exist_ok=True)
    img = Image.open(HERO).convert("RGB").resize((512, 512), Image.LANCZOS)
    variants = {"a": img, "b": img.transpose(Image.FLIP_LEFT_RIGHT)}
    warm = np.array(img).astype(np.float32)
    warm[..., 0] *= 1.12
    warm[..., 2] *= 0.9
    variants["c"] = Image.fromarray(np.clip(warm, 0, 255).astype(np.uint8))
    cool = np.array(img).astype(np.float32)
    cool[..., 0] *= 0.9
    cool[..., 2] *= 1.12
    variants["d"] = Image.fromarray(np.clip(cool, 0, 255).astype(np.uint8))
    paths = []
    for name, im in variants.items():
        p = out / f"hero_{name}.png"
        im.save(p, "JPEG", quality=88)
        paths.append(str(p))
    print(f"[dataset] {len(paths)} 张（含扩增）")
    return paths


def load_pipe():
    from diffusers import StableDiffusionPipeline
    pipe = StableDiffusionPipeline.from_single_file(
        CKPT, config="Lykon/DreamShaper",
        torch_dtype=torch.float32, safety_checker=None, requires_safety_checker=False)
    pipe.set_progress_bar_config(disable=True)
    return pipe


def train(pipe, dataset, steps, lr):
    from peft import LoraConfig, get_peft_model

    unet = pipe.unet
    vae, te, tok = pipe.vae, pipe.text_encoder, pipe.tokenizer
    lcfg = LoraConfig(r=8, lora_alpha=16, lora_dropout=0.0, bias="none",
                      target_modules=["to_q", "to_k", "to_v", "to_out_0"])
    unet = get_peft_model(unet, lcfg)
    unet.train()
    trainable = [p for p in unet.parameters() if p.requires_grad]
    print(f"[train] trainable params: {sum(p.numel() for p in trainable):,}")

    from PIL import Image
    from diffusers import DDPMScheduler
    sched = DDPMScheduler.from_config(pipe.scheduler.config)
    opt = torch.optim.AdamW(trainable, lr=lr)
    prompts = [f"{TRIGGER}, {PROMPT_T}"] * len(dataset)
    imgs = [np.array(Image.open(p).convert("RGB")).astype(np.float32) / 127.5 - 1
            for p in dataset]
    imgs = torch.from_numpy(np.stack(imgs)).permute(0, 3, 1, 2)  # N,3,512,512

    vae.scaling_factor = getattr(vae.config, "scaling_factor", 0.18215)
    with torch.no_grad():
        latents = vae.encode(imgs).latent_dist.sample() * vae.scaling_factor

    g = torch.Generator().manual_seed(42)
    t0 = time.time()
    for step in range(1, steps + 1):
        i = random.randrange(len(dataset))
        with torch.no_grad():
            ti = tok([prompts[i]], padding="max_length", max_length=77,
                     truncation=True, return_tensors="pt")
            emb = te(ti.input_ids)[0]
        noise = torch.randn((1, 4, 64, 64), generator=g)
        t = torch.randint(0, sched.config.num_train_timesteps, (1,),
                          generator=g).item()
        # diffusers：add_noise 返回单张量；扩散目标即所加噪声
        noisy = sched.add_noise(latents[i:i + 1], noise, torch.tensor([t]))
        target = noise
        pred = unet(noisy, t, encoder_hidden_states=emb).sample
        loss = torch.nn.functional.mse_loss(pred, target)
        opt.zero_grad()
        loss.backward()
        opt.step()
        if step % 20 == 0 or step == 1:
            print(f"[train] step {step}/{steps} loss={loss.item():.4f} "
                  f"elapsed={time.time() - t0:.0f}s")
    unet.eval()
    pipe.unet = unet
    return pipe


def eval_sims(pipe):
    from PIL import Image
    enc = FaceEncoder(library_root="/tmp/lora_lib")
    ref = enc.extract_feature(HERO)
    assert enc.last_mode == "insightface", "参考特征必须真实模型"
    rows = []
    for s in SEEDS:
        g = torch.Generator().manual_seed(s)
        img = pipe(f"{TRIGGER}, {PROMPT_T}{DRIFT_SUFFIX}", num_inference_steps=20,
                   guidance_scale=7.0, generator=g,
                   height=512, width=512).images[0]
        p = OUT_LORA / f"lora_{s}.png"
        img.save(p, "JPEG", quality=92)
        f = enc.extract_feature(str(p))
        rows.append(round(float(ref @ f), 4))
        print(f"[eval] seed={s} sim={rows[-1]} mode={enc.last_mode}")
    return rows


def export_kohya(pipe):
    """peft 键位 → kohya/ComfyUI 格式（best-effort remap）"""
    sd = {k: v for k, v in pipe.unet.state_dict().items()
          if "lora" in k.lower() and v.dtype == torch.float32}
    out = {}
    for k, v in sd.items():
        nk = k.replace("base_model.model.", "").replace(".", "_")
        nk = nk.replace("_lora_A_weight", ".lora_down.weight")
        nk = nk.replace("_lora_B_weight", ".lora_up.weight")
        nk = "lora_unet_" + nk.split("unet_", 1)[-1] if "unet_" in nk else nk
        out[nk] = v
    OUT_KOHYA.parent.mkdir(parents=True, exist_ok=True)
    from safetensors.torch import save_file
    save_file(out, str(OUT_KOHYA))
    print(f"[export] kohya remap {len(out)} 张量 → {OUT_KOHYA.name}")
    pipe.unet.save_pretrained(str(OUT_LORA / "peft"))
    return len(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=240)
    ap.add_argument("--lr", type=float, default=5e-4)
    args = ap.parse_args()

    random.seed(42)
    torch.manual_seed(42)

    dataset = build_dataset()
    pipe = load_pipe()
    pipe = train(pipe, dataset, args.steps, args.lr)
    n_kohya = export_kohya(pipe)
    rows = eval_sims(pipe)

    report = {
        "steps": args.steps, "lr": args.lr,
        "rows": rows,
        "lora_min": min(rows), "lora_max": max(rows),
        "lora_mean": round(sum(rows) / len(rows), 4),
        "baseline": {"no_anchor": BASE_NOANCHOR, "ipadapter": BASE_IPADAPTER},
        "target_ge_0.85_min": min(rows) >= 0.85,
        "kohya_tensors": n_kohya,
        "exports": {"peft": str(OUT_LORA / "peft"), "kohya": str(OUT_KOHYA)},
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    Path("/tmp/lora_eval.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
