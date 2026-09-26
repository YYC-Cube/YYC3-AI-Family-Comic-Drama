#!/bin/bash

# 性能基线分析脚本
# 用于建立性能监控基准和趋势分析

PROMETHEUS_URL="${PROMETHEUS_URL:-http://localhost:9090}"
OUTPUT_DIR="${OUTPUT_DIR:-./performance-baselines}"
DURATION="${DURATION:-1h}"  # 数据采集时长

echo "性能基线分析工具"
echo "Prometheus URL: $PROMETHEUS_URL"
echo "输出目录: $OUTPUT_DIR"
echo "采集时长: $DURATION"
echo ""

# 创建输出目录
mkdir -p "$OUTPUT_DIR"

# 获取当前时间戳
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_FILE="$OUTPUT_DIR/performance_baseline_$TIMESTAMP.json"

echo "开始采集性能数据..."

# 采集 CPU 使用率
echo "采集 CPU 使用率..."
CPU_QUERY="100 - (avg by(instance) (irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)"
CPU_DATA=$(curl -s -G "$PROMETHEUS_URL/api/v1/query" \
    --data-urlencode "query=$CPU_QUERY" \
    --data-urlencode "time=$(date +%s)" | jq '.')

# 采集内存使用率
echo "采集内存使用率..."
MEMORY_QUERY="(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100"
MEMORY_DATA=$(curl -s -G "$PROMETHEUS_URL/api/v1/query" \
    --data-urlencode "query=$MEMORY_QUERY" \
    --data-urlencode "time=$(date +%s)" | jq '.')

# 采集磁盘使用率
echo "采集磁盘使用率..."
DISK_QUERY="(node_filesystem_size_bytes - node_filesystem_avail_bytes) / node_filesystem_size_bytes * 100"
DISK_DATA=$(curl -s -G "$PROMETHEUS_URL/api/v1/query" \
    --data-urlencode "query=$DISK_QUERY" \
    --data-urlencode "time=$(date +%s)" | jq '.')

# 采集网络流量
echo "采集网络流量..."
NETWORK_IN_QUERY="rate(node_network_receive_bytes_total[5m])"
NETWORK_OUT_QUERY="rate(node_network_transmit_bytes_total[5m])"
NETWORK_IN_DATA=$(curl -s -G "$PROMETHEUS_URL/api/v1/query" \
    --data-urlencode "query=$NETWORK_IN_QUERY" \
    --data-urlencode "time=$(date +%s)" | jq '.')
NETWORK_OUT_DATA=$(curl -s -G "$PROMETHEUS_URL/api/v1/query" \
    --data-urlencode "query=$NETWORK_OUT_QUERY" \
    --data-urlencode "time=$(date +%s)" | jq '.')

# 采集 API 请求速率
echo "采集 API 请求速率..."
API_REQUEST_QUERY="rate(http_requests_total[5m])"
API_REQUEST_DATA=$(curl -s -G "$PROMETHEUS_URL/api/v1/query" \
    --data-urlencode "query=$API_REQUEST_QUERY" \
    --data-urlencode "time=$(date +%s)" | jq '.')

# 采集 API 响应时间
echo "采集 API 响应时间..."
API_LATENCY_QUERY="histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))"
API_LATENCY_DATA=$(curl -s -G "$PROMETHEUS_URL/api/v1/query" \
    --data-urlencode "query=$API_LATENCY_QUERY" \
    --data-urlencode "time=$(date +%s)" | jq '.')

# 采集 API 错误率
echo "采集 API 错误率..."
API_ERROR_QUERY="rate(http_requests_total{status=~\"5..\"}[5m]) / rate(http_requests_total[5m]) * 100"
API_ERROR_DATA=$(curl -s -G "$PROMETHEUS_URL/api/v1/query" \
    --data-urlencode "query=$API_ERROR_QUERY" \
    --data-urlencode "time=$(date +%s)" | jq '.')

# 采集数据库连接数
echo "采集数据库连接数..."
DB_CONNECTION_QUERY="pg_stat_database_numbackends"
DB_CONNECTION_DATA=$(curl -s -G "$PROMETHEUS_URL/api/v1/query" \
    --data-urlencode "query=$DB_CONNECTION_QUERY" \
    --data-urlencode "time=$(date +%s)" | jq '.')

