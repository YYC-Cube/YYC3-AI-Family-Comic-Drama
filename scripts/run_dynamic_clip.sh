#!/usr/bin/env bash
# ==============================================================
# run_dynamic_clip.sh — H3 动态镜头规格适配（M4 扩产 · 动态混排执行器）
# 输入：H3 Ref2VA 产物 mp4（如 640x384@24，音视频联合生成）→
#       ffmpeg 等比覆盖 16:9 居中裁切 → 1920x1080@30 H.264+AAC
# 与 run_clip_compose.sh 产物同规格 → 可直接进 run_episode_concat.sh 混排
# 用法：bash scripts/run_dynamic_clip.sh <h3_clip.mp4> <out.mp4>
# 说明：防变形采用 compose 同款 increase+crop（直拼 concat 的 scale 滤镜
#       会把 5:3 拉伸到 16:9，垂直变形 6.7%）
# ==============================================================
set -euo pipefail

SRC="${1:?用法: run_dynamic_clip.sh <h3_clip.mp4> <out.mp4>}"
OUT="${2:?缺少输出路径}"

# 画幅可选（2026-10-05 平台适配）：与 run_clip_compose.sh 同款（16:9 默认/9:16/1:1）
# 注意：H3 源为 ~5:3 横画幅，9:16 档下裁切左右损失约 48% 宽度——
#       动态镜竖版建议优先 blur-pad 转制（run_vertical_transcode.py）
ASPECT="${ASPECT:-16:9}"
case "$ASPECT" in
  16:9) W=1920; H=1080 ;;
  9:16) W=1080; H=1920 ;;
  1:1)  W=1080; H=1080 ;;
  *) echo "ASPECT 仅支持 16:9|9:16|1:1（当前：$ASPECT）"; exit 1 ;;
esac

echo "[1/2] 动态镜头规格适配（H.264+AAC → ${W}x${H}@30（ASPECT=${ASPECT}），等比覆盖居中裁切）…"
# 音频 32kHz → 128k AAC 重编；时长以源为准（H3 为音视频联合生成，内生同步）
ffmpeg -y -i "$SRC" \
  -c:v libx264 -pix_fmt yuv420p -r 30 \
  -vf "scale=${W}:${H}:force_original_aspect_ratio=increase,crop=${W}:${H}" \
  -c:a aac -b:a 128k "$OUT" 2>&1 | tail -2

echo "[2/2] 校验产物（TC-G4-001 交付规格）…"
ffprobe -v error -show_entries format=duration,size -show_entries stream=codec_name,width,height,r_frame_rate \
  -of default=noprint_wrappers=1 "$OUT"
echo "完成：${OUT}（源：${SRC}）"
