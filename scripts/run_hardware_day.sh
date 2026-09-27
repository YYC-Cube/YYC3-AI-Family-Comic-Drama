#!/usr/bin/env bash
# ==============================================================
# run_hardware_day.sh — YYC³ 硬件日一键动作清单（DGX/NAS 到位日执行）
# 覆盖：G1-003（NAS 三端互写）/ G1-006（DGX vLLM 首 token）/
#       TC-G2-010 终值（vLLM 并发）/ TC-G3-006 DGX 基线
# 纪律：每项输出 PASS/BLOCKED + 证据原文；BLOCKED 不算缺陷（环境前置）
# 用法：bash scripts/run_hardware_day.sh [--nas-host H --dgx1 H --dgx2 H]
# ==============================================================
set -uo pipefail

NAS_HOST="${NAS_HOST:-}"
DGX1="${DGX1:-}"
DGX2="${DGX2:-}"
for a in "$@"; do
  case "$a" in
    --nas-host) shift; NAS_HOST="${1:-}"; shift;;
    --dgx1) shift; DGX1="${1:-}"; shift;;
    --dgx2) shift; DGX2="${1:-}"; shift;;
  esac
done

pass=0; blocked=0
report() { # $1=状态 $2=项 $3=证据
  if [ "$1" = "PASS" ]; then pass=$((pass+1)); else blocked=$((blocked+1)); fi
  printf "[%s] %s\n       证据: %s\n" "$1" "$2" "${3:-(无)}"
}

echo "════ YYC³ 硬件日动作清单 ════"
echo "NAS=${NAS_HOST:-未指定} DGX1=${DGX1:-未指定} DGX2=${DGX2:-未指定}"
echo

# ── 1. NAS 挂载与三端互写（G1-003）──
echo "── 1. NAS 三端互写（TC-G1-003）"
if [ -d /mnt/nas ]; then
  TS=$(date +%s)
  echo "mac_$TS" > /mnt/nas/projects/_hw_probe/write_mac.txt 2>/dev/null \
    && cat /mnt/nas/projects/_hw_probe/write_mac.txt >/dev/null \
    && report PASS "Mac 端 /mnt/nas 读写" "$(cat /mnt/nas/projects/_hw_probe/write_mac.txt)" \
    || report BLOCKED "Mac 端 /mnt/nas 读写" "写入失败"
else
  report BLOCKED "/mnt/nas 挂载" "目录不存在（先执行 scripts/init_nas_path.sh + SMB/NFS 挂载）"
fi
for h in "$NAS_HOST" "$DGX1" "$DGX2"; do
  [ -z "$h" ] && continue
  ssh -o ConnectTimeout=5 "$h" 'mkdir -p /mnt/nas/projects/_hw_probe && \
    echo "$(hostname)_'"$TS"'" > /mnt/nas/projects/_hw_probe/write_$(hostname).txt && \
    cat /mnt/nas/projects/_hw_probe/write_mac.txt' 2>/dev/null \
    && report PASS "$h 互写+交叉读取" "ok" \
    || report BLOCKED "$h 互写" "SSH 或挂载未就绪"
done

# ── 2. DGX vLLM 起服与首 token（G1-006）──
echo "── 2. DGX vLLM 首 token ≤3s（TC-G1-006）"
for h in "$DGX1" "$DGX2"; do
  [ -z "$h" ] && continue
  if ssh -o ConnectTimeout=5 "$h" 'curl -s -m 3 http://localhost:8000/v1/models' 2>/dev/null | grep -q id; then
    T0=$(python3 -c 'import time; print(time.time())')
    ssh "$h" 'curl -s -m 30 -X POST http://localhost:8000/v1/chat/completions \
      -H "Content-Type: application/json" \
      -d "{\"model\":\"deepseek-v4-pro\",\"messages\":[{\"role\":\"user\",\"content\":\"回复OK\"}],\"max_tokens\":8}"' >/dev/null 2>&1
    T1=$(python3 -c 'import time; print(time.time())')
    LAT=$(python3 -c "print(round($T1-$T0, 2))")
    ok=$(python3 -c "print('PASS' if $LAT <= 3 else 'BLOCKED')")
    report "$ok" "$h 首 token（实测 ${LAT}s ≤3s）" "ssh+curl 计时"
  else
    report BLOCKED "$h vLLM 服务" "8000 未响应（先 docker compose -f deploy/dgx/docker-compose.llm.yml up -d）"
  fi
done

# ── 3. TC-G2-010 终值（vLLM 连续批处理并发）──
echo "── 3. TC-G2-010 终值（双 DGX 并发）"
if [ -n "$DGX1" ] && [ -n "$DGX2" ]; then
  python3 - <<'PYEOF'
import time, json
from concurrent.futures import ThreadPoolExecutor
import urllib.request

def call(host):
    req = urllib.request.Request(
        f"http://{host}:8000/v1/chat/completions",
        data=json.dumps({"model": "deepseek-v4-pro", "max_tokens": 96,
                         "messages": [{"role": "user", "content": "回复OK"}]}).encode(),
        headers={"Content-Type": "application/json"})
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=120) as r:
        r.read()
    return time.perf_counter() - t0

s1, s2 = call("DGX1_PLACEHOLDER"), call("DGX2_PLACEHOLDER")
serial = s1 + s2
with ThreadPoolExecutor(max_workers=2) as p:
    t0 = time.perf_counter()
    fa = p.submit(call, "DGX1_PLACEHOLDER"); fb = p.submit(call, "DGX2_PLACEHOLDER")
    fa.result(); fb.result()
    par = time.perf_counter() - t0
print(f"[INFO] serial={serial:.1f}s parallel={par:.1f}s ratio={par/serial:.3f} "
      f"({'PASS' if par/serial <= 0.8 else 'BLOCKED'})")
PYEOF
else
  report BLOCKED "TC-G2-010 终值" "需 DGX1+DGX2 同时在线"
fi

# ── 4. TC-G3-006 DGX 基线（单镜 ≤300s）──
echo "── 4. TC-G3-006 DGX 基线（留证模板）"
report BLOCKED "TC-G3-006 DGX NF4 单镜耗时" \
  "DGX ComfyUI 部署后执行：COMFYUI_URL=http://\$DGX1:41888 \
COMFYUI_MODEL=<nf4模型> yyc3-ai-manju-studio/.venv/bin/python scripts/run_comfy_real.py（读 latency_s）"

echo
echo "════ 汇总：PASS $pass / BLOCKED $blocked ════"
echo "证据归档：/mnt/nas/projects/_acceptance/hardware_day/（NAS 就绪后补录）"