# 采集 Redis 缓存命中率
echo "采集 Redis 缓存命中率..."
REDIS_HIT_QUERY="redis_keyspace_hits / (redis_keyspace_hits + redis_keyspace_misses) * 100"
REDIS_HIT_DATA=$(curl -s -G "$PROMETHEUS_URL/api/v1/query" \
    --data-urlencode "query=$REDIS_HIT_QUERY" \
    --data-urlencode "time=$(date +%s)" | jq '.')

# 采集 Redis 内存使用
echo "采集 Redis 内存使用..."
REDIS_MEMORY_QUERY="redis_memory_used_bytes / 1024 / 1024"
REDIS_MEMORY_DATA=$(curl -s -G "$PROMETHEUS_URL/api/v1/query" \
    --data-urlencode "query=$REDIS_MEMORY_QUERY" \
    --data-urlencode "time=$(date +%s)" | jq '.')

# 生成性能基线报告
echo "生成性能基线报告..."
cat > "$OUTPUT_FILE" <<EOF
{
  "timestamp": "$TIMESTAMP",
  "collection_time": "$(date -Iseconds)",
  "duration": "$DURATION",
  "prometheus_url": "$PROMETHEUS_URL",
  "metrics": {
    "cpu": $CPU_DATA,
    "memory": $MEMORY_DATA,
    "disk": $DISK_DATA,
    "network": {
      "in": $NETWORK_IN_DATA,
      "out": $NETWORK_OUT_DATA
    },
    "api": {
      "request_rate": $API_REQUEST_DATA,
      "latency_p95": $API_LATENCY_DATA,
      "error_rate": $API_ERROR_DATA
    },
    "database": {
      "connections": $DB_CONNECTION_DATA
    },
    "redis": {
      "hit_rate": $REDIS_HIT_DATA,
      "memory_mb": $REDIS_MEMORY_DATA
    }
  }
}
EOF

echo "✓ 性能基线报告已生成: $OUTPUT_FILE"

# 提取性能指标值
CPU_VALUE=$(echo "$CPU_DATA" | jq -r '.data.result[0].value[1] // "N/A"')
MEMORY_VALUE=$(echo "$MEMORY_DATA" | jq -r '.data.result[0].value[1] // "N/A"')
DISK_VALUE=$(echo "$DISK_DATA" | jq -r '.data.result[0].value[1] // "N/A"')
NETWORK_IN_VALUE=$(echo "$NETWORK_IN_DATA" | jq -r '.data.result[0].value[1] // "N/A"')
NETWORK_OUT_VALUE=$(echo "$NETWORK_OUT_DATA" | jq -r '.data.result[0].value[1] // "N/A"')
API_REQUEST_VALUE=$(echo "$API_REQUEST_DATA" | jq -r '.data.result[0].value[1] // "N/A"')
API_LATENCY_VALUE=$(echo "$API_LATENCY_DATA" | jq -r '.data.result[0].value[1] // "N/A"')
API_ERROR_VALUE=$(echo "$API_ERROR_DATA" | jq -r '.data.result[0].value[1] // "N/A"')
DB_CONNECTION_VALUE=$(echo "$DB_CONNECTION_DATA" | jq -r '.data.result[0].value[1] // "N/A"')
REDIS_HIT_VALUE=$(echo "$REDIS_HIT_DATA" | jq -r '.data.result[0].value[1] // "N/A"')
REDIS_MEMORY_VALUE=$(echo "$REDIS_MEMORY_DATA" | jq -r '.data.result[0].value[1] // "N/A"')

# 生成可读的文本报告
TEXT_REPORT="$OUTPUT_DIR/performance_baseline_$TIMESTAMP.txt"
cat > "$TEXT_REPORT" <<EOF
YYC³ 性能基线报告
==================

采集时间: $(date -Iseconds)
采集时长: $DURATION
Prometheus URL: $PROMETHEUS_URL

系统资源
--------
CPU 使用率: ${CPU_VALUE}%
内存使用率: ${MEMORY_VALUE}%
磁盘使用率: ${DISK_VALUE}%

网络流量
--------
接收速率: ${NETWORK_IN_VALUE} bytes/s
发送速率: ${NETWORK_OUT_VALUE} bytes/s

API 性能
--------
请求速率: ${API_REQUEST_VALUE} requests/s
P95 延迟: ${API_LATENCY_VALUE} seconds
错误率: ${API_ERROR_VALUE}%

数据库
------
连接数: ${DB_CONNECTION_VALUE}%

