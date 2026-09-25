---
file: YYC3-测试用例-审核验收.md
description: YYC³ 项目闭环验收系统 — 测试用例生成与审核标准（第三类验收阶段）
author: YanYuCloudCube Team <admin@0379.email>
version: v2.0.0
created: 2026-05-25
updated: 2026-05-30
status: stable
tags: [验收],[测试用例],[单元测试],[集成测试],[E2E],[覆盖率],[闭环]
category: acceptance
language: zh-CN
audience: developers,qa-engineers,test-managers
complexity: advanced
---

<div align="center">

# YYC³（YanYuCloudCube）闭环验收系统

## 第三类：测试用例审核验收

> **_YanYuCloudCube_**
> _言启象限 | 语枢未来_
> **_Words Initiate Quadrants, Language Serves as Core for Future_**
> _万象归元于云枢 | 深栈智启新纪元_
> **_All things converge in cloud pivot; Deep stacks ignite a new era of intelligence_**

---

| 属性         | 值                                    |
| ------------ | ------------------------------------- |
| **文档版本** | v1.0.0                                |
| **发布日期** | 2026-05-25                            |
| **验收阶段** | 第三阶段：测试用例类                     |
| **验收性质** | 测试覆盖度保障 · 质量门禁控制          |
| **适用范围** | Next.js + React + Vitest + Playwright |

</div>

---

## 📋 目录

