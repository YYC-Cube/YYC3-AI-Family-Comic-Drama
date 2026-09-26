# ==============================================================
# run_threshold_calibration.py — anchor_guard 0.85 阈值复标（强变换多机位素材）
# 变换族：水平翻转/旋转12°/暖调/冷调/JPEG60/裁剪60%/压暗0.72/去饱和（8×2 角色）
# 判定：same = 库参考特征 vs 变体；cross = 跨角色全部配对
# 输出：分布表 + 推荐阈值（min_same 与 max_cross 中点，0.05 步长向下取整）
# 运行：yyc3-ai-manju-studio/.venv/bin/python scripts/run_threshold_calibration.py
# ==============================================================
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance

REPO = Path(__file__).resolve().parents[1]
MANJU = REPO / "yyc3-ai-manju-studio"
FACES = Path("/tmp/g3_faces")
LIBRARY = MANJU / "backend" / "face_library"

sys.path.insert(0, str(MANJU / "backend"))
from app.modules.consistency_engine.face_encoder import FaceEncoder, FEATURE_DIM  # noqa: E402


def build_variants():
    """8 种强变换（模拟换光/换机位/压缩/构图差异）"""
    out = {}
    for pid, src in (("A", FACES / "charA_shot1.png"), ("B", FACES / "charB_shot1.png")):
        img = Image.open(src).convert("RGB")
        vs = {}
        vs["flip"] = img.transpose(Image.FLIP_LEFT_RIGHT)
        vs["rot12"] = img.rotate(12, expand=True, fillcolor=(20, 20, 24))
        warm = np.array(img).astype(np.float32)
        warm[..., 0] *= 1.16; warm[..., 2] *= 0.88
        vs["warm"] = Image.fromarray(np.clip(warm, 0, 255).astype(np.uint8))
        cool = np.array(img).astype(np.float32)
        cool[..., 0] *= 0.88; cool[..., 2] *= 1.16
        vs["cool"] = Image.fromarray(np.clip(cool, 0, 255).astype(np.uint8))
        vs["crop60"] = img.crop((128, 128, 512, 512)).resize((640, 640), Image.LANCZOS)
        vs["dark"] = ImageEnhance.Brightness(img).enhance(0.72)
        vs["desat"] = ImageEnhance.Color(img).enhance(0.25)
        paths = {}
        for name, im in vs.items():
            p = FACES / f"cal_{pid}_{name}.png"
            im.save(p, "JPEG", quality=60 if name == "jpeg60" else 92)
            paths[name] = p
        # jpeg60 独立（在原图上再压）
        p = FACES / f"cal_{pid}_jpeg60.png"
        img.save(p, "JPEG", quality=55)
        paths["jpeg60"] = p
        out[pid] = paths
    return out


def main():
    # 库参考 = shot1（G3-001 同路径重建）
    enc = FaceEncoder(library_root=str(LIBRARY))
    if LIBRARY.exists():
        shutil.rmtree(LIBRARY)
    enc.save_character("hero", "hero", str(FACES / "charA_shot1.png"))
    enc.save_character("villain", "villain", str(FACES / "charB_shot1.png"))
    ref = {"A": enc.load_feature("hero"), "B": enc.load_feature("villain")}

    variants = build_variants()
    feats, modes = {}, {}
    for pid, paths in variants.items():
        for name, p in paths.items():
            feats[f"{pid}_{name}"] = enc.extract_feature(str(p))
            modes[f"{pid}_{name}"] = enc.last_mode

    def cos(a, b):
        return float(a @ b)

    same_rows, undetected = [], []
    for key, f in feats.items():
        pid = key[0]
        if modes[key] != "insightface":
            undetected.append(key)
            continue
        same_rows.append({"variant": key, "sim": round(cos(ref[pid], f), 4)})
    same_sims = [r["sim"] for r in same_rows]

    cross_sims = []
    for ka, fa in feats.items():
        for kb, fb in feats.items():
            if ka[0] == "B" and kb[0] == "A":
                cross_sims.append(round(cos(fa, fb), 4))
    cross_max = max(cross_sims)
    same_min = min(same_sims) if same_sims else 0.0

    recommended = max(0.5, min(0.9, ((same_min + cross_max) / 2) // 0.05 * 0.05))
    report = {
        "feature_dim": FEATURE_DIM,
        "variants_detected": f"{len(same_rows)}/{len(feats)}",
        "undetected": undetected,
        "same_min": same_min, "same_max": max(same_sims),
        "cross_max": cross_max, "cross_min": min(cross_sims),
        "margin": round(same_min - cross_max, 4),
        "recommended_threshold": round(recommended, 2),
        "rows": sorted(same_rows, key=lambda r: r["sim"]),
        "note": "强变换（翻/旋/色温/压缩/构图/明度/去饱和）= 多机位上界压力位；"
                "未检出的变换以 escalate 处置（不进生产判定），不计入阈值分位",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    Path("/tmp/threshold_calibration.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n=== 复标结论：same_min={same_min:.4f} cross_max={cross_max:.4f} "
          f"→ 推荐阈值 {recommended:.2f}（margin {report['margin']:.4f}）===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
