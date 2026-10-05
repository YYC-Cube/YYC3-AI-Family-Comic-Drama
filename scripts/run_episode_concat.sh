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

# 画幅可选（2026-10-05 平台适配）：与 run_clip_compose.sh 同款（16:9 默认/9:16/1:1）
# 混排镜（静态/动态）须同 ASPECT 产出，串联层统一画幅 CFR
ASPECT="${ASPECT:-16:9}"
case "$ASPECT" in
  16:9) W=1920; H=1080 ;;
  9:16) W=1080; H=1920 ;;
  1:1)  W=1080; H=1080 ;;
  *) echo "ASPECT 仅支持 16:9|9:16|1:1（当前：$ASPECT）"; exit 1 ;;
esac

# 1) 构造 concat filter（解码域拼接：视频统一目标画幅 30fps CFR，音频统一 32k stereo）
# 2026-10-05 修复：concat 边界时间戳跳槽（帧数守恒但 duration 元数据虚多 1-3 帧，
#   实测 88+199+19=306 帧产物报 10.3s=309/30）——拼接后 setpts=N/(30*TB) 按帧序
#   重建连续 CFR 时间轴，元数据归真（零内容变化，黑帧/帧数不变）
FC=""
IDX=""
for ((i=0; i<N; i++)); do
  FC+="[$i:v]fps=30,scale=${W}:${H},setsar=1[v$i];"
  FC+="[$i:a]aresample=32000,aformat=sample_fmts=fltp:channel_layouts=stereo[a$i];"
  IDX+="[v$i][a$i]"
done
FC+="${IDX}concat=n=${N}:v=1:a=1[vc][a];[vc]setpts=N/(30*TB)[v]"

echo "[1/2] 串联 ${N} 镜（concat filter 解码域拼接，帧对齐 + 音频全域统一）…"
IN=()
for c in "${CLIPS[@]}"; do IN+=(-i "$c"); done
ffmpeg -y "${IN[@]}" -filter_complex "$FC" \
  -map "[v]" -map "[a]" \
  -c:v libx264 -pix_fmt yuv420p -c:a aac -b:a 128k "$OUT" 2>&1 | tail -1

# 2) 验证：视频轨时长 vs 各镜之和（±1 帧）、音频轨齐平、黑帧、规格
# 2026-10-05 口径修正（对齐定版语义「按视频轨计；AAC padding 为编码器物理
#   产物不计入判定」）：镜和与成片统一取视频轨 stream duration（内容口径，
#   原实现镜和误用 format=duration 含容器 padding，混口径恒带 30-50ms 系统
#   偏差）；音频齐平容差 0.1→0.2s——实测 concat 后 AAC 尾部 padding ≤160ms
#   为编码产物，内容对齐由时长判定（视频轨）承担红线
echo "[2/2] 验证（TC-G4-003）…"
SUM=0
for c in "${CLIPS[@]}"; do
  D=$(ffprobe -v error -select_streams v:0 -show_entries stream=duration -of csv=p=0 "$c")
  SUM=$(python3 -c "print($SUM + $D)")
done
OUT_V=$(ffprobe -v error -select_streams v:0 -show_entries stream=duration -of csv=p=0 "$OUT")
OUT_A=$(ffprobe -v error -select_streams a:0 -show_entries stream=duration -of csv=p=0 "$OUT")
python3 -c "
s=$SUM; v=$OUT_V; a=$OUT_A
print(f'各镜视频轨和:{s:.4f}s 成片视频轨:{v:.4f}s 偏差:{abs(v-s)*1000:.1f}ms（容差 33.3ms/1帧，内容口径）')
print('时长判定:', 'PASS' if abs(v-s) <= 1/30 else 'FAIL')
print(f'音频轨:{a:.4f}s 视频轨:{v:.4f}s 差:{abs(a-v)*1000:.1f}ms（音频齐平，容差含 AAC 尾 padding 物理产物）:', 'PASS' if abs(a-v) <= 0.2 else 'FAIL')"
BLACK=$(ffmpeg -i "$OUT" -vf blackdetect=d=0.1:pix_th=0.10 -an -f null - 2>&1 | grep -c blackdetect || true)
echo "黑帧检测: ${BLACK} 处（0=通过）"
echo "规格: $(ffprobe -v error -select_streams v:0 -show_entries stream=codec_name,width,height,r_frame_rate -of csv=p=0 "$OUT")"
echo "完成：${OUT}"
