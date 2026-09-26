#!/bin/bash

# YYC³ 快速健康检查脚本
# 快速检查各端关键服务状态

set -e

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "========================================"
echo "YYC³ 快速健康检查"
echo "========================================"
echo ""

# 检查 yyc3-22 (MacBook - 本机)
echo -e "${BLUE}[yyc3-22] MacBook Pro M4 Max${NC}"
echo "----------------------------------------"

echo -n "  PostgreSQL 15: "
if pg_isready -q -p 5433 2>/dev/null; then
    echo -e "${GREEN}✓ 运行中 (端口 5433)${NC}"
else
    echo -e "${RED}✗ 未运行${NC}"
fi

echo -n "  Redis: "
if redis-cli -a "$(grep '^requirepass' /opt/homebrew/etc/redis.conf 2>/dev/null | cut -d' ' -f2 | tr -d '"')" ping 2>/dev/null | grep -q "PONG"; then
    echo -e "${GREEN}✓ 运行中${NC}"
elif redis-cli ping 2>/dev/null | grep -q "PONG"; then
    echo -e "${GREEN}✓ 运行中${NC}"
else
    echo -e "${RED}✗ 未运行${NC}"
fi

echo -n "  yyc3_mcp: "
if pgrep -f yyc3_mcp &>/dev/null; then
    echo -e "${GREEN}✓ 运行中${NC}"
else
    echo -e "${YELLOW}⚠ 未运行或未安装${NC}"
fi

echo ""

# 检查 yyc3-33 (ECS) - 使用 Docker 容器
echo -e "${BLUE}[yyc3-33] 阿里云 ECS${NC}"
echo "----------------------------------------"

echo -n "  Traefik (反向代理): "
if ssh yyc3-33 "docker ps --format '{{.Names}}' | grep -q traefik" 2>/dev/null; then
    echo -e "${GREEN}✓ 运行中${NC}"
else
    echo -e "${RED}✗ 未运行${NC}"
fi

echo -n "  Docker: "
if ssh yyc3-33 "docker info &>/dev/null"; then
    echo -e "${GREEN}✓ 运行中${NC}"
else
    echo -e "${RED}✗ 未运行${NC}"
fi

echo -n "  frps: "
if ssh yyc3-33 "systemctl is-active frps 2>/dev/null" | grep -q "active"; then
    echo -e "${GREEN}✓ 运行中${NC}"
else
    echo -e "${YELLOW}⚠ 未运行或未安装${NC}"
fi

echo -n "  API (8000): "
if ssh yyc3-33 "curl -s http://localhost:8000/health 2>/dev/null" | grep -q "healthy"; then
    echo -e "${GREEN}✓ 运行中${NC}"
else
    echo -e "${RED}✗ 未运行${NC}"
fi

echo -n "  PostgreSQL (Docker): "
if ssh yyc3-33 "docker ps --format '{{.Names}}' | grep -q postgres" 2>/dev/null; then
    echo -e "${GREEN}✓ 运行中${NC}"
else
    echo -e "${RED}✗ 未运行${NC}"
fi

echo -n "  Prometheus: "
if ssh yyc3-33 "curl -s http://localhost:9090/-/healthy 2>/dev/null" | grep -q "Healthy"; then
    echo -e "${GREEN}✓ 运行中${NC}"
else
    echo -e "${RED}✗ 未运行${NC}"
fi

echo -n "  Grafana: "
if ssh yyc3-33 "curl -s http://localhost:3000/api/health 2>/dev/null" | grep -q "ok"; then
    echo -e "${GREEN}✓ 运行中${NC}"
else
    echo -e "${RED}✗ 未运行${NC}"
fi

echo ""

# 检查 yyc3-45 (NAS)
echo -e "${BLUE}[yyc3-45] NAS F4-423${NC}"
echo "----------------------------------------"

echo -n "  PostgreSQL 14: "
if ssh yyc3-45 "pg_isready -q" 2>/dev/null; then
    echo -e "${GREEN}✓ 运行中${NC}"
else
    echo -e "${RED}✗ 未运行${NC}"
fi

echo -n "  Docker: "
if ssh yyc3-45 "docker info &>/dev/null"; then
    echo -e "${GREEN}✓ 运行中${NC}"
else
    echo -e "${YELLOW}⚠ 未运行或未安装${NC}"
fi

echo -n "  frpc: "
if ssh yyc3-45 "systemctl is-active frpc 2>/dev/null" | grep -q "active"; then
    echo -e "${GREEN}✓ 运行中${NC}"
else
    echo -e "${YELLOW}⚠ 未运行或未安装${NC}"
fi

echo -n "  NFS: "
if ssh yyc3-45 "systemctl is-active nfs-server 2>/dev/null" | grep -q "active"; then
    echo -e "${GREEN}✓ 运行中${NC}"
else
    echo -e "${YELLOW}⚠ 未运行或未安装${NC}"
fi

echo ""

# 检查 yyc3-77 (iMac)
echo -e "${BLUE}[yyc3-77] iMac M4${NC}"
echo "----------------------------------------"

echo -n "  PostgreSQL 15: "
if ssh yyc3-77 "pg_isready -q" 2>/dev/null; then
    echo -e "${GREEN}✓ 运行中${NC}"
else
    echo -e "${YELLOW}⚠ 未运行（正常，备用节点）${NC}"
fi

echo -n "  Docker: "
if ssh yyc3-77 "docker info &>/dev/null"; then
    echo -e "${GREEN}✓ 运行中${NC}"
else
    echo -e "${YELLOW}⚠ 未运行${NC}"
fi

echo ""

# 检查网络连通性
echo -e "${BLUE}[网络连通性]${NC}"
echo "----------------------------------------"

echo -n "  api.0379.world: "
if curl -s --max-time 5 https://api.0379.world/health 2>/dev/null | grep -q "healthy"; then
    echo -e "${GREEN}✓ 可访问${NC}"
else
    echo -e "${RED}✗ 不可访问${NC}"
fi

echo -n "  grafana.0379.world: "
if curl -s --max-time 5 https://grafana.0379.world/api/health 2>/dev/null | grep -q "ok"; then
    echo -e "${GREEN}✓ 可访问${NC}"
else
    echo -e "${YELLOW}⚠ 不可访问或未配置${NC}"
fi

echo ""

# 总结
echo "========================================"
echo -e "${GREEN}✅ 健康检查完成${NC}"
echo "========================================"
