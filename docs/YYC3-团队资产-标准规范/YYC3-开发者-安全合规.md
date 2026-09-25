---
file: YYC3-开发者-安全合规.md
description: YYC³ 安全合规手册 — 数据安全、API密钥管理、依赖安全、XSS防护、权限控制全量规范
author: YanYuCloudCube Team <admin@0379.email>
version: v1.0.0
created: 2026-07-16
updated: 2026-07-16
status: stable
tags: [security],[compliance],[api-key],[xss],[data-protection]
category: policy
language: zh-CN
audience: developers,security
complexity: advanced
project: yyc3-ai-dev
phase: production
---

<div align="center">

> **_YanYuCloudCube_**
> _言启象限 | 语枢未来_
> **_Words Initiate Quadrants, Language Serves as Core for Future_**
> _万象归元于云枢 | 深栈智启新纪元_
> **_All things converge in cloud pivot; Deep stacks ignite a new era of intelligence_**

---

</div>

# YYC³ 安全合规手册

## 一、五高安全映射

| 五高维度 | 安全落地 |
|----------|----------|
| **高可用** | ErrorBoundary 故障隔离 + 单插件崩溃不影响全局 |
| **高性能** | 前端加密不阻塞主线程（Web Worker） |
| **高安全** | 命名空间隔离 + 密钥不入前端 + XSS 防护 |
| **高扩展** | 权限模型与插件解耦 |
| **高智能** | 异常行为检测 + 智能审计日志 |

---

## 二、数据安全

### 2.1 localStorage 安全

#### 命名空间隔离

```typescript
// ✅ 正确：每个插件使用独立命名空间
const storage = createSystemStorage("target");
storage.set("lastResult", data);
// 实际 Key: yyc3:target:lastResult

// ❌ 禁止：直接操作 localStorage
localStorage.setItem("myKey", data);  // 无命名空间，易冲突
```

#### 禁止存储的数据

| 数据类型 | 禁止原因 |
|----------|----------|
| API 密钥 | 前端存储可被提取 |
| 用户密码 | 明文/哈希均不可 |
| 敏感个人信息 | 身份证/银行卡/手机号 |
| 认证 Token | 使用 HttpOnly Cookie |

### 2.2 数据传输安全

```typescript
// ✅ HTTPS 强制
const API_BASE = "https://api.yyc3.example";

// ✅ 敏感字段脱敏
function maskPhone(phone: string): string {
  return phone.replace(/(\d{3})\d{4}(\d{4})/, "$1****$2");
}
```

---

## 三、API 密钥管理

### 3.1 三条铁律

```
1. 前端代码永远不直接包含 API 密钥
2. API 调用必须通过后端代理
3. 密钥通过 CI/CD Secrets 注入环境变量
```

### 3.2 架构

```
浏览器  →  后端代理  →  OpenAI / LLM API
         ↑ 密钥在此
         (前端只看到代理 URL)
```

### 3.3 后端代理示例

```typescript
// server/api/chat.ts (后端代码，不随前端发布)
const OPENAI_KEY = process.env.OPENAI_API_KEY; // 从服务器环境变量读取

export async function handler(req, res) {
  const response = await fetch("https://api.openai.com/v1/chat/completions", {
    headers: { "Authorization": `Bearer ${OPENAI_KEY}` },
    method: "POST",
    body: JSON.stringify(req.body),
  });
  res.json(await response.json());
}
```

### 3.4 开发环境密钥

```bash
# .env.development (已 .gitignore)
VITE_YYC3_API_PROXY=http://localhost:3000/api

# 开发时使用 mock，不调用真实 API
VITE_YYC3_USE_MOCK=true
```

---

## 四、XSS 防护

### 4.1 React 自动转义

React 默认对 JSX 插值进行 HTML 转义，以下场景需额外注意：

```typescript
// ✅ 安全：React 自动转义
<div>{userInput}</div>

// ⚠️ 危险：dangerouslySetInnerHTML 绕过转义
<div dangerouslySetInnerHTML={{ __html: rawHtml }} />

// ✅ 如果必须用，先净化
import DOMPurify from "dompurify";
<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(rawHtml) }} />
```

### 4.2 AI 回复内容

AI 生成的回复可能包含恶意 HTML，必须净化：

```typescript
// ✅ AI 回复渲染前净化
function renderAIResponse(content: string) {
  const sanitized = DOMPurify.sanitize(content);
  return <div dangerouslySetInnerHTML={{ __html: sanitized }} />;
}
```

---

## 五、依赖安全

### 5.1 依赖审计

```bash
# pnpm 内置审计
pnpm audit

# 自动修复
pnpm audit --fix
```

### 5.2 依赖红线

| 规则 | 要求 |
|------|------|
| 新增依赖 | 必须 review，记录用途 |
| 版本锁定 | 使用 `pnpm-lock.yaml` |
| 定期审计 | 每月执行 `pnpm audit` |
| 禁止来源 | 禁止安装非 npm 官方源包 |

---

## 六、权限控制

### 6.1 前端路由守卫

```typescript
// 路由配置中添加权限检查
{
  path: "/admin",
  element: <RequireAuth role="admin"><AdminPage /></RequireAuth>,
}
```

### 6.2 插件可见性控制

```typescript
// SystemRegistration 可扩展权限字段（Phase 2）
{
  id: "admin",
  name: "系统管理",
  requiredRole: "admin",  // ← 仅管理员可见
}
```

---

## 七、代码安全 Checklist

| # | 检查项 | 验证 |
|---|--------|------|
| 1 | API 密钥不在前端代码中 | `grep -r "sk-" src/` 无结果 |
| 2 | localStorage 使用命名空间 | 所有调用通过 `createSystemStorage` |
| 3 | AI 回复经过 XSS 净化 | DOMPurify 覆盖所有动态 HTML |
| 4 | 依赖无已知漏洞 | `pnpm audit` 零高危 |
| 5 | HTTPS 强制 | 生产环境 HTTP 自动跳转 HTTPS |
| 6 | 错误信息不泄露敏感数据 | catch 块不返回堆栈/SQL |

---

## 变更历史

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|----------|------|
| v1.0.0 | 2026-07-16 | 初始版本 | YanYuCloudCube Team |
