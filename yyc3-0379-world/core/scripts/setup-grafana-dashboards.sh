#!/bin/bash

# Grafana 仪表盘配置脚本

GRAFANA_URL="http://localhost:3000"
GRAFANA_USER="admin"
GRAFANA_PASSWORD="admin"
DATASOURCE_NAME="Prometheus"
DATASOURCE_URL="http://prometheus:9090"

echo "配置 Grafana 仪表盘..."

# 检查 Grafana 是否运行
if ! curl -s -f "$GRAFANA_URL/api/health" > /dev/null 2>&1; then
    echo "错误: Grafana 未运行，请先启动 Grafana 服务"
    exit 1
fi

# 获取认证 Token
echo "获取 Grafana 认证 Token..."
TOKEN=$(curl -s -X POST "$GRAFANA_URL/api/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"user\":\"$GRAFANA_USER\",\"password\":\"$GRAFANA_PASSWORD\"}" | \
    jq -r '.accessToken')

if [ -z "$TOKEN" ]; then
    echo "错误: 无法获取认证 Token"
    exit 1
fi

echo "✓ 认证成功"

# 配置 Prometheus 数据源
echo "配置 Prometheus 数据源..."
DATASOURCE_CONFIG=$(cat <<EOF
{
  "name": "$DATASOURCE_NAME",
  "type": "prometheus",
  "url": "$DATASOURCE_URL",
  "access": "proxy",
  "isDefault": true
}
EOF
)

curl -s -X POST "$GRAFANA_URL/api/datasources" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$DATASOURCE_CONFIG" > /dev/null

echo "✓ Prometheus 数据源配置完成"

# 创建服务概览仪表盘
echo "创建服务概览仪表盘..."
SERVICE_DASHBOARD=$(cat <<'EOF'
{
  "dashboard": {
    "title": "服务概览",
    "uid": "service-overview",
    "tags": ["yyc3", "services"],
    "timezone": "browser",
    "schemaVersion": 27,
    "version": 1,
    "refresh": "30s",
    "panels": [
      {
        "id": 1,
        "title": "服务状态",
        "type": "stat",
        "targets": [
          {
            "expr": "up",
            "legendFormat": "{{job}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "thresholds"
            },
            "thresholds": {
              "steps": [
                {"color": "red", "value": 0},
                {"color": "green", "value": 1}
              ]
            }
          }
        }
      },
      {
        "id": 2,
        "title": "CPU 使用率",
        "type": "graph",
        "targets": [
          {
            "expr": "100 - (avg by(instance) (irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
            "legendFormat": "{{instance}}"
          }
        ]
      },
      {
        "id": 3,
        "title": "内存使用率",
        "type": "graph",
        "targets": [
          {
            "expr": "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100",
            "legendFormat": "{{instance}}"
          }
        ]
      },
      {
        "id": 4,
        "title": "API 请求速率",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{path}}"
          }
        ]
      },
      {
        "id": 5,
        "title": "API 错误率",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m]) / rate(http_requests_total[5m]) * 100",
            "legendFormat": "{{instance}}"
          }
        ]
      },
      {
        "id": 6,
        "title": "API 响应时间 (P95)",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "{{instance}}"
          }
        ]
      }
    ]
  },
  "overwrite": true
}
EOF
)

curl -s -X POST "$GRAFANA_URL/api/dashboards/db" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$SERVICE_DASHBOARD" > /dev/null

echo "✓ 服务概览仪表盘创建完成"

# 创建数据库仪表盘
echo "创建数据库仪表盘..."
DATABASE_DASHBOARD=$(cat <<'EOF'
{
  "dashboard": {
    "title": "数据库监控",
    "uid": "database-monitoring",
    "tags": ["yyc3", "database"],
    "timezone": "browser",
    "schemaVersion": 27,
    "version": 1,
    "refresh": "30s",
    "panels": [
      {
        "id": 1,
        "title": "PostgreSQL 连接数",
        "type": "graph",
        "targets": [
          {
            "expr": "pg_stat_database_numbackends",
            "legendFormat": "{{datname}}"
          }
        ]
      },
      {
        "id": 2,
        "title": "PostgreSQL 事务速率",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(pg_stat_database_xact_commit[5m])",
            "legendFormat": "提交"
          },
          {
            "expr": "rate(pg_stat_database_xact_rollback[5m])",
            "legendFormat": "回滚"
          }
        ]
      },
      {
        "id": 3,
        "title": "PostgreSQL 缓存命中率",
        "type": "graph",
        "targets": [
          {
            "expr": "pg_stat_database_blks_hit / (pg_stat_database_blks_hit + pg_stat_database_blks_read) * 100",
            "legendFormat": "{{datname}}"
          }
        ]
      },
      {
        "id": 4,
        "title": "Redis 内存使用",
        "type": "graph",
        "targets": [
          {
            "expr": "redis_memory_used_bytes / 1024 / 1024",
            "legendFormat": "{{instance}}"
          }
        ]
      },
      {
        "id": 5,
        "title": "Redis 命令速率",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(redis_commands_processed_total[5m])",
            "legendFormat": "{{instance}}"
          }
        ]
      },
      {
        "id": 6,
        "title": "Redis 键数量",
        "type": "graph",
        "targets": [
          {
            "expr": "redis_db_keys",
            "legendFormat": "{{instance}} - DB{{db}}"
          }
        ]
      }
    ]
  },
  "overwrite": true
}
EOF
)

