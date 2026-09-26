# @file Dockerfile
# @description 多平台 Docker 镜像构建文件
# @author YanYuCloudCube Team <admin@0379.email>
# @version v1.0.0
# @created 2026-03-14
# @updated 2026-03-14
# @status stable
# @license MIT
# @copyright Copyright (c) 2026 YanYuCloudCube Team
# @tags docker,python,fastapi,multi-platform

FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装Node.js和npm
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# 安装Docker CLI
RUN curl -fsSL https://get.docker.com | sh

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

RUN mkdir -p /tmp/prometheus_multiproc && chmod 777 /tmp/prometheus_multiproc

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]