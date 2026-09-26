#!/bin/bash

# 环境变量验证脚本

ENV_FILE=".env/.env.local"
REQUIRED_VARS=(
  "APP_NAME"
  "POSTGRES_HOST"
  "POSTGRES_USER"
  "POSTGRES_PASSWORD"
  "REDIS_HOST"
  "SECRET_KEY"
)

echo "验证环境变量配置..."

if [ ! -f "$ENV_FILE" ]; then
  echo "错误: 环境变量文件不存在: $ENV_FILE"
  echo "请复制 .env.example 到 .env.local 并填写实际值"
  exit 1
fi

# 加载环境变量
source "$ENV_FILE"

# 检查必需变量
missing_vars=()
for var in "${REQUIRED_VARS[@]}"; do
  if [ -z "${!var}" ]; then
    missing_vars+=("$var")
  fi
done

if [ ${#missing_vars[@]} -gt 0 ]; then
  echo "错误: 以下必需的环境变量未设置:"
  printf '  - %s\n' "${missing_vars[@]}"
  exit 1
fi

echo "✓ 所有必需的环境变量已设置"
echo "✓ 环境变量验证通过"