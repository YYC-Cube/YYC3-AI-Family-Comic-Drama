#!/usr/bin/env bash
#
# @file rotate_admin_key.sh
# @description ADMIN_API_KEYS 90 天轮换 runbook 脚本——双写两阶段零中断轮换
# @author YanYuCloudCube Team <admin@0379.email>
# @version v1.0.0
# @created 2026-09-24
# @status active
# @tags [ops],[rbac],[rotation],[admin-keys]
#
# 两阶段语义（对应 docs/操作指南/API认证使用指南.md「轮换（90 天）」）:
#   stage1  双写: 生成新 Key → ADMIN_API_KEYS=旧,新 → 重启网关 → 验证双 Key 均 200
#           ↓（此间切换看板/客户端到新 Key，旧 Key 仍有效——零中断窗口）
#   stage2  收敛: 预检新 Key 可用 → 只留新 Key → 重启网关 → 验证旧 403 / 新 200
#           （预检不过 = 使用方未切换完，不动 .env 直接退出）
#
# 用法（在 NAS yyc3-45 上执行）:
#   bash core/scripts/rotate_admin_key.sh stage1
#   bash core/scripts/rotate_admin_key.sh stage2
#   bash core/scripts/rotate_admin_key.sh status     # 脱敏查看当前态
#   bash core/scripts/rotate_admin_key.sh rollback   # 恢复最近一次轮换备份
#
# 选项:
#   --env-file PATH   生产 .env 路径（默认 /Volume2/yyc3-33/.env）
#   --base-url URL    网关地址（默认 http://localhost:8000，NAS 本机回环）
#
# 安全: 每次变更前自动备份 .env.bak-rotate-<时间戳>（cp -p 保权限）；
#       新 Key 仅 stage1 终端展示一次；status 全程脱敏不泄 Key。

set -u

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

CMD="${1:-}"
[ $# -gt 0 ] && shift

ENV_FILE="/Volume2/yyc3-33/.env"
BASE_URL="http://localhost:8000"
CONTAINER="0379-world-gateway-1"
ADMIN_PATH="/v1/admin/virtual-keys"

while [ $# -gt 0 ]; do
    case "$1" in
        --env-file) ENV_FILE="${2:-}"; shift 2 ;;
        --base-url) BASE_URL="${2:-}"; shift 2 ;;
        *) echo -e "${RED}未知参数: $1${NC}" >&2; exit 1 ;;
    esac
done

ENV_DIR=$(dirname "$ENV_FILE")

usage() {
    echo "用法: $0 <stage1|stage2|status|rollback> [--env-file PATH] [--base-url URL]"
}

error() { echo -e "${RED}✗ $1${NC}" >&2; exit 1; }

mask() {  # 脱敏指纹: 前 12 位 + … + 后 4 位
    local k="$1"
    if [ "${#k}" -le 16 ]; then echo "sk-admin-****"
    else echo "${k:0:12}…${k: -4}"; fi
}

get_keys() {  # 读 ADMIN_API_KEYS 值（单 Key 或 旧,新 双 Key）
    grep '^ADMIN_API_KEYS=' "$ENV_FILE" 2>/dev/null | head -1 | cut -d= -f2- | tr -d ' "'
}

write_keys() {  # 可移植写回（grep 剔旧行 + 追加新行，绕开 macOS/Linux sed -i 方言差；cat 写入保 inode 权限）
    local val="$1" tmp
    tmp=$(mktemp)
    grep -v '^ADMIN_API_KEYS=' "$ENV_FILE" > "$tmp" || true
    printf 'ADMIN_API_KEYS=%s\n' "$val" >> "$tmp"
    cat "$tmp" > "$ENV_FILE" && rm -f "$tmp"
}

gen_key() {
    if command -v openssl >/dev/null 2>&1; then
        echo "sk-admin-$(openssl rand -hex 16)"
    else
        python3 -c "import secrets; print(f'sk-admin-{secrets.token_hex(16)}')"
    fi
}

backup_env() {
    local bak=".env.bak-rotate-$(date +%Y%m%d-%H%M%S)"
    cp -p "$ENV_FILE" "${ENV_DIR}/${bak}" || error "备份失败: ${bak}"
    echo -e "  ${BLUE}·${NC} 已备份: ${ENV_DIR}/${bak}"
}

restart_and_wait() {
    echo -e "  ${BLUE}·${NC} 重启网关（${CONTAINER}）…"
    if command -v docker >/dev/null 2>&1 && docker restart "$CONTAINER" >/dev/null 2>&1; then
        :
    elif bash -lc "docker restart $CONTAINER" >/dev/null 2>&1; then
        :  # NAS 非交互 shell docker 不在 PATH，走 login shell
    else
        error "重启失败——手动执行: bash -lc 'docker restart ${CONTAINER}'，健康后重试本阶段验证"
    fi
    local i code
    for i in $(seq 1 30); do
        code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 "${BASE_URL}/healthz" 2>/dev/null) || true
        [ "${code:-000}" = "200" ] && return 0
        sleep 2
    done
    error "healthz 60s 未恢复——查容器日志: bash -lc 'docker logs --tail 50 ${CONTAINER}'"
}

http_code() {  # key / path → 状态码（连接失败兜底 000）
    local c
    c=$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 \
        -H "X-API-Key: $1" "${BASE_URL}$2" 2>/dev/null) || true
    echo "${c:-000}"
}