Redis 缓存
---------
命中率: ${REDIS_HIT_VALUE}%
内存使用: ${REDIS_MEMORY_VALUE} MB

报告文件: $OUTPUT_FILE
EOF

echo "✓ 文本报告已生成: $TEXT_REPORT"

# 生成趋势分析（如果有历史数据）
echo "分析性能趋势..."
if ls "$OUTPUT_DIR"/performance_baseline_*.json 1> /dev/null 2>&1 | grep -q .; then
    # 获取最近的基线数据
    LATEST_BASELINE=$(ls -t "$OUTPUT_DIR"/performance_baseline_*.json | head -2 | tail -1)
    
    if [ -f "$LATEST_BASELINE" ] && [ "$LATEST_BASELINE" != "$OUTPUT_FILE" ]; then
        echo "对比历史基线: $LATEST_BASELINE"
        
        # 提取关键指标进行对比
        PREV_CPU=$(jq -r '.metrics.cpu.data.result[0].value[1]' "$LATEST_BASELINE")
        CURR_CPU=$(jq -r '.metrics.cpu.data.result[0].value[1]' "$OUTPUT_FILE")
        
        PREV_MEMORY=$(jq -r '.metrics.memory.data.result[0].value[1]' "$LATEST_BASELINE")
        CURR_MEMORY=$(jq -r '.metrics.memory.data.result[0].value[1]' "$OUTPUT_FILE")
        
        PREV_LATENCY=$(jq -r '.metrics.api.latency_p95.data.result[0].value[1]' "$LATEST_BASELINE")
        CURR_LATENCY=$(jq -r '.metrics.api.latency_p95.data.result[0].value[1]' "$OUTPUT_FILE")
        
        # 计算变化
        CPU_CHANGE=$(echo "scale=2; ($CURR_CPU - $PREV_CPU) / $PREV_CPU * 100" | bc)
        MEMORY_CHANGE=$(echo "scale=2; ($CURR_MEMORY - $PREV_MEMORY) / $PREV_MEMORY * 100" | bc)
        LATENCY_CHANGE=$(echo "scale=2; ($CURR_LATENCY - $PREV_LATENCY) / $PREV_LATENCY * 100" | bc)
        
        echo ""
        echo "性能趋势分析:"
        echo "CPU 变化: ${CPU_CHANGE}%"
        echo "内存变化: ${MEMORY_CHANGE}%"
        echo "延迟变化: ${LATENCY_CHANGE}%"
        
        # 生成趋势报告
        TREND_REPORT="$OUTPUT_DIR/performance_trend_$TIMESTAMP.txt"
        cat > "$TREND_REPORT" <<EOF
YYC³ 性能趋势分析
==================

当前时间: $(date -Iseconds)
对比时间: $(jq -r '.collection_time' "$LATEST_BASELINE")

指标对比
--------
CPU 使用率:
  之前: ${PREV_CPU}%
  当前: ${CURR_CPU}%
  变化: ${CPU_CHANGE}%

内存使用率:
  之前: ${PREV_MEMORY}%
  当前: ${CURR_MEMORY}%
  变化: ${MEMORY_CHANGE}%

API 延迟 (P95):
  之前: ${PREV_LATENCY}s
  当前: ${CURR_LATENCY}s
  变化: ${LATENCY_CHANGE}%

建议
-----
EOF
        
        # 添加建议
        if (( $(echo "$CPU_CHANGE > 10" | bc -l) )); then
            echo "- CPU 使用率显著增加，建议检查是否有异常进程" >> "$TREND_REPORT"
        fi
        
        if (( $(echo "$MEMORY_CHANGE > 10" | bc -l) )); then
            echo "- 内存使用率显著增加，建议检查内存泄漏" >> "$TREND_REPORT"
        fi
        
        if (( $(echo "$LATENCY_CHANGE > 20" | bc -l) )); then
            echo "- API 延迟显著增加，建议检查数据库和网络" >> "$TREND_REPORT"
        fi
        
        echo "✓ 趋势报告已生成: $TREND_REPORT"
    fi
fi

echo ""
echo "性能基线分析完成！"
echo ""
echo "生成的文件:"
echo "1. JSON 报告: $OUTPUT_FILE"
echo "2. 文本报告: $TEXT_REPORT"
if [ -f "$TREND_REPORT" ]; then
    echo "3. 趋势报告: $TREND_REPORT"
fi
echo ""
echo "查看报告:"
echo "cat $TEXT_REPORT"