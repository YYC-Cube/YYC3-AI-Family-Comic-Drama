#!/bin/bash
# ==============================================================
# gewuzongshi_reload_quality_rules.sh — 格物·宗师质检规则热重载（阶段二件）
# 状态：⚠️ 网关路由 /agent/gewuzongshi/reload_quality_rules 未部署——
#   本脚本在 Agent 化阶段二（YYC3-67 §六/YYC3-72 §五）网关就绪后启用；
#   当前 CLI 范式（run_quality_review.py 无状态）每次执行即新规则，天然热生效。
# 设计：预检 dry_run=true（只解析校验不生效）→ 人工确认 → 正式重载
# 前置：curl + jq；密钥经 .env 注入（不入库，已 .gitignore）
# 用法：cp scripts/gewuzongshi_reload_quality_rules.sh /tmp/ && 配置 .env 后执行
# ==============================================================
set -euo pipefail

# 加载环境变量（.env 不入库：API_ENDPOINT / GATEWAY_API_KEY / RULE_FILE / VERSION_TAG）
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi
: "${API_ENDPOINT:?需在 .env 配置 API_ENDPOINT}"
: "${GATEWAY_API_KEY:?需在 .env 配置 GATEWAY_API_KEY}"
RULE_FILE="${RULE_FILE:-agent_quality_rules.yaml}"
VERSION_TAG="${VERSION_TAG:-m1_final_20261005}"
TRACE_ID="trace_gewu_reload_$(date +%Y%m%d_%H%M%S)"

echo "============================================="
echo "格物·宗师 质检规则热重载 | 版本: ${VERSION_TAG}"
echo "TraceID: ${TRACE_ID}"
echo "============================================="

echo "[1/2] 预检 dry_run=true"
PRE_RESP=$(curl -s -X POST "${API_ENDPOINT}" \
  -H "Authorization: Bearer ${GATEWAY_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"rule_file": "'"${RULE_FILE}"'", "version_tag": "'"${VERSION_TAG}"'",
        "dry_run": true, "trace_id": "'"${TRACE_ID}"'"}')
echo "$PRE_RESP" | jq .
[ "$(echo "$PRE_RESP" | jq -r '.status')" = "success" ] || { echo "❌ 预检失败，终止"; exit 1; }

read -p "确认正式重载？输入 yes 继续: " CONFIRM
[ "${CONFIRM}" = "yes" ] || { echo "⏹️ 已取消，规则未变更"; exit 0; }

echo "[2/2] 正式热重载 dry_run=false"
REAL_RESP=$(curl -s -X POST "${API_ENDPOINT}" \
  -H "Authorization: Bearer ${GATEWAY_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"rule_file": "'"${RULE_FILE}"'", "version_tag": "'"${VERSION_TAG}"'",
        "dry_run": false, "trace_id": "'"${TRACE_ID}"'"}')
echo "$REAL_RESP" | jq .
if [ "$(echo "$REAL_RESP" | jq -r '.status')" = "reloaded" ]; then
  echo "🎉 热重载完成：${VERSION_TAG}（新任务用新规则，在途任务沿用旧规则）"
else
  echo "❌ 正式重载失败"; exit 1
fi
