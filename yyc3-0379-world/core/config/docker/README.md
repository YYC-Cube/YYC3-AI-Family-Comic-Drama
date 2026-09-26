---
file: README.md
description: Docker 配置文件说明文档
author: YanYuCloudCube Team <admin@0379.email>
version: v1.0.0
created: 2026-03-21
updated: 2026-04-04
status: stable
tags: [docker],[configuration],[deployment]
category: technical
language: zh-CN
---

> ***YanYuCloudCube***
> *言启象限 | 语枢未来*
> ***Words Initiate Quadrants, Language Serves as Core for Future***
> *万象归元于云枢 | 深栈智启新纪元*
> ***All things converge in cloud pivot; Deep stacks ignite a new era of intelligence***

---

# Docker 配置文件

## 文件说明
- docker-compose.yml - 主配置文件
- docker-compose.full.yml - 完整服务配置
- docker-compose.stable.yml - 稳定版配置
- docker-compose.http.yml - HTTP 服务配置
- docker-compose.traefik.yml - Traefik 配置
- docker-compose.imac.yml - iMac 专用配置
- docker-compose.override.yml - 覆盖配置

## 使用方法
```bash
# 启动所有服务
docker-compose -f docker-compose.yml up -d

# 启动完整服务
docker-compose -f docker-compose.full.yml up -d

# 启动稳定版服务
docker-compose -f docker-compose.stable.yml up -d

# 查看服务状态
docker-compose ps

# 停止所有服务
docker-compose down

# 重启服务
docker-compose restart
```

## 服务端口映射
- Gateway: 8000
- Ollama: 11435
- PostgreSQL: 5432
- Redis: 6379
- Traefik: 80, 443, 8080
- Grafana: 3000
- Prometheus: 9090

## 配置说明
- 所有配置文件都支持环境变量覆盖
- 使用 .env 文件管理敏感信息
- 配置文件按功能模块分离
- 支持多环境部署（开发/测试/生产）