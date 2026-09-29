# ==============================================================
# run_lora_dataset_v2.py — LoRA 二轮训练集组装（M3 一致性二轮冲刺 · P1）
# 策略：首轮 4 张变换族是泛化瓶颈（跨种子复测最优仅 0.6441），
#   二轮扩至 20 图三源混合：
#   ① hero_base 原图 + 首轮 4 变换（orig/flip/warm/cool）
#   ② 新增 6 变换（亮度±/饱和度±/上/下裁剪视角——多光照多视角）
#   ③ H3 动态镜抽帧 9 张（生产链真实多姿态帧，insightface 质检全过）
# 运行（ComfyUI venv）：
#   ComfyUI.venv/bin/python scripts/run_lora_dataset_v2.py
# ==============================================================
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance

HERO = Path("/tmp/comfy_out/hero_base.png")
H3_FRAMES = Path("/tmp/h3_frames")
OUT = Path("/tmp/kohya_train_v2/train/10_sdhero")

CAPTION = ("portrait of a young chinese wuxia heroine, delicate face, "
           "ancient hanfu, ink wash background, upper body, highly detailed")


def variants(img: Image.Image) -> dict[str, Image.Image]:
    """从 512 基准图派生 10 张变换（含原图）：多光照 + 多裁剪视角。"""
    arr = np.array(img).astype(np.float32)

    warm = arr.copy()
    warm[..., 0] *= 1.12
    warm[..., 2] *= 0.9
    cool = arr.copy()
    cool[..., 0] *= 0.9
    cool[..., 2] *= 1.12
    bright_up = arr * 1.25
    bright_dn = arr * 0.75

    w, h = img.size
    ch = int(h * 0.8)  # 裁掉 20% 再 resize = 视角/构图变化
    cw = int(w * 0.8)

    return {
        "orig": img,
        "flip": img.transpose(Image.Transpose.FLIP_LEFT_RIGHT),
        "warm": Image.fromarray(np.clip(warm, 0, 255).astype(np.uint8)),
        "cool": Image.fromarray(np.clip(cool, 0, 255).astype(np.uint8)),
        "bright_up": Image.fromarray(np.clip(bright_up, 0, 255).astype(np.uint8)),
        "bright_dn": Image.fromarray(np.clip(bright_dn, 0, 255).astype(np.uint8)),
        "sat_up": ImageEnhance.Color(img).enhance(1.4),
        "sat_dn": ImageEnhance.Color(img).enhance(0.6),
        "crop_top": img.crop((0, 0, w, ch)).resize((512, 512), Image.Resampling.LANCZOS),
        "crop_bottom": img.crop((0, h - ch, w, h)).resize((512, 512), Image.Resampling.LANCZOS),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    base = Image.open(HERO).convert("RGB").resize(
        (512, 512), Image.Resampling.LANCZOS)

    n = 0
    # ① + ②：基准图与变换族
    for name, im in variants(base).items():
        p = OUT / f"hero_{name}.png"
        im.save(p, "PNG")
        p.with_suffix(".txt").write_text(CAPTION, encoding="utf-8")
        n += 1

    # ③：H3 动态镜帧（生产链真实多姿态；insightface 质检 9/9 有脸）
    for p in sorted(H3_FRAMES.glob("*.png")):
        im = Image.open(p).convert("RGB")
        w, h = im.size
        side = min(w, h)  # 中心方形裁剪（脸居中构图）
        im = im.crop(((w - side) // 2, (h - side) // 2,
                      (w + side) // 2, (h + side) // 2))
        out = OUT / f"h3_{p.stem}.png"
        im.save(out, "PNG")
        out.with_suffix(".txt").write_text(CAPTION, encoding="utf-8")
        n += 1

    print(f"[dataset-v2] {n} 图 + caption -> {OUT}")
    print("[dataset-v2] 步数核算：20 图 x 10 repeats = 200 步/epoch，"
          "max_train_steps=2000 即 10 epoch（首轮 5 图 40 epoch）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
