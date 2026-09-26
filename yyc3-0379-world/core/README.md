---
file: README.md
description: YYC³ 0379-world 核心文件索引
author: YanYuCloudCube Team <admin@0379.email>
version: v1.0.0
created: 2026-04-04
updated: 2026-04-04
status: stable
tags: [core],[index],[documentation]
category: general
language: zh-CN
---

> ***YanYuCloudCube***
> *言启象限 | 语枢未来*
> ***Words Initiate Quadrants, Language Serves as Core for Future***
> *万象归元于云枢 | 深栈智启新纪元*
> ***All things converge in cloud pivot; Deep stacks ignite a new era of intelligence***

---

# YYC³ 0379-world 核心文件

## 📁 目录结构

```
core/
├── api/               # FastAPI 网关（运行时映射为 app 包）
├── scripts/           # 运维脚本库（见 core/scripts/README.md）
│
├── config/            # 核心配置
│   ├── docker/        # Docker 配置
│   ├── prometheus/    # 监控配置
│   ├── redis/         # Redis 配置
│   ├── traefik/       # 网关配置
│   ├── wireguard/     # VPN 配置
│   ├── .env.0379-world/  # 环境变量
│   └── .env.example   # 配置模板
│
├── scripts/           # 核心脚本
│   ├── start-monitoring.sh          # 启动监控
│   ├── setup-grafana-dashboards.sh  # 配置仪表盘
│   ├── send-alert-notification.sh   # 发送告警
│   ├── performance-baseline.sh      # 性能基线
│   └── validate-env.sh              # 验证环境
│
├── api/               # API 代码
│   ├── main.py        # 应用入口
│   ├── api/           # API 路由
│   ├── services/      # 业务服务
│   └── config.py      # 配置管理
│
├── database/          # 数据库文件
│   └── docker/        # Docker 配置
│
└── models/            # 模型配置
    ├── MCP/           # MCP 工具配置
    └── MODEL_CONFIGURATION_PLAN.md  # 模型配置方案
```

## 🚀 快速启动

### 1. 启动监控服务

```bash
cd core/scripts
./start-monitoring.sh
```

### 2. 启动 API 服务

```bash
cd core/database/docker
docker-compose -f docker-compose.stable.yml up -d gateway
```

### 3. 启动模型服务

```bash
ollama serve
ollama run codegeex4
```

## 📖 核心文档

> 文档体系已于 2026-09 SSOT 化重构，见 [docs/README.md](../docs/README.md) 索引。

### 架构文档

- [API 全链路闭环（SSOT）](../docs/架构与部署/API全链路闭环文档.md)
- [多设备网络拓扑与架构链路](../docs/架构与部署/多设备网络拓扑与架构链路.md)

### 配置文档

- [变量清单（环境变量 SSOT）](../docs/核心参考/变量清单.md)
- [统一配置管理指南](../docs/操作指南/统一配置管理指南.md)

### 模型文档

- [设备-模型全量信息](../docs/YYC3-设备-模型全量信息文档.md)

## 🔧 核心功能

### 已完成

- ✅ 云端集成 API（api.0379.world）
- ✅ MCP 服务（多个工具）
- ✅ 后端 API（23个端点）
- ✅ 多端架构（4个节点）
- ✅ 模型存储（NFS 自动挂载）
- ✅ 自动挂载（监控和重连）

### API 端点

- GET  /v1/ping                    # 健康检查
- GET  /v1/models                  # 模型列表
- POST /v1/chat/completions        # 聊天对话
- GET  /v1/mcp/tools              # MCP 工具列表
- POST /v1/mcp/execute            # 执行 MCP 工具

## 📞 联系方式

- **邮箱**: <admin@0379.email>
- **团队**: YanYuCloudCube Team

---

**版本**: v1.0.0
**创建时间**: 2026-04-04
**维护团队**: YYC³ Team