curl -s -X POST "$GRAFANA_URL/api/dashboards/db" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$DATABASE_DASHBOARD" > /dev/null

echo "✓ 数据库仪表盘创建完成"

# 创建告警仪表盘
echo "创建告警仪表盘..."
ALERT_DASHBOARD=$(cat <<'EOF'
{
  "dashboard": {
    "title": "告警监控",
    "uid": "alert-monitoring",
    "tags": ["yyc3", "alerts"],
    "timezone": "browser",
    "schemaVersion": 27,
    "version": 1,
    "refresh": "30s",
    "panels": [
      {
        "id": 1,
        "title": "活跃告警",
        "type": "stat",
        "targets": [
          {
            "expr": "ALERTS{alertstate=\"firing\"}",
            "legendFormat": "{{alertname}}"
          }
        ]
      },
      {
        "id": 2,
        "title": "告警历史",
        "type": "table",
        "targets": [
          {
            "expr": "ALERTS",
            "format": "table",
            "instant": true
          }
        ]
      }
    ]
  },
  "overwrite": true
}
EOF
)

curl -s -X POST "$GRAFANA_URL/api/dashboards/db" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$ALERT_DASHBOARD" > /dev/null

echo "✓ 告警仪表盘创建完成"

# 创建 A2A 可观测仪表盘（TOP3：DLQ 深度 / 结果流堆积 / 挂起回收量）
echo "创建 A2A 可观测仪表盘..."
A2A_DASHBOARD=$(cat <<'EOF'
{
  "dashboard": {
    "title": "A2A 可观测",
    "uid": "a2a-observability",
    "tags": ["yyc3", "a2a", "observability"],
    "timezone": "browser",
    "schemaVersion": 27,
    "version": 1,
    "refresh": "30s",
    "panels": [
      {
        "id": 1,
        "title": "DLQ 死信深度（按 Agent）",
        "type": "timeseries",
        "targets": [
          {
            "expr": "a2a_dlq_depth{agent_id=~\".+\"}",
            "legendFormat": "{{agent_id}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "none",
            "min": 0,
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"color": "green", "value": null},
                {"color": "red", "value": 1}
              ]
            }
          }
        }
      },
      {
        "id": 2,
        "title": "结果流堆积长度",
        "type": "stat",
        "targets": [
          {
            "expr": "a2a_result_stream_len",
            "legendFormat": "结果流长度"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "none",
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"color": "green", "value": null},
                {"color": "orange", "value": 500},
                {"color": "red", "value": 2000}
              ]
            }
          }
        }
      },
      {
        "id": 3,
        "title": "各 Agent 任务流 PEL 挂起",
        "type": "timeseries",
        "targets": [
          {
            "expr": "a2a_task_stream_pending{agent_id=~\".+\"}",
            "legendFormat": "{{agent_id}}"
          }
        ]
      },
      {
        "id": 4,
        "title": "结果流 PEL 挂起",
        "type": "timeseries",
        "targets": [
          {
            "expr": "a2a_result_stream_pending",
            "legendFormat": "结果流 PEL"
          }
        ]
      },
      {
        "id": 5,
        "title": "死信入队速率",
        "type": "timeseries",
        "targets": [
          {
            "expr": "rate(a2a_dlq_enqueued_total[5m])",
            "legendFormat": "DLQ 入队 /s"
          }
        ]
      },
      {
        "id": 6,
        "title": "挂起回收速率",
        "type": "timeseries",
        "targets": [
          {
            "expr": "rate(a2a_result_reclaimed_total[5m])",
            "legendFormat": "回收 /s"
          }
        ]
      },
      {
        "id": 7,
        "title": "孤儿回执速率",
        "type": "timeseries",
        "targets": [
          {
            "expr": "rate(a2a_result_orphan_total[5m])",
            "legendFormat": "孤儿 /s"
          }
        ]
      }
    ]
  },
  "overwrite": true
}
EOF
)

curl -s -X POST "$GRAFANA_URL/api/dashboards/db" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$A2A_DASHBOARD" > /dev/null

echo "✓ A2A 可观测仪表盘创建完成"

echo ""
echo "Grafana 仪表盘配置完成！"
echo "访问地址: $GRAFANA_URL"
echo "用户名: $GRAFANA_USER"
echo "密码: $GRAFANA_PASSWORD"
echo ""
echo "已创建的仪表盘："
echo "1. 服务概览 (uid: service-overview)"
echo "2. 数据库监控 (uid: database-monitoring)"
echo "3. 告警监控 (uid: alert-monitoring)"
echo "4. A2A 可观测 (uid: a2a-observability)"