#!/usr/bin/env bash
# ==============================================================
# comfyui_guardian.sh — ComfyUI 守护进程（M3 稳定性治理 · ②）
# 行为：--force-fp16 启动（降 MPS 内存/负载）；进程退出后 5s 自动重启；
#       每次退出记录时间与原因线索到 /tmp/comfyui_guardian.log
# 用法：bash scripts/comfyui_guardian.sh [port]（默认 41888；停止=杀本脚本）
# ==============================================================
PORT="${1:-41888}"
COMFY_DIR="/Users/yanyu/YYC-Cube/tools/ComfyUI"
LOG="/tmp/comfyui_guardian.log"

echo "[guardian] start port=$PORT fp16=on $(date)" >> "$LOG"
while true; do
  cd "$COMFY_DIR" || exit 1
  # --force-fp16：MPS 下显著降内存与功耗（第九轮被系统杀的缓解项）
  ".venv/bin/python" main.py --port "$PORT" --listen 127.0.0.1 --force-fp16
  code=$?
  echo "[guardian] ComfyUI exited code=$code at $(date) — restart in 5s" >> "$LOG"
  sleep 5
done
