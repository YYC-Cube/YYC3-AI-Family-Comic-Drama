#!/bin/bash

# YYC³ 模型配置查看脚本
# 快速查看当前启用的模型配置

set -e

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo "========================================"
echo "YYC³ 模型配置查看"
echo "========================================"
echo ""

# 数据库连接信息
DB_HOST="localhost"
DB_PORT="5433"
DB_USER="yyc3_dev"
DB_NAME="yyc3_mcp"

echo -e "${BLUE}[已启用的模型]${NC}"
echo "----------------------------------------"

# 查询已启用的模型
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
SELECT
    name as \"模型名称\",
    provider as \"提供商\",
    model as \"可用模型\"
FROM api_configs
WHERE enabled = true AND api_type = 'chat'
ORDER BY name;
"

echo ""
echo -e "${BLUE}[已禁用的模型]${NC}"
echo "----------------------------------------"

# 查询已禁用的模型
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
SELECT
    name as \"模型名称\",
    provider as \"提供商\",
    model as \"可用模型\"
FROM api_configs
WHERE enabled = false AND api_type = 'chat'
ORDER BY name;
"

echo ""
echo "========================================"
echo -e "${GREEN}✅ 查询完成${NC}"
echo "========================================"
echo ""
echo "💡 提示:"
echo "  - 启用模型: psql -h localhost -p 5433 -U yyc3_dev -d yyc3_mcp -c \"UPDATE api_configs SET enabled = true WHERE name = '模型名称';\""
echo "  - 禁用模型: psql -h localhost -p 5433 -U yyc3_dev -d yyc3_mcp -c \"UPDATE api_configs SET enabled = false WHERE name = '模型名称';\""
echo ""
