# YYC³ 0379-world Dockerfile
# 多阶段构建，优化镜像大小和构建速度

# ============================================
# 阶段 1: 基础镜像
# ============================================
FROM python:3.11-slim AS base

# 元数据
LABEL maintainer="YanYuCloudCube Team <admin@0379.email>"
LABEL version="1.0.0"
LABEL description="YYC³ 0379-world API Service"
LABEL project="yyc3-api-world"

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# ============================================
# 阶段 2: 构建阶段
# ============================================
FROM base AS builder

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
# PIP_INDEX_URL 可在构建时注入（NAS/ECS 国内环境走清华源）
ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip install --user -i $PIP_INDEX_URL -r requirements.txt

# ============================================
# 阶段 3: 生产镜像
# ============================================
FROM base AS production

# 从构建阶段复制依赖
COPY --from=builder /root/.local /root/.local

# 更新 PATH
ENV PATH=/root/.local/bin:$PATH

# 复制应用代码（core/api 映射为 app 包，与生产运行布局一致）
COPY core/api/ /app/app/
# AI Family Agent 独立包（PYTHONPATH=/app 使 core.agents 可导入；Phase 1 适配点 A1/A2）
COPY core/agents/ /app/core/agents/

# 创建非 root 用户
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# 切换到非 root 用户
USER appuser

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/v1/ping')" || exit 1

# 启动命令（uvicorn 多 worker + 优雅关闭，与生产容器一致）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--log-level", "info"]

# ============================================
# 阶段 4: 开发镜像
# ============================================
FROM base AS development

# 安装开发依赖
COPY requirements.txt .
RUN pip install -i ${PIP_INDEX_URL:-https://pypi.tuna.tsinghua.edu.cn/simple} -r requirements.txt

# 安装开发工具
RUN pip install \
    pytest \
    pytest-cov \
    black \
    flake8 \
    mypy \
    ipython

# 复制应用代码（core/api 映射为 app 包，与生产布局一致）
COPY core/api/ /app/app/
COPY core/agents/ /app/core/agents/

# 暴露端口
EXPOSE 8000

# 开发模式启动命令（uvicorn --reload 热重载）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ============================================
# 构建说明
# ============================================
#
# 构建生产镜像:
#   docker build -t yyc3-api-world:latest --target production .
#
# 构建开发镜像:
#   docker build -t yyc3-api-world:dev --target development .
#
# 运行容器:
#   docker run -d -p 8000:8000 --env-file .env yyc3-api-world:latest
#
# 使用 Docker Compose:
#   docker-compose up -d
#
# ============================================
