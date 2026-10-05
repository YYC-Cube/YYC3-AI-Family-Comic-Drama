#!/usr/bin/env bash
# ==============================================================
# run_sdxl_train_n1.sh — SDXL LoRA 阶段 2 重训（YYC3-62 §五，n1 DGX Spark）
# 链路：v2 数据集（19 图）上采样 1024 → kohya sdxl_train_network.py 重训
# 配方：v2 生产配方原样复用（自 safetensors 元数据恢复口径，G4 §16.1）——
#   dim32/alpha16 · lr 5e-4 constant · AdamW · bf16 · bucket no_upscale ·
#   keep_tokens 1 · seed 42 · 2000 步 + 每 500 步存档（五件产物口径）
# SDXL 增量：上采样 1024（对齐原生分辨率，沿用 v2m777 LANCZOS 先例）+
#   sdxl_train_network.py 入口；HF 离线变量沿用（G4 §13.2 排障沉淀）
# 用法：本机执行  bash scripts/run_sdxl_train_n1.sh launch   # 上传+启动
#                  bash scripts/run_sdxl_train_n1.sh status   # 看进度尾部
#                  bash scripts/run_sdxl_train_n1.sh pull     # 回拉五件产物
# ==============================================================
set -euo pipefail
N1="yyc3-n1"
REMOTE_ROOT="\$HOME"
TRAIN_LOG="\$HOME/train_sdxl_v1.log"
OUT_DIR="\$HOME/kohya_out_sdxl"

cmd="$1"

case "$cmd" in
launch)
  ssh "$N1" 'bash -s' <<'REMOTE'
set -euo pipefail
# ① 数据集上采样 512/384 → 1024（LANCZOS，v2m777 先例；caption 原样复制）
SRC="$HOME/datasets/kohya_dataset_v2/train/10_sdhero"
DST="$HOME/datasets/kohya_dataset_sdxl_v2/train/10_sdhero"
rm -rf "$HOME/datasets/kohya_dataset_sdxl_v2"
mkdir -p "$DST"
"$HOME/venvs/kohya/bin/python" - "$SRC" "$DST" <<'PY'
import sys, shutil
from pathlib import Path
from PIL import Image
src, dst = Path(sys.argv[1]), Path(sys.argv[2])
n = 0
for p in sorted(src.glob("*.png")):
    im = Image.open(p).convert("RGB")
    if im.size != (1024, 1024):
        im = im.resize((1024, 1024), Image.Resampling.LANCZOS)
    im.save(dst / p.name, "PNG")
    cap = p.with_suffix(".txt")
    if cap.exists():
        shutil.copy(cap, dst / cap.name)
    n += 1
print(f"[sdxl-dataset] {n} 图上采样→1024 + caption → {dst}")
PY
# 注：~/models 为 root 属主不可写（2026-10-05 实测 rsync 挂起根因），基模落 ~/sdxl_models
[ -f "$HOME/sdxl_models/DreamShaperXL_Lightning.safetensors" ] || { echo "基模缺失：~/sdxl_models/DreamShaperXL_Lightning.safetensors"; exit 1; }

# ② 训练（nohup 后台；配方=v2 元数据恢复口径 + SDXL 入口）
# 排障（2026-10-05 首启失败）：HF_HUB_OFFLINE=1 会使单文件 ckpt 的 tokenizer
# 解析为 None（vocab_file None → TypeError）；改走 hf-mirror 在线解析（tokenizer
# 仅 ~2MB，SD15 时代 4:38 挂起系未设 HF_ENDPOINT 直连 HF 所致）
cd "$HOME/tools/sd-scripts"
rm -f "$HOME/train_sdxl_v1.log"
nohup env HF_ENDPOINT=https://hf-mirror.com \
  "$HOME/venvs/kohya/bin/python" sdxl_train_network.py \
    --pretrained_model_name_or_path "$HOME/sdxl_models/DreamShaperXL_Lightning.safetensors" \
    --train_data_dir "$HOME/datasets/kohya_dataset_sdxl_v2/train" \
    --output_dir "$HOME/kohya_out_sdxl" \
    --output_name sd-hero-xl-v1 \
    --network_module networks.lora \
    --network_dim 32 --network_alpha 16 \
    --learning_rate 5e-4 --lr_scheduler constant \
    --optimizer_type AdamW \
    --max_train_steps 2000 --save_every_n_steps 500 \
    --save_precision bf16 --mixed_precision bf16 \
    --resolution "1024,1024" \
    --enable_bucket --min_bucket_reso 512 --max_bucket_reso 1024 --bucket_no_upscale \
    --keep_tokens 1 --seed 42 --gradient_checkpointing \
    --cache_latents --cache_latents_to_disk \
    > "$HOME/train_sdxl_v1.log" 2>&1 &
echo "[launch] 训练已启动 pid=$! log=~/train_sdxl_v1.log"
REMOTE
  ;;
status)
  ssh "$N1" 'tail -5 ~/train_sdxl_v1.log | cut -c1-200; echo ---; grep -cE "^steps: [0-9]+" ~/train_sdxl_v1.log 2>/dev/null || true; ls ~/kohya_out_sdxl 2>/dev/null'
  ;;
pull)
  mkdir -p /tmp/kohya_out_sdxl
  rsync -a "$N1:~/kohya_out_sdxl/sd-hero-xl-v1*.safetensors" /tmp/kohya_out_sdxl/
  rsync -a "$N1:~/train_sdxl_v1.log" /tmp/kohya_out_sdxl/
  /bin/ls -la /tmp/kohya_out_sdxl/
  ;;
*)
  echo "用法: $0 {launch|status|pull}"; exit 1
  ;;
esac
