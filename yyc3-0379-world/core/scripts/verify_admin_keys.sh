#!/usr/bin/env bash
#
# @file verify_admin_keys.sh
# @description ADMIN_API_KEYS 生产写入验证——管理面/推理面密钥分离三连验证（P2-6 runbook 配套）
# @author YanYuCloudCube Team <admin@0379.email>
# @version v1.0.0
# @created 2026-09-23
# @status active
# @tags [ops],[rbac],[admin-keys]
#
# 用法（在能访问目标网关的机器上执行，默认公网入口）:
#   bash core/scripts/verify_admin_keys.sh <业务KEY> <管理面KEY> [BASE_URL]
#
#   示例:
#     bash core/scripts/verify_admin_keys.sh sk-biz-001 sk-admin-xxx https://api.0379.world
#
# 验证矩阵（三项全过 = 分离生效）:
#   ① 业务 Key  → /v1/admin/virtual-keys → 期望 403（管理面拒绝业务 Key）
#   ② 管理 Key  → /v1/admin/virtual-keys → 期望 200（管理面放行）
#   ③ 业务 Key  → /v1/models             → 期望 200（推理面不受影响）
#
# 退出码: 0=三项全过 / 1=存在失败项（含未配置回退态判定）

set -u

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

BIZ_KEY="${1:-}"
ADMIN_KEY="${2:-}"
BASE_URL="${3:-https://api.0379.world}"
ADMIN_PATH="/v1/admin/virtual-keys"

FAIL=0

echo "========================================"
echo "YYC³ ADMIN_API_KEYS 生产分离验证"
echo "========================================"
echo -e "目标: ${BLUE}${BASE_URL}${NC}"
echo ""

if [ -z "$BIZ_KEY" ] || [ -z "$ADMIN_KEY" ]; then
    echo -e "${RED}用法: $0 <业务KEY> <管理面KEY> [BASE_URL]${NC}"
    exit 1
fi

# 单项检查: name / key / path / 期望状态码 / 失败含义
check() {
    local name="$1" key="$2" path="$3" expect="$4" failmsg="$5"
    local code
    code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 \
        -H "X-API-Key: ${key}" "${BASE_URL}${path}" 2>/dev/null) || true
    code="${code:-000}"  # 连接失败（-w 无输出）兜底
    if [ "$code" = "$expect" ]; then
        echo -e "  ${GREEN}✓${NC} ${name}: ${code}（期望 ${expect}）"
    else
        echo -e "  ${RED}✗${NC} ${name}: ${code}（期望 ${expect}）— ${failmsg}"
        FAIL=1
    fi
}

echo "── ① 管理面拒绝业务 Key ──"
check "业务Key → ${ADMIN_PATH}" "$BIZ_KEY" "$ADMIN_PATH" "403" \
    "业务 Key 可进管理面：ADMIN_API_KEYS 未写入生产 .env（当前处于回退态，业务/管理同源）"

echo "── ② 管理面放行管理 Key ──"
check "管理Key → ${ADMIN_PATH}" "$ADMIN_KEY" "$ADMIN_PATH" "200" \
    "管理 Key 被拒：确认网关已滚动重启加载新 .env（部署桥 ~2 分钟周期）"

echo "── ③ 推理面不受影响 ──"
check "业务Key → /v1/models" "$BIZ_KEY" "/v1/models" "200" \
    "推理面异常：与密钥分离无关，查 /health 与上游池状态"

echo ""
if [ "$FAIL" = "0" ]; then
    echo -e "${GREEN}✅ 三连全过——管理面/推理面密钥分离已在生产生效${NC}"
    exit 0
else
    echo -e "${RED}❌ 存在失败项——按上方提示处置后重试${NC}"
    echo -e "${YELLOW}提示: ①失败=生产 .env 未写入 ADMIN_API_KEYS；②失败=网关未重启；③失败=查服务健康${NC}"
    exit 1
fi
