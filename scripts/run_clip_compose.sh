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

echo "[2/3] ffmpeg 合成（H.264 + AAC，交付规格 1920x1080@30，时长=音轨）…"
# TC-G4-001 交付规格：1920x1080 / 30fps / H.264 / AAC
# 方形原图（1024x1024）→ 等比放大覆盖 16:9 后居中裁切，避免拉伸变形
ffmpeg -y -loop 1 -i "$IMG" -i "$TMP_WAV" \
  -c:v libx264 -tune stillimage -pix_fmt yuv420p -r 30 \
  -vf "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080" \
  -c:a aac -b:a 128k -shortest "$OUT" 2>&1 | tail -2

echo "[3/3] 校验产物（TC-G4-001 规格）…"
ffprobe -v error -show_entries format=duration,size -show_entries stream=codec_name,width,height,r_frame_rate \
  -of default=noprint_wrappers=1 "$OUT"
echo "完成：${OUT}（音轨：${TMP_WAV}）"
