# YYC³ 运维脚本库

> 实用、高效、可靠的运维脚本集合

---

## 📋 脚本清单

### 🔍 监控检查类

| 脚本 | 用途 | 执行时间 |
|------|------|---------|
| **health-check.sh** | 快速健康检查 | < 10秒 |
| **check-all-nodes.sh** | 全面状态检查 | ~ 30秒 |
| **performance-baseline.sh** | 性能基线测试 | ~ 60秒 |

### 🛠️ 运维管理类

| 脚本 | 用途 | 功能数 |
|------|------|--------|
| **yyc3-ops.sh** | 快速运维工具 | 8+ |
| **start-monitoring.sh** | 启动监控服务 | 1 |
| **validate-env.sh** | 环境变量验证 | 1 |

### 📢 告警通知类

| 脚本 | 用途 | 支持渠道 |
|------|------|---------|
| **send-alert-notification.sh** | 发送告警通知 | 邮件、钉钉、企业微信 |

### 📊 可视化类

| 脚本 | 用途 | 依赖 |
|------|------|------|
| **setup-grafana-dashboards.sh** | 配置 Grafana 仪表盘 | Grafana |

---

## 🚀 快速开始

### 1. 快速健康检查

```bash
./health-check.sh
```

**输出示例**:
```
========================================
YYC³ 快速健康检查
========================================

[yyc3-22] MacBook Pro M4 Max
----------------------------------------
  PostgreSQL 15: ✓ 运行中
  Redis: ✓ 运行中
  yyc3_mcp: ✓ 运行中

[yyc3-33] 阿里云 ECS
----------------------------------------
  nginx: ✓ 运行中
  Docker: ✓ 运行中
  frps: ✓ 运行中
  API (8000): ✓ 运行中

========================================
✅ 健康检查完成
========================================
```

### 2. 全面状态检查

```bash
./check-all-nodes.sh
```

### 3. 快速运维

```bash
# 查看帮助
./yyc3-ops.sh help

# 检查节点状态
./yyc3-ops.sh status yyc3-33

# 查看日志
./yyc3-ops.sh logs yyc3-33 nginx

# 重启服务
./yyc3-ops.sh restart yyc3-33 nginx
```

---

## 📚 详细文档

完整的脚本使用指南请查看：[运维脚本使用指南.md](./运维脚本使用指南.md)

---

## 🎯 使用场景

### 日常巡检
```bash
# 每天早上执行
./health-check.sh
```

### 问题排查
```bash
# 1. 快速检查
./health-check.sh

# 2. 深度检查
./check-all-nodes.sh

# 3. 查看日志
./yyc3-ops.sh logs yyc3-33 nginx
```

### 部署前检查
```bash
# 验证环境
./validate-env.sh

# 检查服务
./health-check.sh

# 检查 Docker
./yyc3-ops.sh docker yyc3-33
```

---

## 📊 节点信息

| 节点 | 设备 | IP | 角色 |
|------|------|----|----|
| **yyc3-22** | MacBook Pro M4 Max | 192.168.3.22 | 主开发机 |
| **yyc3-33** | 阿里云 ECS | 39.97.53.176 | 生产服务器 |
| **yyc3-45** | NAS F4-423 | 192.168.3.45 | 存储服务 |
| **yyc3-77** | iMac M4 | 192.168.3.77 | 副开发机 |

---

## 🔧 自定义扩展

### 添加自定义检查

编辑 `health-check.sh`，添加新的检查项：

```bash
echo -n "  自定义服务: "
if ssh yyc3-33 "systemctl is-active custom-service" 2>/dev/null | grep -q "active"; then
    echo -e "${GREEN}✓ 运行中${NC}"
else
    echo -e "${RED}✗ 未运行${NC}"
fi
```

### 添加新的运维命令

编辑 `yyc3-ops.sh`，添加新命令：

```bash
custom_command() {
    local node=$1
    echo "执行自定义命令..."
    ssh $node "your-custom-command"
}
```

---

## 🆘 故障排除

### 脚本无法执行

```bash
# 添加执行权限
chmod +x *.sh
```

### SSH 连接失败

```bash
# 检查 SSH 配置
cat ~/.ssh/config

# 测试连接
ssh yyc3-33 "echo 连接成功"
```

---

## 📞 获取帮助

```bash
# 查看脚本帮助
./yyc3-ops.sh help

# 查看脚本内容
cat health-check.sh

# 查看详细指南
cat 运维脚本使用指南.md
```

---

**维护团队**: YanYuCloudCube Team  
**最后更新**: 2026-04-06
