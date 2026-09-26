# YYC³ 0379-world Makefile
# 项目构建和管理自动化脚本

.PHONY: help install dev clean test lint format run docker-up docker-down docker-logs

# 默认目标
.DEFAULT_GOAL := help

# 变量定义
PYTHON := python3
PIP := pip3
PROJECT_NAME := yyc3-api-world
PROJECT_VERSION := 1.0.0

# Docker 相关
DOCKER_COMPOSE := docker-compose
DOCKER_FILE := core/database/docker/docker-compose.yml

# 颜色输出
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
RESET := \033[0m

# 帮助信息
help: ## 显示帮助信息
	@echo "$(BLUE)YYC³ 0379-world 项目管理工具$(RESET)"
	@echo ""
	@echo "$(GREEN)使用方法:$(RESET)"
	@echo "  make [目标]"
	@echo ""
	@echo "$(GREEN)可用目标:$(RESET)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(BLUE)%-15s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""

# 安装依赖
install: ## 安装项目依赖
	@echo "$(GREEN)安装项目依赖...$(RESET)"
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)✅ 依赖安装完成$(RESET)"

# 安装开发依赖
dev: ## 安装开发依赖
	@echo "$(GREEN)安装开发依赖...$(RESET)"
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-dev.txt 2>/dev/null || $(PIP) install pytest pytest-cov black flake8 mypy
	@echo "$(GREEN)✅ 开发依赖安装完成$(RESET)"

# 清理临时文件
clean: ## 清理临时文件
	@echo "$(YELLOW)清理临时文件...$(RESET)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✅ 清理完成$(RESET)"

# 运行测试
test: ## 运行测试（全量：快速层 + integration 集成层）
	@echo "$(GREEN)运行测试（全量）...$(RESET)"
	$(PYTHON) -m pytest tests/ -v -m "" --cov=core --cov-report=html --cov-report=term
	@echo "$(GREEN)✅ 测试完成$(RESET)"

test-fast: ## 快速回归层（~0.3s，单元 + 纯 mock；开发迭代用）
	@echo "$(GREEN)运行快速回归层...$(RESET)"
	$(PYTHON) -m pytest tests/ -m "not integration" --cov=core --cov-report=term
	@echo "$(GREEN)✅ 快速层完成$(RESET)"

test-integration: ## 集成层（TestClient 全链路，~7-8 分钟；发布前用）
	@echo "$(GREEN)运行集成层...$(RESET)"
	$(PYTHON) -m pytest tests/ -m integration --cov=core --cov-report=term --cov-append
	@echo "$(GREEN)✅ 集成层完成$(RESET)"

# 代码检查
lint: ## 代码检查
	@echo "$(GREEN)运行代码检查...$(RESET)"
	$(PYTHON) -m flake8 core/ --max-line-length=100 --exclude=__pycache__,migrations --ignore=E402,W503,E203
	@echo "$(GREEN)✅ 代码检查完成$(RESET)"

# 架构依赖契约检查（P2-2: importlinter 分层防腐，正式门禁）
check-architecture: ## 检查分层依赖契约（3/3 KEPT 方可通过）
	@echo "$(GREEN)运行架构契约检查...$(RESET)"
	$(PIP) install import-linter 2>/dev/null || true
	PYTHONPATH=$$(pwd)/scripts/importlinter_boot lint-imports --config .importlinter
	@echo "$(GREEN)✅ 架构契约检查完成$(RESET)"

# 代码格式化
format: ## 代码格式化
	@echo "$(GREEN)格式化代码...$(RESET)"
	$(PYTHON) -m black core/ --line-length=100
	@echo "$(GREEN)✅ 代码格式化完成$(RESET)"

# 类型检查
typecheck: ## 类型检查
	@echo "$(GREEN)运行类型检查...$(RESET)"
	$(PYTHON) -m mypy core/ --ignore-missing-imports
	@echo "$(GREEN)✅ 类型检查完成$(RESET)"