- [🎯 验收目标与定位](#-验收目标与定位)
- [📐 五维评估框架](#-五维评估框架)
- [🧪 测试类型体系](#-测试类型体系)
- [📊 测试覆盖率标准](#-测试覆盖率标准)
- [⚙️ 测试框架配置](#️-测试框架配置)
- [✅ 验收标准体系](#-验收标准体系)
- [📋 输出报告模板](#-输出报告模板)
- [🔄 闭环验证机制](#-闭环验证机制)

---

## 🎯 验收目标与定位

### 核心使命

作为YYC³闭环验收系统的**质量保障核心**，测试用例审核验收承担着建立全面测试体系、确保代码质量可度量、构建自动化质量门禁的关键职责。本阶段聚焦于从单元到端到端的全层次测试覆盖。

### 战略定位

```
┌─────────────────────────────────────────────────────────────┐
│              闭环验收系统流水线                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  第一类：代码语法测试核验 ✅                                  │
│  第二类：功能逻辑验收标准 ✅                                  │
│       ↓ 已通过                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  ⭐ 第三类：测试用例审核验收（当前阶段）               │   │
│  │  ├── 单元测试覆盖率 > 80%                            │   │
│  │  ├── 集成测试覆盖率 > 70%                            │   │
│  │  ├── E2E测试覆盖主要流程                              │   │
│  │  └── 性能/安全/兼容性测试通过                         │   │
│  └─────────────────────────────────────────────────────┘   │
│                          ↓                                  │
│  第四类：组件测试验收标准                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 核心价值主张

| 维度       | 价值主张                                   | 实现方式                              |
| ---------- | ------------------------------------------ | ------------------------------------- |
| **时间维** | 快速反馈循环，问题早期发现                  | CI/CD集成，PR自动触发，并行执行      |
| **空间维** | 全量代码覆盖，无死角盲区                    | 多维度覆盖率统计，分支/语句/函数覆盖 |
| **属性维** | 质量可度量，标准可量化                      | 覆盖率阈值，质量评分，趋势分析        |
| **事件维** | 变更即时验证，回归风险可控                  | 增量测试，影响分析，智能选择          |
| **关联维** | 层次清晰，职责明确                          | 测试金字塔，分层策略，依赖隔离        |

---

## 📐 五维评估框架

### 时间维度评估

#### 度量指标

| 指标名称                | 目标值    | 测量方法              | 优先级 |
| ----------------------- | --------- | --------------------- | ------ |
| 单元测试执行时间        | < 60s     | Vitest 执行耗时       | P0     |
| 集成测试执行时间        | < 5min    | Vitest + MSW          | P0     |
| E2E测试执行时间         | < 10min   | Playwright            | P1     |
| 全量测试套件总耗时      | < 20min   | CI Pipeline           | P1     |
| PR增量测试响应时间      | < 3min    | CI/CD 反馈延迟        | P0     |
| 测试失败定位时间        | < 10min   | 日志+截图分析         | P2     |

### 空间维度评估

#### 测试金字塔结构

```
                    /\
                   /  \
                  / E2E \          10%  (端到端测试)
                 /--------\
                / 集成测试 \       20%  (API集成测试)
               /------------\
              /   单元测试    \     70%  (组件/函数测试)
             /----------------\
```

#### 覆盖率分布矩阵

```
┌──────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
│   测试层     │   目标数量   │   通过率     │   覆盖率     │   平均耗时   │
├──────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ 单元测试     │   ≥500       │   >98%      │   >80%       │   <60s      │
│ 组件测试     │   ≥100       │   >95%      │   >85%       │   <120s     │
│ 集成测试     │   ≥80        │   >90%      │   >70%       │   <300s     │
│ E2E测试      │   ≥30        │   >85%      │   流程100%   │   <600s     │
│ 性能测试     │   ≥10        │   100%      │   场景100%    │   <180s     │
│ 安全测试     │   ≥15        │   100%      │   漏洞100%    │   <240s     │
└──────────────┴──────────────┴──────────────┴──────────────┴──────────────┘
```

### 属性维度评估

#### 质量属性指标

| 属性类别       | 具体指标                   | 目标值   | 权重   | 测量方法              |
| -------------- | -------------------------- | -------- | ------ | --------------------- |
| **完备性**      | 语句覆盖率                 | > 80%    | 15%    | c8 / istanbul         |
|                | 分支覆盖率                 | > 75%    | 15%    | c8 / istanbul         |
|                | 函数覆盖率                 | > 85%    | 10%    | c8 / istanbul         |
|                | 行覆盖率                   | > 78%    | 10%    | c8 / istanbul         |
| **可靠性**      | 测试通过率                 | > 98%    | 15%    | Vitest / Playwright   |
|                | Flaky Test比例             | < 2%     | 10%    | 历史运行记录          |
|                | 测试隔离性                 | 100%     | 5%     | 并发执行验证          |
| **有效性**      | Bug检出率                  | > 90%    | 10%    | 缺陷回溯分析          |
|                | 回归测试覆盖率             | > 95%    | 5%     | 变更影响分析          |
|                | Mock使用合理性             | < 30%    | 5%     | 代码审查              |
| **可维护性**    | 测试代码复杂度             | < 10     | 5%     | 圈复杂度计算          |
|                | 测试命名规范性             | 100%     | 5%     | 命名规则检查          |

### 事件维度评估

#### 测试触发事件矩阵

| 事件类型               | 触发条件                 | 执行范围                       | 反馈时间 | 告警级别 |
| ---------------------- | ------------------------ | ------------------------------ | -------- | -------- |
| PR提交                 | Pull Request 创建        | 变更文件相关测试 + 冒烟测试    | < 5min   | Error    |
| 主分支合并             | Merge to main            | 全量测试套件                   | < 20min  | Warning  |
| 定时任务               | Nightly Build            | 全量测试 + 覆盖率报告          | < 30min  | Info     |
| 手动触发               | pnpm test                | 用户指定范围                   | 即时     | -        |
| 发布前检查             | Release Branch           | 全量测试 + 性能 + 安全         | < 45min  | Critical |

### 关联维度评估

#### 测试依赖关系图

```
┌─────────────────────────────────────────────────────────────┐
│                  测试依赖关系矩阵                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  单元测试层                                                  │
│  ├── 无外部依赖                                             │
│  ├── 可独立并行执行                                         │
│  └── 执行顺序无关                                           │
│                                                             │
│  组件测试层                                                  │
│  ├── 依赖 React Testing Library                             │
│  ├── 需要 JSDOM 环境                                        │
│  └── 可按组件模块分组                                       │
│                                                             │
│  集成测试层                                                  │
│  ├── 依赖 MSW (Mock Service Worker)                         │
│  ├── 需要 API Mock 数据                                     │
│  └── 有执行顺序要求（如先登录）                              │
│                                                             │
│  E2E测试层                                                   │
│  ├── 依赖完整应用环境                                       │
│  ├── 需要数据库连接                                         │
│  ├── 严格串行执行                                           │
│  └── 需要测试数据准备和清理                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧪 测试类型体系

### 1. 单元测试 (Unit Tests)

#### 1.1 测试范围

```typescript
// ✅ 单元测试示例：工具函数
// src/__tests__/utils/formatDate.test.ts
import { formatDate, formatCurrency, parseQueryString } from '@/utils/format';

describe('格式化工具函数', () => {
  describe('formatDate', () => {
    it('应正确格式化日期为 YYYY-MM-DD', () => {
      const date = new Date('2026-05-25T12:00:00Z');
      expect(formatDate(date)).toBe('2026-05-25');
    });

    it('应处理空值返回默认字符串', () => {
      expect(formatDate(null)).toBe('-');
      expect(formatDate(undefined)).toBe('-');
    });

    it('应支持自定义格式', () => {
      const date = new Date('2026-05-25T12:00:00Z');
      expect(formatDate(date, 'MM/DD/YYYY')).toBe('05/25/2026');
    });
  });

  describe('formatCurrency', () => {
    it('应正确格式化货币金额', () => {
      expect(formatCurrency(1234.5)).toBe('¥1,234.50');
      expect(formatCurrency(0)).toBe('¥0.00');
    });

    it('应处理负数', () => {
      expect(formatCurrency(-100)).toBe('-¥100.00');
    });
  });
});
```

#### 1.2 覆盖率要求

| 文件类型         | 目标覆盖率 | 必须覆盖的场景                     |
| --------------- | ---------- | ------------------------------------ |
| 工具函数 (utils) | 100%       | 所有导出函数、边界条件、异常输入     |
| Hooks            | > 95%      | 正常状态、加载态、错误态、卸载清理   |
| Store/Context   | > 90%      | 所有 actions、getters、状态转换     |
| 类型定义         | > 80%      | 类型守卫、类型断言、泛型约束        |
| 配置文件         | > 70%      | 默认值、环境变量解析、校验逻辑      |

### 2. 组件测试 (Component Tests)

#### 2.1 测试策略

```tsx
// ✅ 组件测试示例：用户卡片
// src/components/UserCard/__tests__/UserCard.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { UserCard } from '../UserCard';

const mockUser = {
  id: '1',
  name: '张三',
  email: 'zhangsan@example.com',
  avatar: '/avatar.jpg',
  role: 'admin',
};

describe('UserCard 组件', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('应正确渲染用户信息', () => {
    render(<UserCard user={mockUser} />);

    expect(screen.getByText('张三')).toBeInTheDocument();
    expect(screen.getByText('zhangsan@example.com')).toBeInTheDocument();
    expect(screen.getByAltText('张三的头像')).toHaveAttribute('src', '/avatar.jpg');
  });

  it('应在点击时调用 onClick 回调', async () => {
    const mockOnClick = jest.fn();
    const user = userEvent.setup();

    render(<UserCard user={mockUser} onClick={mockOnClick} />);

    await user.click(screen.getByRole('button'));

    expect(mockOnClick).toHaveBeenCalledTimes(1);
    expect(mockOnClick).toHaveBeenCalledWith(mockUser);
  });

  it('应显示管理员徽章', () => {
    render(<UserCard user={mockUser} />);

    expect(screen.getByText('管理员')).toBeInTheDocument();
  });

  it('应处理加载状态', () => {
    render(<UserCard isLoading />);

    expect(screen.getByTestId('skeleton-loader')).toBeInTheDocument();
  });

  it('应处理错误状态', () => {
    render(<UserCard error="用户数据加载失败" />);

    expect(screen.getByText('用户数据加载失败')).toBeInTheDocument();
    expect(screen.getByRole('alert')).toBeInTheDocument();
  });
});
```

#### 2.2 测试场景清单

| 场景类别       | 测试点                           | 优先级 |
| -------------- | -------------------------------- | ------ |
| **渲染测试**   | 正常渲染、空数据、加载中、错误   | P0     |
| **交互测试**   | 点击、输入、拖拽、表单提交       | P0     |
| **状态测试**   | Props变化、State更新、副作用     | P0     |
| **事件测试**   | 回调触发、事件冒泡、自定义事件   | P1     |
| **样式测试**   | 类名应用、响应式、主题切换       | P1     |
| **无障碍测试** | 键盘导航、ARIA标签、屏幕阅读器   | P2     |

### 3. 集成测试 (Integration Tests)

#### 3.1 API集成测试

```typescript
// ✅ API集成测试示例
// src/__tests__/api/projects.integration.test.ts
import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';
import { getProjects, createProject, deleteProject } from '@/api/projects';

const server = setupServer(
  // Mock GET /api/projects
  http.get('/api/projects', () => {
    return HttpResponse.json([
      { id: '1', name: 'Project A', status: 'active' },
      { id: '2', name: 'Project B', status: 'completed' },
    ]);
  }),

  // Mock POST /api/projects
  http.post('/api/projects', async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({ id: '3', ...body }, { status: 201 });
  }),

  // Mock DELETE /api/projects/:id
  http.delete('/api/projects/:id', ({ params }) => {
    return HttpResponse.json({ success: true, deletedId: params.id });
  }),
);

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('项目API集成测试', () => {
  it('应成功获取项目列表', async () => {
    const projects = await getProjects();

    expect(projects).toHaveLength(2);
    expect(projects[0]).toMatchObject({
      id: '1',
      name: 'Project A',
      status: 'active',
    });
  });

  it('应成功创建新项目', async () => {
    const newProject = await createProject({
      name: 'Project C',
      description: 'New project',
    });

    expect(newProject.id).toBe('3');
    expect(newProject.name).toBe('Project C');
  });

  it('应处理服务器错误', async () => {
    server.use(
      http.get('/api/projects', () => {
        return new HttpResponse(null, { status: 500, statusText: 'Internal Server Error' });
      })
    );

    await expect(getProjects()).rejects.toThrow('Failed to fetch projects');
  });

  it('应处理网络错误', async () => {
    server.use(
      http.get('/api/projects', () => {
        return new HttpResponse.networkError('Network error')
      })
    );

    await expect(getProjects()).rejects.toThrow('Network error');
  });
});
```

#### 3.2 数据库集成测试

```typescript
// ✅ 数据库集成测试示例
// src/__tests__/db/users.integration.test.ts
import { describe, it, expect, beforeAll, afterAll, beforeEach } from 'vitest';
import { db } from '@/lib/database';
import { createUser, getUserById, updateUser } from '@/repositories/userRepository';

describe('用户数据库操作集成测试', () => {
  let testUserId: string;

  beforeAll(async () => {
    // 使用测试数据库
    await db.connect(process.env.TEST_DATABASE_URL!);
  });

  afterAll(async () => {
    await db.disconnect();
  });

  beforeEach(async () => {
    // 清理测试数据
    await db.query('DELETE FROM users WHERE email LIKE ?', ['%test.com%']);
  });

  it('应创建并查询用户', async () => {
    const userData = {
      name: 'Test User',
      email: 'test@example.com',
      password: 'hashedpassword123',
    };

    const user = await createUser(userData);
    testUserId = user.id;

    expect(user.id).toBeDefined();
    expect(user.name).toBe(userData.name);
    expect(user.createdAt).toBeInstanceOf(Date);

    // 查询验证
    const fetchedUser = await getUserById(testUserId);
    expect(fetchedUser).toEqual(user);
  });

  it('应更新用户信息', async () => {
    const updatedUser = await updateUser(testUserId, {
      name: 'Updated Name',
    });

    expect(updatedUser.name).toBe('Updated Name');
    expect(updatedUser.updatedAt).not.toBeNull();
  });

  it('应处理唯一约束冲突', async () => {
    const duplicateData = {
      name: 'Another User',
      email: 'test@example.com', // 相同邮箱
      password: 'anotherhash',
    };

    await expect(createUser(duplicateData)).rejects.toThrow('Duplicate entry');
  });
});
```

### 4. 端到端测试 (E2E Tests)

#### 4.1 Playwright配置

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html', { open: 'never' }],
    ['junit', { outputFile: 'results/junit.xml' }],
  ],
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
  ],
  webServer: {
    command: 'pnpm dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

#### 4.2 E2E测试用例

```typescript
// e2e/user-workflow.spec.ts
import { test, expect } from '@playwright/test';

test.describe('用户工作流', () => {
  test.beforeEach(async ({ page }) => {
    // 登录
    await page.goto('/login');
    await page.fill('[data-testid="email-input"]', 'test@example.com');
    await page.fill('[data-testid="password-input"]', 'password123');
    await page.click('[data-testid="login-button"]');
    await page.waitForURL('/dashboard');
  });

  test('应完成创建项目的完整流程', async ({ page }) => {
    // 导航到项目页面
    await page.click('[data-testid="nav-projects"]');
    await expect(page).toHaveURL(/\/projects/);

    // 点击新建按钮
    await page.click('[data-testid="create-project-btn"]');
    await expect(page.locator('[data-testid="project-modal"]')).toBeVisible();

    // 填写表单
    await page.fill('[data-testid="project-name"]', 'E2E Test Project');
    await page.fill('[data-testid="project-description"]', 'Created by E2E test');
    await page.selectOption('[data-testid="project-type"]', 'web-app');

    // 提交表单
    await page.click('[data-testid="submit-btn"]');

    // 验证成功
    await expect(page.locator('[data-testid="toast-success"]')).toContainText('项目创建成功');
    await expect(page.locator('text=E2E Test Project')).toBeVisible();
  });

  test('应正确处理文件上传流程', async ({ page }) => {
    // 进入项目详情
    await page.goto('/projects/test-project-id');

    // 上传文件
    const fileChooserPromise = page.waitForEvent('filechooser');
    await page.click('[data-testid="upload-btn"]');
    const fileChooser = await fileChooserPromise;

    await fileChooser.setFiles({
      name: 'test-document.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('fake pdf content'),
    });

    // 验证上传成功
    await expect(page.locator('[data-testid="file-item"]')).toContainText('test-document.pdf');
  });

  test('AI对话功能应正常工作', async ({ page }) => {
    // 打开AI助手面板
    await page.click('[data-testid="ai-assistant-toggle"]');
    await expect(page.locator('[data-testid="ai-chat-panel"]')).toBeVisible();

    // 发送消息
    await page.fill('[data-testid="ai-input"]', '帮我生成一个React组件');
    await page.click('[data-testid="ai-send-btn"]');

    // 等待响应
    await expect(page.locator('[data-testid="ai-response"]')).toBeVisible({ timeout: 15000 });

    // 验证响应内容包含代码
    const responseText = await page.locator('[data-testid="ai-response"]').textContent();
    expect(responseText).toContain('function');
    expect(responseText).toContain('return');
  });
});

test.describe('异常场景处理', () => {
  test('网络断开时应显示离线提示', async ({ page }) => {
    // 模拟离线
    await page.context().setOffline(true);

    // 尝试操作
    await page.goto('/dashboard');
    await expect(page.locator('[data-testid="offline-banner"]')).toBeVisible();

    // 恢复在线
    await page.context().setOffline(false);
    await expect(page.locator('[data-testid="offline-banner"]')).toBeHidden();
  });

  test('会话过期时应跳转登录页', async ({ page }) => {
    // 清除认证token
    await page.evaluate(() => {
      localStorage.removeItem('auth_token');
    });

    // 刷新页面
    await page.reload();
    await expect(page).toHaveURL('/login');
    await expect(page.locator('[data-testid="session-expired-msg"]')).toBeVisible();
  });
});
```

### 5. 性能测试 (Performance Tests)

#### 5.1 Lighthouse性能审计

```javascript
// e2e/performance.spec.ts
import { test, expect } from '@playwright/test';
import lighthouse from 'lighthouse';
import * as fs from 'fs';

test.describe('性能基准测试', () => {
  let results: any;

  test('首页性能应符合Core Web Vitals标准', async ({ page }) => {
    // 使用Lighthouse进行性能审计
    results = await lighthouse('http://localhost:3000', {
      port: 9222,
      output: 'json',
      logLevel: 'error',
      onlyCategories: ['performance'],
    });

    const perfScore = results.categories.performance.score * 100;
    console.log(`Performance Score: ${perfScore}`);

    // 验证各项指标
    const audits = results.audits;

    // FCP < 1.8s
    expect(parseFloat(audits['first-contentful-paint'].numericValue)).toBeLessThan(1800);

    // LCP < 2.5s
    expect(parseFloat(audits['largest-contentful-paint'].numericValue)).toBeLessThan(2500);

    // CLS < 0.1
    expect(parseFloat(audits['cumulative-layout-shift'].numericValue)).toBeLessThan(0.1);

    // TTI < 3.8s
    expect(parseFloat(audits['interactive'].numericValue)).toBeLessThan(3800);

    // 总分 >= 90
    expect(perfScore).toBeGreaterThanOrEqual(90);
  });

  test.afterAll(() => {
    if (results) {
      // 保存详细报告
      fs.writeFileSync(
        `lighthouse-report-${new Date().toISOString().split('T')[0]}.json`,
        JSON.stringify(results, null, 2)
      );
    }
  });
});
```

### 6. 安全测试 (Security Tests)

#### 6.1 OWASP Top 10检查

```typescript
// e2e/security.spec.ts
import { test, expect } from '@playwright/test';

test.describe('安全漏洞检测', () => {
  test('应防止XSS攻击', async ({ page }) => {
    // 尝试注入XSS payload
    const xssPayload = '<script>alert("xss")</script>';

    await page.goto('/search?q=' + encodeURIComponent(xssPayload));

    // 验证脚本未被执行
    const alertFired = await page.evaluate(() => {
      return window.__xssAlertFired || false;
    });
    expect(alertFired).toBeFalsy();

    // 验证内容被正确转义
    const content = await page.content();
    expect(content).not.toContain('<script>');
  });

  test('应防止CSRF攻击', async ({ page }) => {
    // 检查表单是否包含CSRF token
    await page.goto('/settings/profile');

    const csrfToken = await page.evaluate(() => {
      const form = document.querySelector('form');
      const input = form?.querySelector('input[name="_csrf"]');
      return input?.value;
    });

    expect(csrfToken).toBeTruthy();
    expect(csrfToken).toHaveLength(32); // 假设CSRF token长度为32
  });

  test('敏感信息不应暴露在客户端', async ({ page }) => {
    await page.goto('/');

    // 检查localStorage
    const localStorageData = await page.evaluate(() => {
      return Object.entries(localStorage);
    });

    for (const [key, value] of localStorageData) {
      expect(key).not.toContain('password');
      expect(key).not.toContain('secret');
      expect(String(value)).not.toMatch(/Bearer\s+\w+/);
    }

    // 检查JavaScript变量
    const hasSensitiveData = await page.evaluate(() => {
      const scripts = Array.from(document.querySelectorAll('script'));
      return scripts.some(script => {
        const content = script.textContent || '';
        return content.includes('api_key') ||
               content.includes('password') ||
               content.includes('secret');
      });
    });

    expect(hasSensitiveData).toBeFalsy();
  });

  test('应正确实施速率限制', async ({ page }) => {
    const maxRequests = 10;

    for (let i = 0; i < maxRequests + 5; i++) {
      const response = await page.request.post('/api/login', {
        data: { email: 'test@test.com', password: 'wrong' },
      });

      if (i >= maxRequests) {
        expect(response.status()).toBe(429); // Too Many Requests
      }
    }

    // 验证响应头包含限流信息
    const response = await page.request.post('/api/login');
    const retryAfter = response.headers()['retry-after'];
    expect(retryAfter).toBeTruthy();
  });
});
```

---

## 📊 测试覆盖率标准

### 覆盖率阈值配置

```javascript
// vitest.config.ts
export default defineConfig({
  test: {
    coverage: {
      provider: 'v8', // 或 'istanbul'
      reporter: ['text', 'text-summary', 'html', 'lcov', 'json'],
      reportsDirectory: './coverage',

      // 全局阈值
      thresholds: {
        lines: 80,
        functions: 85,
        branches: 75,
        statements: 80,
      },

      // 按目录配置不同阈值
      thresholdsByFile: {
        'src/utils/**': {
          lines: 100,
          functions: 100,
          branches: 100,
          statements: 100,
        },
        'src/hooks/**': {
          lines: 95,
          functions: 95,
          branches: 90,
          statements: 95,
        },
        'src/components/**': {
          lines: 85,
          functions: 85,
          branches: 75,
          statements: 85,
        },
      },

      // 排除文件
      exclude: [
        'src/**/*.d.ts',
        'src/**/*.test.{ts,tsx}',
        'src/**/*.spec.{ts,tsx}',
        'src/mocks/**',
        'src/types/**',
        'src/config/**',
        'node_modules/**',
      ],

      // 其他配置
      all: true, // 包含未测试文件
      watermarks: {
        statements: [70, 90],
        branches: [65, 85],
        functions: [75, 95],
        lines: [70, 90],
      },
    },
  },
});
```

### 覆盖率报告解读

```
┌─────────────────────────────────────────────────────────────┐
│                    覆盖率报告示例                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  % Coverage report:                                         │
│  --------------------------- ------- -------- -------- ------│
│  File                        % Stmts % Branch % Funcs % Lines │
│  --------------------------- ------- -------- -------- ------│
│  All files                      82.3    76.4    84.2   82.3  │
│  src/utils/format.ts           100      100     100    100   │
│  src/hooks/useAuth.ts           92.5    88.3    94.1   92.5  │
│  src/components/Button.tsx      87.3    72.1    89.5   87.3  │
│  src/api/projects.ts           78.6    68.2    81.4   78.6  │
│  src/pages/Dashboard.tsx        71.2    62.5    74.8   71.2  │
│  --------------------------- ------- -------- -------- ------│
│                                                             │
│  🎯 评级标准：                                               │
│  ✓ 优秀: > 90% (绿色)                                      │
│  ✓ 良好: 80-90% (黄色)                                     │
│  ⚠ 合格: 70-80% (橙色)                                     │
│  ✗ 不合格: < 70% (红色)                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚙️ 测试框架配置

### Vitest完整配置

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],

  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },

  test: {
    globals: true,
    environment: 'jsdom', // 或 'node' for API tests

    // 测试文件匹配模式
    include: [
      'src/**/*.{test,spec}.{ts,tsx}',
      'e2e/**/*.{test,spec}.ts',
    ],

    exclude: [
      'node_modules',
      'dist',
      '.next',
      'coverage',
    ],

    // 设置文件
    setupFiles: ['./src/test/setup.ts'],

    // 全局设置文件
    globalSetup: './src/test/global-setup.ts',

    // CSS Modules支持
    css: {
      modules: {
        classNameStrategy: 'non-scoped',
      },
    },

    // 超时配置
    testTimeout: 10000,
    hookTimeout: 10000,

    // 并行配置
    pool: 'threads',
    poolOptions: {
      threads: {
        singleThread: false,
        minThreads: 2,
        maxThreads: 4,
        isolate: true,
      },
    },

    // 报告器
    reporters: ['verbose', 'json', 'html'],

    // 输出目录
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov', 'html'],
    },
  },
});
```

### 测试工具函数

```typescript
// src/test/setup.ts
import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Mock浏览器API
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock IntersectionObserver
globalThis.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// Mock ResizeObserver
globalThis.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// Mock next/router
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
    pathname: '/',
    query: {},
  }),
  usePathname: () => '/',
  useSearchParams: () => new URLSearchParams(),
}));

// Mock next/image
vi.mock('next/image', () => ({
  __esModule: true,
  default: (props: any) => {
    // eslint-disable-next-line @next/next/no-img-element
    return <img {...props} />;
  },
}));
```

---

## ✅ 验收标准体系

### 总体验收标准

| 标准编号 | 验收项                        | 目标值       | 优先级 | 是否通过 | 实际值   |
| -------- | ----------------------------- | ------------ | ------ | -------- | -------- |
| TEST-01  | 单元测试语句覆盖率            | > 80%        | P0     | □        | XX%      |
| TEST-02  | 单元测试分支覆盖率            | > 75%        | P0     | □        | XX%      |
| TEST-03  | 单元测试函数覆盖率            | > 85%        | P0     | □        | XX%      |
| TEST-04  | 组件测试覆盖率                | > 85%        | P0     | □        | XX%      |
| TEST-05  | 集成测试覆盖率                | > 70%        | P1     | □        | XX%      |
| TEST-06  | E2E测试关键流程覆盖率         | 100%         | P0     | □        | XX%      |
| TEST-07  | 测试通过率                    | > 98%        | P0     | □        | XX%      |
| TEST-08  | Flaky Test比例                | < 2%         | P1     | □        | XX%      |
| TEST-09  | 性能测试通过率                | 100%         | P0     | □        | XX%      |
| TEST-10  | 安全测试高危漏洞数            | 0            | P0     | □        | X        |

### 分级验收准则

#### 🔴 P0 - 必须通过（Blocking）

以下任一条件不满足即**阻断发布**：

- [ ] 单元测试覆盖率达标（语句>80%、分支>75%、函数>85%）
- [ ] 关键业务流程E2E测试100%通过
- [ ] 测试整体通过率 > 98%
- [ ] 无Flaky测试（或<1%且已标记）
- [ ] 性能测试Core Web Vitals达标
- [ ] 安全扫描无高危/严重漏洞

#### 🟡 P1 - 强烈建议通过（Warning）

以下条件不满足将**降低质量评级**：

- [ ] 集成测试覆盖率 > 70%
- [ ] 组件测试交互场景覆盖率 > 90%
- [ ] 测试代码质量和可维护性良好
- [ ] 测试执行效率合理（全量<20min）
- [ ] 测试文档完整（README、注释）

#### 🟢 P2 - 建议优化（Optional）

以下条件满足将**提升至优秀级别**：

- [ ] 覆盖率优于目标值10%以上
- [ ] 具备完整的视觉回归测试
- [ ] 混沌工程/故障注入测试完善
- [ ] 测试数据管理自动化（工厂模式）
- [ ] 测试报告可视化仪表板

### 验收决策矩阵

```
┌─────────────────┬─────────────────────────────────────────┐
│  P0 通过？      │  结果                                   │
├─────────────────┼─────────────────────────────────────────┤
│  ❌ 不通过      │  🚫 阻断发布                            │
│                 │  → 补充测试用例至达标                   │
│                 │  → 修复失败的测试                       │
├─────────────────┼─────────────────────────────────────────┤
│  ✅ 通过        │                                         │
│  ├─ 覆盖率≥90% │  🌟 优秀：测试质量卓越                  │
│  ├─ 覆盖率≥85% │  ✅ 良好：可以发布                      │
│  ├─ 覆盖率≥80% │  ⚠️ 合格：有改进空间                    │
│  └─ 覆盖率<80% │  ❌ 不达标：需补充测试                   │
└─────────────────┴─────────────────────────────────────────┘
```

---

## 📋 输出报告模板

### 测试验收报告结构

```markdown
# YYC³ 测试用例审核验收报告

## 📋 报告概要

| 属性           | 值                                      |
| -------------- | --------------------------------------- |
| **报告编号**   | RPT-TEST-{YYYYMMDD}-{SEQUENCE}          |
| **项目名称**   | {PROJECT_NAME}                          |
| **报告日期**   | {YYYY-MM-DD HH:MM}                      |
| **验收阶段**   | 第三类：测试用例审核验收                 |
| **测试负责人** | {TEST_LEADER_NAME}                      |
| **Git Commit** | {COMMIT_HASH}                           |
| **测试环境**   | Node {VERSION}, Chrome {VERSION}        |

---

## 📊 测试总览

| 维度           | 用例总数 | 通过数 | 失败数 | 跳过数 | 通过率 | 执行耗时 |
| -------------- | -------- | ------ | ------ | ------ | ------ | -------- |
| **单元测试**   | XXX      | XXX    | X      | X      | XX.X%  | XXs      |
| **组件测试**   | XXX      | XXX    | X      | X      | XX.X%  | XXs      |
| **集成测试**   | XXX      | XXX    | X      | X      | XX.X%  | XXs      |
| **E2E测试**    | XX       | XX     | X      | 0      | XX.X%  | XXs      |
| **性能测试**   | XX       | XX     | 0      | 0      | 100%   | XXs      |
| **安全测试**   | XX       | XX     | 0      | 0      | 100%   | XXs      |
| **总计**       | XXXX     | XXXX   | XX     | XX     | XX.X%  | XXmXXs   |

---

## 📈 覆盖率详情

### 1. 整体覆盖率

| 指标         | 当前值   | 目标值   | 状态   | 差距     |
| ------------ | -------- | -------- | ------ | -------- |
| Statements   | XX.X%    | 80%      | ✅/❌  | ±XX.X%   |
| Branches     | XX.X%    | 75%      | ✅/❌  | ±XX.X%   |
| Functions    | XX.X%    | 85%      | ✅/❌  | ±XX.X%   |
| Lines        | XX.X%    | 80%      | ✅/❌  | ±XX.X%   |

### 2. 模块覆盖率明细

| 模块路径                    | 语句%  | 分支%  | 函数%  | 行%    | 状态   |
| --------------------------- | ------ | ------ | ------ | ------ | ------ |
| src/utils/                  | XX.X%  | XX.X%  | XX.X%  | XX.X%  | ✅/❌  |
| src/hooks/                  | XX.X%  | XX.X%  | XX.X%  | XX.X%  | ✅/❌  |
| src/components/             | XX.X%  | XX.X%  | XX.X%  | XX.X%  | ✅/❌  |
| src/api/                    | XX.X%  | XX.X%  | XX.X%  | XX.X%  | ✅/❌  |
| src/lib/                    | XX.X%  | XX.X%  | XX.X%  | XX.X%  | ✅/❌  |
| src/pages/                  | XX.X%  | XX.X%  | XX.X%  | XX.X%  | ✅/❌  |

### 3. 未覆盖代码分析

#### 低覆盖率文件 TOP 10

| 文件路径                          | 覆盖率 | 未覆盖行数 | 建议               |
| --------------------------------- | ------ | ---------- | ------------------ |
| src/components/ComplexChart.tsx   | XX.X%  | XX         | 拆分为小组件       |
| src/pages/Dashboard.tsx           | XX.X%  | XX         | 提取自定义Hooks     |
| src/helpers/dataTransformer.ts    | XX.X%  | XX         | 增加边界条件测试   |

---

## 🔍 失败用例分析

### 失败用例列表

| 用例ID   | 所属模块 | 用例名称               | 错误信息                     | 严重程度 | 重试次数 | 状态   |
| -------- | -------- | ---------------------- | ---------------------------- | -------- | -------- | ------ |
| TC-001   | Unit     | should handle null input | Expected null but got undefined | High   | 3       | 🔧修复中|
| TC-002   | E2E      | should submit form      | Timeout waiting for element  | Medium  | 2       | 📝待分析|

### 失败原因分类

| 失败原因分类       | 数量   | 占比   | 主要原因说明                 |
| ------------------ | ------ | ------ | ---------------------------- |
| 代码Bug            | X      | XX%    | 功能实现与预期不符           |
| 测试代码问题       | X      | XX%    | 测试用例本身编写错误         |
| 环境问题           | X      | XX%    | 依赖服务不可用/数据不一致    |
| Flaky Test         | X      | XX%    | 时序问题/竞态条件            |
| 数据问题           | X      | XX%    | 测试数据缺失或脏数据         |

### 修复计划

| 用例ID   | 问题根因 | 修复方案                   | 负责人 | 截止日期 | 状态   |
| -------- | -------- | -------------------------- | ------ | -------- | ------ |
| TC-001   | 边界条件遗漏 | 增加null check测试       | 张三   | 2026-05-27 | 进行中 |
| TC-002   | 元素等待不足 | 增加显式等待和重试逻辑   | 李四   | 2026-05-28 | 待开始 |

---

## ⚡ 性能测试结果

### Core Web Vitals

| 指标名称                | 当前值   | 目标值   | 状态   | 页面               |
| ----------------------- | -------- | -------- | ------ | ------------------ |
| First Contentful Paint | XXXXms   | < 1800ms | ✅/❌  | / (首页)           |
| Largest Contentful Paint| XXXXms  | < 2500ms | ✅/❌  | /dashboard         |
| Time to Interactive    | XXXXms   | < 3800ms | ✅/❌  | /projects          |
| Cumulative Layout Shift| X.XX     | < 0.1    | ✅/❌  | All Pages          |
| First Input Delay      | XXXms    | < 100ms  | ✅/❌  | Interactive Pages  |

### API性能

| API端点                    | P50    | P95    | P99    | QPS    | 状态   |
| -------------------------- | ------ | ------ | ------ | ------ | ------ |
| GET /api/files             | XXms   | XXXms  | XXXms  | XXX    | ✅/❌  |
| POST /api/auth/login       | XXms   | XXXms  | XXXms  | XXX    | ✅/❌  |
| POST /ai/chat              | XXXms  | XXXXms | XXXXms | XX     | ✅/❌  |

---

## 🔒 安全测试结果

### OWASP Top 10检查结果

| 漏洞类别               | 发现数 | 严重程度 | 状态   | 备注               |
| ---------------------- | ------ | -------- | ------ | ------------------ |
| Injection (注入攻击)   | 0      | -        | ✅     | 无SQL/NoSQL注入     |
| Broken Auth (身份失效) | 0      | -        | ✅     | Token刷新正常        |
| Sensitive Data Exposure | 0     | -        | ✅     | 加密存储正常         |
| XSS                     | 0      | -        | ✅     | 输出编码正确         |
| Broken Access Control   | 1      | Medium   | ⚠️     | 权限边界case待修复   |
| Security Misconfig      | 0      | -        | ✅     | Headers配置正确      |
| CSRF                    | 0      | -        | ✅     | Token验证正常        |
| Using Components w/KV   | 0      | -        | ✅     | 依赖无已知漏洞       |
| ...                     | ...    | ...      | ...    | ...                |

---

## ✅ 验收结论

### 决策结果

- **综合得分**: XX/100
- **评级**: 优秀 / 良好 / 合格 / 不合格
- **决策**: ✅ 准予发布 / ⚠️ 有条件发布 / 🚫 不通过

### 通过条件确认

- [ ] 所有P0覆盖率指标达标
- [ ] E2E关键流程100%通过
- [ ] 测试通过率 > 98%
- [ ] 性能指标符合Core Web Vitals
- [ ] 无高危安全漏洞

### 质量提升建议

1. **短期优化（1周内）**:
   - 补充低覆盖率模块的测试用例
   - 修复所有失败的测试用例
   - 优化Flaky Test，提高稳定性

2. **中期改进（1月内）**:
   - 引入视觉回归测试（Chromatic/Percy）
   - 增加混沌工程测试场景
   - 完善测试数据工厂和数据清理机制

3. **长期规划（季度计划）**:
   - 建设测试效能平台（测试用例管理、执行调度、报告展示）
   - 引入AI辅助测试用例生成
   - 实现测试左移，在需求阶段即开始测试设计

---

## 📝 签字确认

| 角色           | 姓名   | 日期       | 意见   |
| -------------- | ------ | ---------- | ------ |
| 测试负责人     |        | YYYY-MM-DD |        |
| 开发负责人     |        | YYYY-MM-DD |        |
| QA经理         |        | YYYY-MM-DD |        |
| 技术负责人     |        | YYYY-MM-DD |        |

---

**报告生成时间**: {YYYY-MM-DD HH:MM:SS}
**报告有效期**: 至下一版本发布
**下次复验建议**: {YYYY-MM-DD}
```

---

## 🔄 闭环验证机制

### 持续集成流程

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main]

jobs:
  unit-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'pnpm'

      - run: pnpm install
      - run: pnpm test:unit -- --coverage

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/lcov.info

  component-test:
    needs: unit-test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pnpm install
      - run: pnpm test:component

  integration-test:
    needs: unit-test
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd "pg_isready"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - run: pnpm install
      - run: pnpm test:integration
        env:
          DATABASE_URL: postgresql://postgres:test@localhost:5432/testdb

  e2e-test:
    needs: [component-test, integration-test]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
      - uses: actions/setup-node@v4
        with:
          node-version: 20

      - run: pnpm install
      - run: ppm install -D @playwright/test
      - npx playwright install --with-deps
      - npx playwright test
      - uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: playwright-report/
```

---

## 📚 附录

### A. 测试最佳实践

1. **AAA原则**: Arrange（准备）→ Act（执行）→ Assert（断言）
2. **单一职责**: 每个测试只验证一个行为
3. **命名规范**: `should [expected behavior] when [condition/context]`
4. **独立性**: 测试间无依赖，可任意顺序执行
5. **快速反馈**: 单元测试 < 100ms，集成测试 < 1s
6. **有意义的数据**: 使用真实场景数据，避免 magic numbers
7. **避免实现细节**: 测试行为而非实现

### B. 相关文档索引

- [YYC3-功能逻辑-验收标准.md](./YYC3-功能逻辑-验收标准.md) - 前置阶段
- [YYC3-组件测试-验收标准.md](./YYC3-组件测试-验收标准.md) - 后续阶段
- [YYC3-单元框架-审核验收.md](./YYC3-单元框架-审核验收.md) - 框架搭建指南

### C. 版本历史

| 版本   | 日期       | 变更内容                       | 作者                |
| ------ | ---------- | -------------------------------- | ------------------- |
| v1.0.0 | 2026-05-25 | 初始版本，建立测试用例审核标准 | YanYuCloudCube Team |

---

<div align="center">

**© 2026 YanYuCloudCube Team**
**言启象限 | 语枢未来**
**Words Initiate Quadrants, Language Serves as Core for Future**

</div>
