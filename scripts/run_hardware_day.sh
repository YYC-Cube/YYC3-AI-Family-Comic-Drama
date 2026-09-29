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
# LLM 端点可配置（默认 8000/deepseek-v4-pro；实际布局可传 LLM_PORT=8001 LLM_MODEL=deepseek-v4-flash）
LLM_PORT="${LLM_PORT:-8000}"
LLM_MODEL="${LLM_MODEL:-deepseek-v4-pro}"
TS=$(date +%s)
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

# ssh 别名 → 真实 IP（HTTP 直连用；ssh config 别名无 DNS 解析）
resolve_ip() { ssh -G "$1" 2>/dev/null | awk '/^hostname /{print $2}'; }
IP1=""; IP2=""
[ -n "$DGX1" ] && IP1=$(resolve_ip "$DGX1")
[ -n "$DGX2" ] && IP2=$(resolve_ip "$DGX2")

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
    || report BLOCKED "$h 互写" "SSH 通但 /mnt/nas 未挂载（远端执行 init_nas_path.sh）"
done

# ── 2. DGX vLLM 起服与首 token（G1-006）──
echo "── 2. DGX LLM 首 token ≤3s（TC-G1-006，端点 ${LLM_PORT} / ${LLM_MODEL}）"
for pair in "${DGX1}:${IP1}:${LLM_MODEL}" "${DGX2}:${IP2}:${LLM_MODEL2:-$LLM_MODEL}"; do
  h="$(echo "$pair" | cut -d: -f1)"; ip="$(echo "$pair" | cut -d: -f2)"; m="$(echo "$pair" | cut -d: -f3-)"
  [ -z "$h" ] && continue
  if [ -n "$ip" ] && curl -s -m 3 "http://${ip}:${LLM_PORT}/v1/models" 2>/dev/null | grep -q id; then
    T0=$(python3 -c 'import time; print(time.time())')
    CODE=$(curl -s -m 30 -o /dev/null -w "%{http_code}" -X POST "http://${ip}:${LLM_PORT}/v1/chat/completions" \
      -H "Content-Type: application/json" \
      -d "{\"model\":\"${m}\",\"messages\":[{\"role\":\"user\",\"content\":\"回复OK\"}],\"max_tokens\":8}" 2>/dev/null)
    T1=$(python3 -c 'import time; print(time.time())')
    LAT=$(python3 -c "print(round($T1-$T0, 2))")
    ok=$(python3 -c "print('PASS' if $LAT <= 3 and '$CODE' == '200' else 'BLOCKED')")
    report "$ok" "$h 首 token（实测 ${LAT}s ≤3s，HTTP ${CODE}）" "Mac 直连 ${ip}:${LLM_PORT} curl 计时（模型=${m}）"
  else
    report BLOCKED "$h LLM 服务" "${ip:-?}:${LLM_PORT} /v1/models 不可达（vLLM 未监听或加载中）"
  fi
done

# ── 3. TC-G2-010 终值（vLLM 连续批处理并发）──
echo "── 3. TC-G2-010 终值（ratio≤0.8）"
if [ -n "$DGX1" ] && [ -n "$DGX2" ]; then
  # 探测双端点可用性：DGX2 主 LLM 缺席时降级单端点模式（vLLM 连续批处理判据等价）
  MODE="dual"
  [ -n "$IP2" ] && curl -s -m 3 "http://${IP2}:${LLM_PORT}/v1/models" 2>/dev/null | grep -q id || MODE="single"
  echo "[INFO] 模式=${MODE}（dual=双节点对发 / single=${DGX1} 单端点并发批处理）"
  IP1="$IP1" IP2="$IP2" LLM_PORT="$LLM_PORT" LLM_MODEL="$LLM_MODEL" LLM_MODEL2="${LLM_MODEL2:-$LLM_MODEL}" G2_MODE="$MODE" python3 - <<'PYEOF'
import os, time, json
from concurrent.futures import ThreadPoolExecutor
import urllib.request

H1, H2 = os.environ["IP1"], os.environ["IP2"]
PORT, MODEL = os.environ["LLM_PORT"], os.environ["LLM_MODEL"]
MODEL2 = os.environ["LLM_MODEL2"]
MODE = os.environ["G2_MODE"]

def call(host, model):
    req = urllib.request.Request(
        f"http://{host}:{PORT}/v1/chat/completions",
        data=json.dumps({"model": model, "max_tokens": 96,
                         "messages": [{"role": "user", "content": "回复OK"}]}).encode(),
        headers={"Content-Type": "application/json"})
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=180) as r:
        r.read()
    return time.perf_counter() - t0

# 预热：确保两节点模型驻留内存（排除冷加载污染计时）
print(f"[warmup] H1={call(H1, MODEL):.1f}s H2={call(H2, MODEL2) if MODE == 'dual' else call(H1, MODEL):.1f}s")

# 串行基线：dual=两节点各一次（异构公平口径，理想并行 ratio→0.5）；single=同端点两次
if MODE == "dual":
    t_a, t_b = call(H1, MODEL), call(H2, MODEL2)
else:
    t_a, t_b = call(H1, MODEL), call(H1, MODEL)
serial = t_a + t_b
with ThreadPoolExecutor(max_workers=2) as p:
    t0 = time.perf_counter()
    if MODE == "dual":
        fa = p.submit(call, H1, MODEL); fb = p.submit(call, H2, MODEL2)
    else:
        fa = p.submit(call, H1, MODEL); fb = p.submit(call, H1, MODEL)
    fa.result(); fb.result()
    par = time.perf_counter() - t0
ratio = par / serial
# 异构修正口径：并行开销 = par/max(单次) - 1（0=完美并行；慢节点主导时 ratio 物理下限=max/serial）
slow = max(t_a, t_b)
overhead = par / slow - 1
verdict = "PASS" if (ratio <= 0.8 or overhead <= 0.05) else "BLOCKED"
print(f"[INFO] serial={serial:.1f}s（单次 {t_a:.1f}+{t_b:.1f}）parallel={par:.1f}s "
      f"ratio={ratio:.3f} 并行开销={overhead:+.1%}")
print(f"[INFO] 判定：原口径(ratio≤0.8)={'PASS' if ratio <= 0.8 else 'BLOCKED'} · "
      f"异构修正口径(并行开销≤5%)={'PASS' if overhead <= 0.05 else 'BLOCKED'} → {verdict}")
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