# 运行 API 服务
run: ## 运行 API 服务
	@echo "$(GREEN)启动 API 服务...$(RESET)"
	cd core/api && $(PYTHON) main.py

# 启动 Docker 服务
docker-up: ## 启动 Docker 服务
	@echo "$(GREEN)启动 Docker 服务...$(RESET)"
	$(DOCKER_COMPOSE) -f $(DOCKER_FILE) up -d
	@echo "$(GREEN)✅ Docker 服务已启动$(RESET)"
	@echo ""
	@echo "$(BLUE)服务状态:$(RESET)"
	@$(DOCKER_COMPOSE) -f $(DOCKER_FILE) ps

# 停止 Docker 服务
docker-down: ## 停止 Docker 服务
	@echo "$(YELLOW)停止 Docker 服务...$(RESET)"
	$(DOCKER_COMPOSE) -f $(DOCKER_FILE) down
	@echo "$(GREEN)✅ Docker 服务已停止$(RESET)"

# 查看 Docker 日志
docker-logs: ## 查看 Docker 日志
	@echo "$(GREEN)查看 Docker 日志...$(RESET)"
	$(DOCKER_COMPOSE) -f $(DOCKER_FILE) logs -f

# 重启 Docker 服务
docker-restart: ## 重启 Docker 服务
	@echo "$(YELLOW)重启 Docker 服务...$(RESET)"
	$(DOCKER_COMPOSE) -f $(DOCKER_FILE) restart
	@echo "$(GREEN)✅ Docker 服务已重启$(RESET)"

# 数据库迁移
db-migrate: ## 数据库迁移
	@echo "$(GREEN)运行数据库迁移...$(RESET)"
	@echo "$(RED)⚠️  数据库迁移功能待实现$(RESET)"

# 数据库备份
db-backup: ## 数据库备份
	@echo "$(GREEN)备份数据库...$(RESET)"
	@mkdir -p backups
	@$(PYTHON) -c "import datetime; print(datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))" > /tmp/timestamp.txt
	@TIMESTAMP=$$(cat /tmp/timestamp.txt); \
	pg_dump -h localhost -p 5433 -U yanyu 0379_world > backups/0379_world_$${TIMESTAMP}.sql
	@echo "$(GREEN)✅ 数据库备份完成$(RESET)"

# 生成文档
docs: ## 生成文档
	@echo "$(GREEN)生成 API 文档...$(RESET)"
	@echo "$(RED)⚠️  API 文档生成功能待实现$(RESET)"

# 安全检查
security: ## 安全检查
	@echo "$(GREEN)运行安全检查...$(RESET)"
	$(PIP) install safety 2>/dev/null || true
	safety check
	@echo "$(GREEN)✅ 安全检查完成$(RESET)"

# 依赖更新
update: ## 更新依赖
	@echo "$(GREEN)更新依赖...$(RESET)"
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt --upgrade
	@echo "$(GREEN)✅ 依赖更新完成$(RESET)"

# 环境检查
check-env: ## 环境检查
	@echo "$(GREEN)检查环境配置...$(RESET)"
	@if [ ! -f .env ]; then \
		echo "$(RED)❌ .env 文件不存在，请复制 .env.example 并配置$(RESET)"; \
		exit 1; \
	fi
	@echo "$(GREEN)✅ 环境配置检查通过$(RESET)"

# 项目状态
status: check-env ## 项目状态
	@echo "$(BLUE)YYC³ 0379-world 项目状态$(RESET)"
	@echo ""
	@echo "$(GREEN)项目信息:$(RESET)"
	@echo "  名称: $(PROJECT_NAME)"
	@echo "  版本: $(PROJECT_VERSION)"
	@echo ""
	@echo "$(GREEN)Python 环境:$(RESET)"
	@$(PYTHON) --version
	@echo ""
	@echo "$(GREEN)依赖状态:$(RESET)"
	@$(PIP) list | grep -E "(fastapi|uvicorn|psycopg2|redis)" || echo "  未安装"
	@echo ""
	@echo "$(GREEN)Docker 服务状态:$(RESET)"
	@$(DOCKER_COMPOSE) -f $(DOCKER_FILE) ps 2>/dev/null || echo "  Docker 服务未启动"

