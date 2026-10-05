#!/usr/bin/env bash
# ==============================================================
# run_clip_compose.sh — 单镜头音视频合成链（M4 前置 · ③）
# 输入：关键帧 PNG + 台词文本 → TTS(piper) → ffmpeg 合成 MP4（H.264+AAC）
# 用法：bash scripts/run_clip_compose.sh <image.png> "台词文本" <out.mp4>
# 说明：本脚本为 Bash 固定参数流水线（DramaToolGateway.compose 的服务化
#       前身）；生产化后封装为 4xxxx 段的 compose 服务
# ==============================================================
set -euo pipefail

IMG="${1:?用法: run_clip_compose.sh <image.png> <台词> <out.mp4>}"
TEXT="${2:?缺少台词文本}"
OUT="${3:?缺少输出路径}"
VENV_PY="/Users/yanyu/YYC-Cube/YYC3 AI Family-Comic Drama/yyc3-ai-manju-studio/.venv/bin/python"
VOICE_DIR="/Users/yanyu/YYC-Cube/tools/piper-voices"
TMP_WAV="$(dirname "$OUT")/_tts_$(basename "$OUT" .mp4).wav"

# 画幅可选（2026-10-05 平台适配）：ASPECT=16:9(默认·B站)/9:16(抖音·TikTok·Shorts)/1:1(信息流)
# 静态镜源为 1024x1024 方图——画幅仅在合成层决策，原生竖/横重渲无需重跑生成
ASPECT="${ASPECT:-16:9}"
case "$ASPECT" in
  16:9) W=1920; H=1080 ;;
  9:16) W=1080; H=1920 ;;
  1:1)  W=1080; H=1080 ;;
  *) echo "ASPECT 仅支持 16:9|9:16|1:1（当前：$ASPECT）"; exit 1 ;;
esac

echo "[1/3] TTS 合成（piper zh_CN-huayan-medium）…"
"$VENV_PY" - "$TEXT" "$TMP_WAV" "$VOICE_DIR" <<'PYEOF'
import io, sys, wave
from piper import PiperVoice

text, out_wav, voice_dir = sys.argv[1], sys.argv[2], sys.argv[3]
voice = PiperVoice.load(f"{voice_dir}/zh_CN-huayan-medium.onnx")
chunks = voice.synthesize(text)
pcm = b"".join(c.audio_int16_bytes for c in chunks)
buf = io.BytesIO()
with wave.open(buf, "wb") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(voice.config.sample_rate)
    w.writeframes(pcm)
open(out_wav, "wb").write(buf.getvalue())
print(f"      wav={len(buf.getvalue())} bytes rate={voice.config.sample_rate}")
PYEOF

echo "[2/3] ffmpeg 合成（H.264 + AAC，交付规格 ${W}x${H}@30（ASPECT=${ASPECT}），时长=音轨）…"
# TC-G4-001 交付规格：1080p 级 / 30fps / H.264 / AAC（横竖方三档可选）
# 方形原图（1024x1024）→ 等比放大覆盖目标画幅后居中裁切，避免拉伸变形
ffmpeg -y -loop 1 -i "$IMG" -i "$TMP_WAV" \
  -c:v libx264 -tune stillimage -pix_fmt yuv420p -r 30 \
  -vf "scale=${W}:${H}:force_original_aspect_ratio=increase,crop=${W}:${H}" \
  -c:a aac -b:a 128k -shortest "$OUT" 2>&1 | tail -2

echo "[3/3] 校验产物（TC-G4-001 规格）…"
ffprobe -v error -show_entries format=duration,size -show_entries stream=codec_name,width,height,r_frame_rate \
  -of default=noprint_wrappers=1 "$OUT"
echo "完成：${OUT}（音轨：${TMP_WAV}）"
