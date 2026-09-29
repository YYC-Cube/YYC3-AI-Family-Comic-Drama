#!/usr/bin/env bash
# ==============================================================
# run_episode_concat.sh — 集级串联成片（M4 · TC-G4-003 执行器）
# 用法：bash scripts/run_episode_concat.sh <c1.mp4> <c2.mp4> ... <out.mp4>
# 方法论（TC-G4-003 三轮实测定版 2026-09-28 + 扩产修订 2026-09-29）：
#   ✗ 流拷贝 -c copy       → 每文件 AAC priming 累积，偏差 ~47ms（>1 帧）
#   ✗ 视频拷贝+音频重编    → 仍累积，偏差 ~70ms
#   ✓ 全重编码单时间线      → 帧对齐，视频轨偏差 20.3ms（静态同质镜 PASS）
#   ✓✓ concat filter 解码域拼接（扩产定版）→ concat demuxer 在混排源
#      （H3 动态镜 + compose 静态镜）下尾部音频帧整体丢失（ep02 实测
#      音频流 9.57s < 视频 12.53s，aresample=async 亦不可修复），
#      filter 级 concat 规避 demuxer pts/priming 缺陷
# 判定基准：±1 帧按「视频轨时长」计（格式时长含 AAC padding，为编码器
#   物理产物非内容偏差，不计入判定——YYC3-60 TC-G4-003 同步修订）
#   音频轨时长应 ≈ 视频轨时长（± AAC 一帧粒度），混排后必须复验
# ==============================================================
set -euo pipefail

if [ $# -lt 3 ]; then
  echo "用法: run_episode_concat.sh <clip1.mp4> <clip2.mp4> ... <out.mp4>"
  exit 1
fi

OUT="${@: -1}"
CLIPS=("${@:1:$#-1}")
N=${#CLIPS[@]}

# 1) 构造 concat filter（解码域拼接：视频统一 1080p30 CFR，音频统一 32k stereo）
FC=""
IDX=""
for ((i=0; i<N; i++)); do
  FC+="[$i:v]fps=30,scale=1920:1080,setsar=1[v$i];"
  FC+="[$i:a]aresample=32000,aformat=sample_fmts=fltp:channel_layouts=stereo[a$i];"
  IDX+="[v$i][a$i]"
done
FC+="${IDX}concat=n=${N}:v=1:a=1[v][a]"

echo "[1/2] 串联 ${N} 镜（concat filter 解码域拼接，帧对齐 + 音频全域统一）…"
IN=()
for c in "${CLIPS[@]}"; do IN+=(-i "$c"); done
ffmpeg -y "${IN[@]}" -filter_complex "$FC" \
  -map "[v]" -map "[a]" \
  -c:v libx264 -pix_fmt yuv420p -c:a aac -b:a 128k "$OUT" 2>&1 | tail -1

# 2) 验证：视频轨时长 vs 各镜之和（±1 帧）、音频轨齐平、黑帧、规格
echo "[2/2] 验证（TC-G4-003）…"
SUM=0
for c in "${CLIPS[@]}"; do
  D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$c")
  SUM=$(python3 -c "print($SUM + $D)")
done
OUT_V=$(ffprobe -v error -select_streams v:0 -show_entries stream=duration -of csv=p=0 "$OUT")
OUT_A=$(ffprobe -v error -select_streams a:0 -show_entries stream=duration -of csv=p=0 "$OUT")
python3 -c "
s=$SUM; v=$OUT_V; a=$OUT_A
print(f'各镜和:{s:.4f}s 成片视频轨:{v:.4f}s 偏差:{abs(v-s)*1000:.1f}ms（容差 33.3ms/1帧，按视频轨计）')
print('时长判定:', 'PASS' if abs(v-s) <= 1/30 else 'FAIL')
print(f'音频轨:{a:.4f}s 视频轨:{v:.4f}s 差:{abs(a-v)*1000:.1f}ms（音频齐平判定）:', 'PASS' if abs(a-v) <= 0.1 else 'FAIL')"
BLACK=$(ffmpeg -i "$OUT" -vf blackdetect=d=0.1:pix_th=0.10 -an -f null - 2>&1 | grep -c blackdetect || true)
echo "黑帧检测: ${BLACK} 处（0=通过）"
echo "规格: $(ffprobe -v error -select_streams v:0 -show_entries stream=codec_name,width,height,r_frame_rate -of csv=p=0 "$OUT")"
echo "完成：${OUT}"
