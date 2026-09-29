# ==============================================================
# run_lora_dataset_v3.py — LoRA 三轮训练集组装（M3 min 口径冲刺 · 777 类姿态）
# 依据 HANDOFF 32.4 TOP1：777 全权重域最低（生成姿态偏离训练分布），
#   三轮扩至三源混合（v2 全量 + H3 密集帧 + 777 族过门样本）：
#   ① v2 全量 19 图原样复用（10 变换族 + 9 生产帧）
#   ② H3 密集抽帧 15 张（4 视频窗口 5 时间点回拉，md5 内容去重防与 v2 旧帧重复）
#   ③ 777 类姿态挖掘过门 8 张（sd-hero-v2 w=0.15 自生成 + insightface 身份门 sim>=0.75）
# 运行（ComfyUI venv）：
#   ComfyUI.venv/bin/python scripts/run_lora_dataset_v3.py
# 上传口径：只传 png（对齐 v2 实际训练形态——caption 未生效，目录 class token 路线，控制变量）
# ==============================================================
import hashlib
import shutil
from pathlib import Path

from PIL import Image

V2_DIR = Path("/tmp/kohya_train_v2/train/10_sdhero")
H3_FRAMES_V3 = Path("/tmp/h3_frames_v3")
MINE_ACCEPTED = Path("/tmp/pose_mining/accepted")
OUT = Path("/tmp/kohya_train_v3/train/10_sdhero")

CAPTION = ("portrait of a young chinese wuxia heroine, delicate face, "
           "ancient hanfu, ink wash background, upper body, highly detailed")


def md5_of(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest()


def center_square_512(src: Path, dst: Path) -> None:
    """中心方形裁剪 + 512 归一（同 v2 蓝本，脸居中构图）。"""
    im = Image.open(src).convert("RGB")
    w, h = im.size
    side = min(w, h)
    im = im.crop(((w - side) // 2, (h - side) // 2,
                  (w + side) // 2, (h + side) // 2))
    im = im.resize((512, 512), Image.Resampling.LANCZOS)
    im.save(dst, "PNG")


def main() -> int:
    if not V2_DIR.is_dir():
        print(f"[dataset-v3] 阻塞：v2 数据集缺失 {V2_DIR}")
        return 1
    OUT.mkdir(parents=True, exist_ok=True)

    seen: set[str] = set()
    n = 0

    # ① v2 全量复用（png 直拷保真；caption 同步写本地资产）
    for p in sorted(V2_DIR.glob("*.png")):
        shutil.copy2(p, OUT / p.name)
        seen.add(md5_of(p))
        (OUT / p.name).with_suffix(".txt").write_text(CAPTION, encoding="utf-8")
        n += 1

    # ② H3 v3 密集帧（md5 去重后中心方形裁剪）
    h3_in = 0
    for p in sorted(H3_FRAMES_V3.glob("*.png")):
        h = md5_of(p)
        if h in seen:
            continue
        seen.add(h)
        dst = OUT / f"h3v3_{p.stem}.png"
        center_square_512(p, dst)
        dst.with_suffix(".txt").write_text(CAPTION, encoding="utf-8")
        n += 1
        h3_in += 1

    # ③ 777 族挖掘过门样本（身份门 sim>=0.75 已由挖掘器把关）
    mine_in = 0
    for p in sorted(MINE_ACCEPTED.glob("*.png")):
        h = md5_of(p)
        if h in seen:
            continue
        seen.add(h)
        dst = OUT / f"mine777_{p.stem}.png"
        center_square_512(p, dst)
        dst.with_suffix(".txt").write_text(CAPTION, encoding="utf-8")
        n += 1
        mine_in += 1

    per_epoch = n * 10
    print(f"[dataset-v3] {n} 图（v2 {n - h3_in - mine_in} + h3v3 {h3_in} + mine777 {mine_in}）"
          f" -> {OUT}")
    print(f"[dataset-v3] 步数核算：{n} 图 x 10 repeats = {per_epoch} 步/epoch，"
          f"max_train_steps=2000 即 {2000 / per_epoch:.2f} epoch")
    print("[dataset-v3] 上传口径：只传 png（对齐 v2 实际训练形态，控制变量）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
