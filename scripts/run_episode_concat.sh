#!/usr/bin/env bash
# ==============================================================
# run_episode_concat.sh — 集级串联成片（M4 · TC-G4-003 执行器）
# 用法：bash scripts/run_episode_concat.sh <c1.mp4> <c2.mp4> ... <out.mp4>
# 方法论（TC-G4-003 三轮实测定版 2026-09-28）：
#   ✗ 流拷贝 -c copy       → 每文件 AAC priming 累积，偏差 ~47ms（>1 帧）
#   ✗ 视频拷贝+音频重编    → 仍累积，偏差 ~70ms
#   ✓ 全重编码单时间线      → 帧对齐，视频轨偏差 20.3ms（<1 帧 @30fps）PASS
# 判定基准：±1 帧按「视频轨时长」计（格式时长含 AAC padding，为编码器
#   物理产物非内容偏差，不计入判定——YYC3-60 TC-G4-003 同步修订）
# ==============================================================
set -euo pipefail

if [ $# -lt 3 ]; then
  echo "用法: run_episode_concat.sh <clip1.mp4> <clip2.mp4> ... <out.mp4>"
  exit 1
fi

OUT="${@: -1}"
CLIPS=("${@:1:$#-1}")
TMPDIR_EP="$(mktemp -d /tmp/yyc3_concat.XXXXXX)"
trap 'rm -rf "$TMPDIR_EP"' EXIT

# 1) concat 清单（按参数顺序 = 分镜顺序）
LIST="$TMPDIR_EP/concat.txt"
for c in "${CLIPS[@]}"; do
  echo "file '$c'" >> "$LIST"
done

# 2) 全重编码串联（单时间线帧对齐，交付规格 1920x1080@30 H.264+AAC）
echo "[1/2] 串联 ${#CLIPS[@]} 镜（全重编码，帧对齐）…"
ffmpeg -y -f concat -safe 0 -i "$LIST" \
  -vf "fps=30,scale=1920:1080" \
  -c:v libx264 -pix_fmt yuv420p -c:a aac -b:a 128k "$OUT" 2>&1 | tail -1

# 3) 验证：视频轨时长 vs 各镜之和（±1 帧）、黑帧、规格
echo "[2/2] 验证（TC-G4-003）…"
SUM=0
for c in "${CLIPS[@]}"; do
  D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$c")
  SUM=$(python3 -c "print($SUM + $D)")
done
OUT_V=$(ffprobe -v error -select_streams v:0 -show_entries stream=duration -of csv=p=0 "$OUT")
OUT_F=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")
python3 -c "
s=$SUM; v=$OUT_V; f=$OUT_F
print(f'各镜和:{s:.4f}s 成片视频轨:{v:.4f}s 偏差:{abs(v-s)*1000:.1f}ms（容差 33.3ms/1帧，按视频轨计）')
print('时长判定:', 'PASS' if abs(v-s) <= 1/30 else 'FAIL')"
BLACK=$(ffmpeg -i "$OUT" -vf blackdetect=d=0.1:pix_th=0.10 -an -f null - 2>&1 | grep -c blackdetect || true)
echo "黑帧检测: ${BLACK} 处（0=通过）"
echo "规格: $(ffprobe -v error -select_streams v:0 -show_entries stream=codec_name,width,height,r_frame_rate -of csv=p=0 "$OUT")"
echo "完成：${OUT}"