report() {  # label / code / expect / failmsg
    if [ "$2" = "$3" ]; then
        echo -e "  ${GREEN}✓${NC} $1: $2（期望 $3）"
    else
        echo -e "  ${RED}✗${NC} $1: $2（期望 $3）— $4"
        FAIL=1
    fi
}

cmd_stage1() {
    local cur new code
    cur=$(get_keys)
    [ -n "$cur" ] || error "生产 .env 未配置 ADMIN_API_KEYS（回退态）——先按「管理面密钥分离」runbook 完成初次写入"
    case "$cur" in
        *,*) error "已处于双写轮换中（旧,新 并存）——先完成 stage2 或 rollback" ;;
    esac
    new=$(gen_key)
    echo "── stage1 双写（旧,新 并存，零中断窗口开启）──"
    backup_env
    write_keys "${cur},${new}"
    restart_and_wait
    FAIL=0
    report "旧Key → ${ADMIN_PATH}" "$(http_code "$cur" "$ADMIN_PATH")" "200" "旧 Key 失效异常——立即 rollback"
    report "新Key → ${ADMIN_PATH}" "$(http_code "$new" "$ADMIN_PATH")" "200" "新 Key 未生效——确认重启成功后重试，或 rollback"
    echo ""
    if [ "$FAIL" = "1" ]; then
        echo -e "${RED}❌ 双写验证未全过——建议 rollback 后重试${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ 双写生效${NC}——新 Key（${YELLOW}仅此一次展示，立即分发${NC}）:"
    echo ""
    echo -e "    ${new}"
    echo ""
    echo -e "下一步: 切换看板/客户端到新 Key → 确认使用方全部切换 → 执行 ${BLUE}$0 stage2${NC} 收敛"
}

cmd_stage2() {
    local cur old new code
    cur=$(get_keys)
    case "$cur" in
        *,*) : ;;
        "")  error "生产 .env 未配置 ADMIN_API_KEYS（回退态）" ;;
        *)   error "当前为单 Key 稳态（无轮换中状态）——从 stage1 开始" ;;
    esac
    old="${cur%%,*}"
    new="${cur##*,}"
    echo "── stage2 收敛（移除旧 Key，只留新 Key）──"
    # 预检: 新 Key 必须已可用（使用方已切换），预检不过不动 .env
    code=$(http_code "$new" "$ADMIN_PATH")
    [ "$code" = "200" ] || error "新 Key 预检失败（${code}）——使用方尚未切换完成，未做任何修改；切换后再执行 stage2"
    backup_env
    write_keys "$new"
    restart_and_wait
    FAIL=0
    report "新Key → ${ADMIN_PATH}" "$(http_code "$new" "$ADMIN_PATH")" "200" "新 Key 失效异常——立即 rollback"
    report "旧Key → ${ADMIN_PATH}" "$(http_code "$old" "$ADMIN_PATH")" "403" "旧 Key 仍有效——确认 .env 已收敛、网关已重启"
    echo ""
    if [ "$FAIL" = "1" ]; then
        echo -e "${RED}❌ 收敛验证未全过——建议 rollback 后排查${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ 轮换完成${NC}——旧 Key $(mask "$old") 已失效；90 天后再次轮换（$0 stage1）"
}

cmd_status() {
    local cur
    cur=$(get_keys)
    if [ -z "$cur" ]; then
        echo -e "当前态: ${YELLOW}回退态${NC}（未配置 ADMIN_API_KEYS，业务/管理同源）"
    elif case "$cur" in *,*) true ;; *) false ;; esac; then
        echo -e "当前态: ${YELLOW}双写轮换中${NC}  旧 $(mask "${cur%%,*}")  新 $(mask "${cur##*,}")"
        echo -e "下一步: 使用方切换完成后执行 ${BLUE}$0 stage2${NC}"
    else
        echo -e "当前态: ${GREEN}稳态${NC}（单 Key $(mask "$cur")）"
    fi
}

cmd_rollback() {
    local latest cur
    latest=$(ls -t "${ENV_DIR}"/.env.bak-rotate-* 2>/dev/null | head -1)
    [ -n "$latest" ] || error "无 .env.bak-rotate-* 备份可回滚"
    echo "── rollback（恢复最近备份）──"
    echo -e "  ${BLUE}·${NC} 恢复自: ${latest}"
    cp -p "$latest" "$ENV_FILE" || error "恢复失败"
    restart_and_wait
    cur=$(get_keys)
    echo -e "${GREEN}✅ 已回滚${NC}（当前 ADMIN_API_KEYS: $(mask "$cur")）"
    echo -e "${YELLOW}注意: 回滚后请核对该备份时点的 Key 与使用方持有 Key 一致${NC}"
}

case "$CMD" in
    stage1)   [ -f "$ENV_FILE" ] || error "env 文件不存在: $ENV_FILE"; cmd_stage1 ;;
    stage2)   [ -f "$ENV_FILE" ] || error "env 文件不存在: $ENV_FILE"; cmd_stage2 ;;
    status)   [ -f "$ENV_FILE" ] || error "env 文件不存在: $ENV_FILE"; cmd_status ;;
    rollback) cmd_rollback ;;
    *) usage; exit 1 ;;
esac
