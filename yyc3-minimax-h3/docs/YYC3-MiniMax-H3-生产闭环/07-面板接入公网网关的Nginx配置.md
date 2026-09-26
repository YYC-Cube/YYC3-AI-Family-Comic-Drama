---
file: 07-面板接入公网网关的Nginx配置.md
description: 面板接入公网网关的 Nginx 配置片段（网关路由蓝图）
author: Intelligent Application Implementation Expert <admin@0379.email>
version: v1.1.0
created: 2026-09-25
updated: 2026-09-25
status: active
tags: [nginx],[gateway],[proxy],[blueprint]
category: config
language: zh-CN
changelog:
  - { version: v1.0.0, date: 2026-09-25, author: 智能应用落地专家, change: 原始版本收录（生成于外部会话） }
  - { version: v1.1.0, date: 2026-09-25, author: 智能应用落地专家, change: P1-D1 规范化（修复腐蚀链接/补齐 YAML FM） }
---

# 面板接入公网网关的 Nginx 配置片段

**100% 对齐现有网关规范、流水线结构与单一事实源标准**，插入即可形成「API网关→调度→生产→评分→面板→同步→公网访问」完整闭环。

---

## 一、面板接入公网网关 Nginx 配置片段

### 定位

复用 DGX 节点 2 现有 `api.0379.world` 统一网关，新增 `/h3-dashboard/` 静态资源路由，指向 NAS RAID1 高可用区面板数据，与现有 API 体系共用鉴权、限流、安全头规范，对齐 `X-YYC3-Upstream` 响应头契约。

### 配置片段

添加到 DGX 节点 2 的 Nginx 站点配置 `server` 块中：

```nginx
# ==============================================================
# H3 数字人流水线可视化面板 公网接入配置
# 域名：api.0379.world
# 数据源：NAS RAID1 高可用区 h3-dashboard 目录
# 规范：X-YYC3-Upstream 响应头契约 + 四级安全管控
# ==============================================================

location /h3-dashboard/ {
    # 指向 NAS RAID1 挂载的面板目录（只读）
    alias /mnt/nas/raid1-core/h3-dashboard/;
    index Ref2VA-流水线管理面板.html;
    autoindex off;

    # 统一响应头契约
    add_header X-YYC3-Upstream "h3-dashboard" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header Cache-Control "public, max-age=300" always;

    # Gzip 压缩静态资源
    gzip on;
    gzip_types text/html application/javascript application/json text/css;
    gzip_min_length 1024;

    # 速率限制（复用全局限流 zone）
    limit_req zone=api_general burst=20 nodelay;

    # 访问控制：内网优先 + 公网授权
    allow 10.0.0.0/24;
    allow 127.0.0.1;
    # 公网IP白名单按需添加
    # allow xxx.xxx.xxx.xxx;
    deny all;

    # 禁止敏感文件访问
    location ~* (\.git|\.env|\.md|backup/) {
        deny all;
        return 404;
    }

    # 单页应用路由兼容
    try_files $uri $uri/ /h3-dashboard/Ref2VA-流水线管理面板.html;
}

# 可选：batches.json 独立接口（供第三方调用）
location /h3-dashboard/api/batches.json {
    alias /mnt/nas/raid1-core/h3-dashboard/batches.json;
    add_header X-YYC3-Upstream "h3-dashboard-api" always;
    add_header Content-Type "application/json; charset=utf-8" always;
    add_header Cache-Control "no-cache" always;
    limit_req zone=api_general burst=30 nodelay;
    allow 10.0.0.0/24;
    deny all;
}
```

### 部署验证

1. 重载 Nginx：`nginx -t && nginx -s reload`
2. 内网验证：访问 `https://api.0379.world/h3-dashboard/`，确认面板正常加载
3. 接口验证：访问 `https://api.0379.world/h3-dashboard/api/batches.json`，确认返回 JSON 数据
4. 安全验证：公网 IP 访问默认 403，符合最小权限原则