# 快速开始
quickstart: check-env install docker-up ## 快速开始（检查环境、安装依赖、启动服务）
	@echo ""
	@echo "$(GREEN)✅ 快速启动完成！$(RESET)"
	@echo ""
	@echo "$(BLUE)访问地址:$(RESET)"
	@echo "  API 服务: http://localhost:8000"
	@echo "  API 文档: http://localhost:8000/docs"
	@echo "  Prometheus: http://localhost:9090"
	@echo "  Grafana: http://localhost:3001"
	@echo ""
	@echo "$(YELLOW)下一步:$(RESET)"
	@echo "  运行 'make run' 启动 API 服务"
	@echo ""

# 版本信息
version: ## 显示版本信息
	@echo "$(BLUE)YYC³ 0379-world$(RESET)"
	@echo "版本: $(PROJECT_VERSION)"
	@echo "构建时间: $$(date '+%Y-%m-%d %H:%M:%S')"
	@echo "Python: $$(python3 --version)"
	@echo "Docker: $$(docker --version)"

# ── 运维操作统一入口 ──────────────────────────────────────

# 节点健康检查
ops-health: ## 全节点健康检查
	@echo "$(BLUE)[运维] 执行全节点健康检查...$(RESET)"
	@bash scripts/health-check.sh 2>/dev/null || bash core/scripts/health-check.sh
	@echo "$(GREEN)✅ 健康检查完成$(RESET)"

# 数据库运维
ops-db-backup: ## 数据库备份
	@echo "$(BLUE)[运维] 备份数据库...$(RESET)"
	@mkdir -p backups
	@bash scripts/pg-failover.sh backup 2>/dev/null || bash core/scripts/yyc3_db_backup.sh
	@echo "$(GREEN)✅ 数据库备份完成$(RESET)"

ops-db-setup-master: ## 设置数据库主节点
	@echo "$(BLUE)[运维] 设置 PostgreSQL 主节点...$(RESET)"
	@bash scripts/pg-setup-master.sh
	@echo "$(GREEN)✅ 主节点设置完成$(RESET)"

ops-db-setup-slave: ## 设置数据库从节点
	@echo "$(BLUE)[运维] 设置 PostgreSQL 从节点...$(RESET)"
	@bash scripts/pg-setup-slave.sh
	@echo "$(GREEN)✅ 从节点设置完成$(RESET)"

ops-db-verify: ## 验证数据库复制状态
	@echo "$(BLUE)[运维] 验证数据库复制...$(RESET)"
	@bash scripts/pg-verify-replication.sh

# 故障转移
ops-failover: ## 手动触发故障转移
	@echo "$(YELLOW)[运维] 触发故障转移...$(RESET)"
	@bash scripts/pg-failover.sh
	@bash scripts/test-failover.sh

# 负载均衡
ops-lb-setup: ## 设置负载均衡
	@echo "$(BLUE)[运维] 配置负载均衡...$(RESET)"
	@bash scripts/setup-load-balancer.sh

ops-lb-verify: ## 验证负载均衡
	@echo "$(BLUE)[运维] 验证负载均衡...$(RESET)"
	@bash scripts/verify-load-balancer.sh

# 配置同步
ops-sync-config: ## 同步配置文件到所有节点
	@echo "$(BLUE)[运维] 同步配置...$(RESET)"
	@bash scripts/sync-config.sh

ops-sync-all: ## 全量同步配置和模型挂载
	@echo "$(BLUE)[运维] 全量同步...$(RESET)"
	@bash scripts/sync-all-configs.sh

# 模型管理
ops-models-list: ## 列出所有可用模型
	@echo "$(BLUE)[运维] 查询模型列表...$(RESET)"
	@bash core/scripts/model-manager.sh list 2>/dev/null || echo "请直接访问 /v1/models"

ops-models-start: ## 启动本地模型服务
	@echo "$(BLUE)[运维] 启动本地模型...$(RESET)"
	@bash core/scripts/start-local-models.sh

