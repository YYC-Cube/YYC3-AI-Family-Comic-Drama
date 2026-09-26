#!/bin/bash
set -euo pipefail

BACKUP_DIR="/Volume2/yyc3_sd/数据库服务/自动备份"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7
LOG_FILE="${BACKUP_DIR}/backup.log"
DOCKER="/Volume2/@apps/DockerEngine/dockerd/bin/docker"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

cleanup_old_backups() {
    log "🧹 清理 ${RETENTION_DAYS} 天前的备份..."
    find "${BACKUP_DIR}" -name "*.sql.gz" -mtime +${RETENTION_DAYS} -delete 2>/dev/null || true
    log "✅ 清理完成"
}

backup_nas_pg14_docker() {
    local DBS=("yyc3_mcp" "yyc3_core" "yyc3_gpt" "yyc3_ai" "yyc3_audit")
    
    for DB_NAME in "${DBS[@]}"; do
        local FILE="${BACKUP_DIR}/nas_pg14_${DB_NAME}_${TIMESTAMP}.sql.gz"
        
        log "📦 备份 NAS PG14: ${DB_NAME}"
        
        local TABLE_CHECK=$(${DOCKER} run --rm --network host postgres:14-alpine \
            psql -h 127.0.0.1 -p 5432 -U postgres -d "${DB_NAME}" -tAc \
            "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'" 2>/dev/null | tr -d '[:space:]')
        
        if [ "${TABLE_CHECK}" = "0" ] || [ -z "${TABLE_CHECK}" ]; then
            log "⏭️ 跳过空库: ${DB_NAME}"
            continue
        fi
        
        if ${DOCKER} run --rm --network host -v "${BACKUP_DIR}:/backup" \
            postgres:14-alpine pg_dump \
            -h 127.0.0.1 -p 5432 -U postgres \
            -d "${DB_NAME}" --no-owner --no-privileges \
            2>/dev/null | gzip > "${FILE}"; then
            
            local SIZE=$(du -h "${FILE}" | cut -f1)
            log "✅ 备份成功: ${DB_NAME} (${SIZE})"
        else
            log "⚠️ 备份跳过: ${DB_NAME}"
            rm -f "${FILE}"
        fi
    done
}

backup_ecs_pg() {
    local DB_HOST="47.97.236.224"
    local DB_PORT="5432"
    local DB_USER="yyc3_33"
    local DB_PASS="yyc3_33"
    local DB_NAME="yyc3_mcp"
    local FILE="${BACKUP_DIR}/ecs_pg_${DB_NAME}_${TIMESTAMP}.sql.gz"
    
    log "📦 备份 ECS PG: ${DB_HOST}:${DB_PORT}/${DB_NAME}"
    
    if ${DOCKER} run --rm -v "${BACKUP_DIR}:/backup" postgres:14-alpine \
        pg_dump -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" \
        -d "${DB_NAME}" --no-owner --no-privileges \
        2>/dev/null | gzip > "${FILE}"; then
        
        local SIZE=$(du -h "${FILE}" | cut -f1)
        log "✅ ECS PG 备份成功 (${SIZE})"
    else
        log "⚠️ ECS PG 备份失败 (网络不可达或认证失败)"
        rm -f "${FILE}"
    fi
}

backup_redis_rdb() {
    local FILE="${BACKUP_DIR}/redis_slave_rdb_${TIMESTAMP}.rdb"
    
    log "📦 备份 Redis RDB"
    
    local REDIS_DATA_DIR=$(${DOCKER} inspect yyc3-redis-slave 2>/dev/null | \
        grep -A10 '"Mounts"' | grep '"Source"' | head -1 | sed 's/.*"Source": "//;s/".*//')
    
    if [ -n "${REDIS_DATA_DIR}" ]; then
        local RDB_FILE=$(ls -t "${REDIS_DATA_DIR}"/dump*.rdb 2>/dev/null | head -1)
        if [ -n "${RDB_FILE}" ] && [ -f "${RDB_FILE}" ]; then
            cp "${RDB_FILE}" "${FILE}"
            local SIZE=$(du -h "${FILE}" | cut -f1)
            log "✅ Redis RDB 备份成功 (${SIZE})"
        else
            log "⚠️ Redis RDB 未找到，尝试 BGSAVE..."
            ${DOCKER} exec yyc3-redis-slave redis-cli BGSAVE 2>/dev/null || true
            sleep 3
            RDB_FILE=$(ls -t "${REDIS_DATA_DIR}"/dump*.rdb 2>/dev/null | head -1)
            if [ -n "${RDB_FILE}" ]; then
                cp "${RDB_FILE}" "${FILE}"
                log "✅ Redis RDB BGSAVE 后备份成功"
            else
                log "⚠️ Redis RDB 仍不可用，跳过"
            fi
        fi
    else
        log "⚠️ Redis 容器数据目录未找到，跳过"
    fi
}

main() {
    log "═══════════════════════════════════════"
    log "🔄 YYC³ 数据库自动备份开始"
    log "═══════════════════════════════════════"
    
    cleanup_old_backups
    
    backup_nas_pg14_docker || true
    backup_ecs_pg || true
    backup_redis_rdb || true
    
    local TOTAL_SIZE=$(du -sh "${BACKUP_DIR}"/*.gz 2>/dev/null | tail -1 | awk '{print $1}')
    log "═══════════════════════════════════════"
    log "🎉 备份完成! 总大小: ${TOTAL_SIZE:-N/A}"
    log "═══════════════════════════════════════"
}

main "$@"
