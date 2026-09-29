#!/usr/bin/env bash
# ==============================================================
# run_episode_build.sh — 集级构建编排（M4 扩产 · 动态镜头混排执行器）
# 结构：c1 静态合成（旁白）+ c2 静态合成（旁白）+ c3 动态适配（H3 对白镜）
#       → run_episode_concat.sh 串联 → {project}_full.mp4（1080p30）
# 用法：run_episode_build.sh <project_dir> <dynamic_mp4> <out_full.mp4>
# 说明：c3 位固定为对白镜（storyboard 第三镜带台词），动态素材自带
#       H3 内生对白音轨；样片阶段三集复用同 prompt 素材（seed 区分），
#       生产阶段按集定制 prompt（留证偏差说明见核算单）。
# ==============================================================
set -euo pipefail

PROJ="${1:?用法: run_episode_build.sh <project_dir> <dynamic_mp4> <out_full.mp4>}"
DYN="${2:?缺少动态镜头 mp4}"
OUT="${3:?缺少输出路径}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE="$REPO/scripts/run_clip_compose.sh"
DYNAMIC="$REPO/scripts/run_dynamic_clip.sh"
SB="$PROJ/storyboard/storyboard.v1.json"
TMP_EP="$(mktemp -d /tmp/yyc3_build.XXXXXX)"
trap 'rm -rf "$TMP_EP"' EXIT

# 1) 取前 3 镜文本（dialogue 优先，无对白用 description 作旁白）
mapfile -t TEXTS < <(python3 -c "
import json
sb = json.load(open('$SB'))
for s in sb['shots'][:3]:
    print((s.get('dialogue') or s.get('description') or '').strip() or '旁白')
")

echo "[build] 项目=$PROJ c1=「${TEXTS[0]:0:18}…」 c2=「${TEXTS[1]:0:18}…」 c3=动态对白镜"

# 2) c1/c2 静态合成（图 + TTS 旁白）
IMGS=("$PROJ"/images/*.png)
bash "$COMPOSE" "${IMGS[0]}" "${TEXTS[0]}" "$TMP_EP/c1.mp4"
bash "$COMPOSE" "${IMGS[1]}" "${TEXTS[1]}" "$TMP_EP/c2.mp4"

# 3) c3 动态镜头规格适配（H3 音视频联合生成，自带对白音轨）
bash "$DYNAMIC" "$DYN" "$TMP_EP/c3.mp4"

# 4) 串联成片（内建 ±1 帧/黑帧/规格验证）
bash "$REPO/scripts/run_episode_concat.sh" "$TMP_EP/c1.mp4" "$TMP_EP/c2.mp4" "$TMP_EP/c3.mp4" "$OUT"