# WireGuard 网络
ops-wireguard-keys: ## 生成 WireGuard 密钥
	@echo "$(BLUE)[运维] 生成 WireGuard 密钥...$(RESET)"
	@bash core/config/wireguard/generate-keys.sh

# 监控运维
ops-monitoring-start: ## 启动监控栈
	@echo "$(BLUE)[运维] 启动监控服务...$(RESET)"
	@bash core/scripts/start-monitoring.sh

# 网关测试
ops-test-gateway: ## 测试网关 API（验证全链路）
	@echo "$(BLUE)[运维] 测试网关 API...$(RESET)"
	@$(PYTHON) tests/test_gateway_api.py

ops-test-websocket: ## 测试 WebSocket 连接
	@echo "$(BLUE)[运维] 测试 WebSocket...$(RESET)"
	@$(PYTHON) scripts/test-websocket.py

# 验证并修复项目完整
ops-validate: ## 验证项目完整性（命名/结构/导入）
	@echo "$(BLUE)[运维] 验证项目完整性...$(RESET)"
	@$(PYTHON) scripts/tools/check_project_completeness.py
	@$(PYTHON) scripts/tools/check_directory_structure.py
	@$(PYTHON) scripts/tools/check_naming_convention.py
	@$(PYTHON) scripts/tools/verify_imports.py
	@echo "$(GREEN)✅ 验证完成$(RESET)"

# 有序启动（按依赖顺序）
ops-startup: ## 有序启动全栈服务（DB→Redis→Ollama→API→Monitor→LB）
	@echo "$(BLUE)══════════════════════════════════════$(RESET)"
	@echo "$(BLUE)  YYC³ 有序启动流程$(RESET)"
	@echo "$(BLUE)══════════════════════════════════════$(RESET)"
	@echo ""
	@echo "$(YELLOW)[Step 1/7] 启动 PostgreSQL...$(RESET)"
	@$(DOCKER_COMPOSE) -f $(DOCKER_FILE) up -d postgres
	@sleep 5
	@echo ""
	@echo "$(YELLOW)[Step 2/7] 启动 Redis...$(RESET)"
	@$(DOCKER_COMPOSE) -f $(DOCKER_FILE) up -d redis
	@sleep 3
	@echo ""
	@echo "$(YELLOW)[Step 3/7] 启动 Ollama...$(RESET)"
	@$(DOCKER_COMPOSE) -f $(DOCKER_FILE) up -d ollama
	@sleep 10
	@echo ""
	@echo "$(YELLOW)[Step 4/7] 启动 API Gateway...$(RESET)"
	@$(DOCKER_COMPOSE) -f $(DOCKER_FILE) up -d api
	@sleep 5
	@echo ""
	@echo "$(YELLOW)[Step 5/7] 启动 Prometheus/Monitor...$(RESET)"
	@$(DOCKER_COMPOSE) -f $(DOCKER_FILE) up -d prometheus loki grafana
	@sleep 3
	@echo ""
	@echo "$(YELLOW)[Step 6/7] 启动 HAProxy/LB...$(RESET)"
	@$(DOCKER_COMPOSE) -f $(DOCKER_FILE) up -d haproxy
	@sleep 2
	@echo ""
	@echo "$(YELLOW)[Step 7/7] 验证健康状态...$(RESET)"
	@$(MAKE) ops-test-gateway
	@echo ""
	@echo "$(GREEN)✅ 全栈启动完成！$(RESET)"
	@echo "$(BLUE)    API: http://localhost:8000$(RESET)"
	@echo "$(BLUE)    Docs: http://localhost:8000/docs$(RESET)"

# ── 完整构建 ──
build: clean install lint test ## 完整构建（清理、安装、检查、测试）
	@echo "$(GREEN)✅ 构建完成$(RESET)"

# CI/CD 流程
ci: clean install lint test security ## CI/CD 流程
	@echo "$(GREEN)✅ CI/CD 流程完成$(RESET)"
