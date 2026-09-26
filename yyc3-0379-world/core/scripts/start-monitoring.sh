#!/bin/bash

# 启动监控服务脚本
# 用于启动 Prometheus 和 Grafana

set -e

PROJECT_ROOT="/Volumes/Development/项目提示词/0379-world"
cd "$PROJECT_ROOT"

echo "YYC³ 监控服务启动"
echo "===================="

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker 未运行，请先启动 Docker"
    echo ""
    echo "启动方法："
    echo "  1. 打开 Docker Desktop 应用"
    echo "  2. 等待 Docker 完全启动"
    echo "  3. 重新运行此脚本"
    exit 1
fi

echo "✓ Docker 正在运行"

# 检查 docker-compose 是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装"
    exit 1
fi

echo "✓ Docker Compose 已安装"

# 创建必要的网络
echo "创建网络..."
docker network create 0379-world_backend 2>/dev/null || true
docker network create docker_backend 2>/dev/null || true

# 检查是否已有监控服务运行
echo "检查监控服务状态..."
PROMETHEUS_RUNNING=$(docker ps --filter "name=prometheus" --filter "status=running" -q)
GRAFANA_RUNNING=$(docker ps --filter "name=grafana" --filter "status=running" -q)

if [ -n "$PROMETHEUS_RUNNING" ] && [ -n "$GRAFANA_RUNNING" ]; then
    echo "✓ Prometheus 和 Grafana 已在运行"
    echo ""
    echo "服务地址："
    echo "  - Prometheus: http://localhost:9090"
    echo "  - Grafana: http://localhost:3000"
    echo ""
    echo "如需重启服务，请运行："
    echo "  cd docker && docker-compose -f docker-compose.stable.yml restart prometheus grafana"
    exit 0
fi

# 启动监控服务
echo "启动监控服务..."
cd docker

# 使用 docker-compose.stable.yml 启动 Prometheus 和 Grafana
docker-compose -f docker-compose.stable.yml up -d prometheus grafana

# 等待服务启动
echo "等待服务启动..."
sleep 5

# 检查服务状态
echo "检查服务状态..."
docker-compose -f docker-compose.stable.yml ps prometheus grafana

# 验证服务是否正常
echo "验证服务..."

# 检查 Prometheus
if curl -s http://localhost:9090/-/healthy > /dev/null; then
    echo "✓ Prometheus 启动成功"
else
    echo "⚠ Prometheus 可能还在启动中，请稍后访问"
fi

# 检查 Grafana
if curl -s http://localhost:3000/api/health > /dev/null; then
    echo "✓ Grafana 启动成功"
else
    echo "⚠ Grafana 可能还在启动中，请稍后访问"
fi

echo ""
echo "===================="
echo "✅ 监控服务启动完成"
echo "===================="
echo ""
echo "服务地址："
echo "  - Prometheus: http://localhost:9090"
echo "  - Grafana: http://localhost:3000"
echo ""
echo "Grafana 默认登录："
echo "  - 用户名: ${GRAFANA_ADMIN_USER:-admin}"
echo "  - 密码: ${GRAFANA_ADMIN_PASSWORD:-admin}"
echo ""
echo "下一步："
echo "  1. 访问 Grafana: open http://localhost:3000"
echo "  2. 配置仪表盘: ./scripts/setup-grafana-dashboards.sh"
echo "  3. 查看监控数据"
