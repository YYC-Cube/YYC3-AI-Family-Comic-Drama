---
file: YYC3-组件测试-验收标准.md
description: YYC³ 项目闭环验收系统 — React组件测试与交互验证标准（第四类验收阶段）
author: YanYuCloudCube Team <admin@0379.email>
version: v2.0.0
created: 2026-05-25
updated: 2026-05-30
status: stable
tags: [验收],[组件测试],[React],[RTL],[交互测试],[无障碍],[闭环]
category: acceptance
language: zh-CN
audience: developers,frontend-engineers,qa-engineers
complexity: advanced
---

<div align="center">

# YYC³（YanYuCloudCube）闭环验收系统

## 第四类：组件测试验收标准

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
| **验收阶段** | 第四阶段：组件测试类                     |
| **验收性质** | 组件质量保障 · 交互正确性验证          |
| **适用范围** | React + TypeScript + RTL + userEvent |

</div>

---

## 📋 目录

- [🎯 验收目标与定位](#-验收目标与定位)
- [📐 五维评估框架](#-五维评估框架)
- [🧩 组件分类体系](#-组件分类体系)
- [✅ 测试场景矩阵](#-测试场景矩阵)
- [⚙️ 测试工具链配置](#️-测试工具链配置)
- [🎨 样式与视觉回归](#-样式与视觉回归)
- [♿ 无障碍测试标准](#-无障碍测试标准)
- [✅ 验收标准体系](#-验收标准体系)
- [📋 输出报告模板](#-输出报告模板)
- [🔄 闭环验证机制](#-闭环验证机制)

---

## 🎯 验收目标与定位

### 核心使命

作为YYC³闭环验收系统的**前端质量核心**，组件测试验收承担着确保所有UI组件渲染正确、交互可靠、状态管理准确、无障碍合规的关键职责。本阶段聚焦于从原子到复合的全层级组件测试覆盖。

### 战略定位

```
┌─────────────────────────────────────────────────────────────┐
│              闭环验收系统流水线                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  第一类：代码语法测试核验 ✅                                  │
│  第二类：功能逻辑验收标准 ✅                                  │
│  第三类：测试用例审核验收 ✅                                  │
│       ↓ 已通过                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  ⭐ 第四类：组件测试验收标准（当前阶段）               │   │
│  │  ├── 基础组件覆盖率 > 95%                            │   │
│  │  ├── 业务组件覆盖率 > 90%                            │   │
│  │  ├── 页面组件覆盖率 > 85%                            │   │
│  │  └── 无障碍合规率 > 98%                              │   │
│  └─────────────────────────────────────────────────────┘   │
│                          ↓                                  │
│  第五类：单元框架审核验收                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 核心价值主张

| 维度       | 价值主张                                   | 实现方式                              |
| ---------- | ------------------------------------------ | ------------------------------------- |
| **时间维** | 快速组件级反馈，问题精准定位                | 热更新测试，变更文件自动关联，<2s响应 |
| **空间维** | 全量组件覆盖，无遗漏盲区                    | 原子→分子→有机体→模板→页面全覆盖     |
| **属性维** | 渲染可预测、交互可验证、状态可追溯          | 快照测试、行为测试、状态机验证        |
| **事件维** | 用户操作完整模拟，边界条件充分覆盖           | userEvent真实模拟，异常流程完整测试   |
| **关联维** | 组件间通信清晰，Props/Context依赖明确        | Mock隔离，依赖注入，接口契约测试      |

---

## 📐 五维评估框架

### 时间维度评估

#### 度量指标

| 指标名称              | 目标值    | 测量方法                    | 优先级 |
| --------------------- | --------- | --------------------------- | ------ |
| 单个组件测试执行时间  | < 100ms   | Vitest + @testing-library  | P0     |
| 组件测试套件总耗时    | < 120s    | 并行执行统计                | P0     |
| 快照测试对比耗时      | < 5s      | Jest snapshot diff         | P1     |
| 视觉回归测试耗时      | < 60s     | Percy/Chromatic            | P2     |
| PR增量组件测试响应    | < 30s     | CI/CD Pipeline             | P0     |

### 空间维度评估

#### 组件层次结构

```
┌─────────────────────────────────────────────────────────────┐
│                  组件测试金字塔                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Layer 5: 页面组件 (Page Components)                        │
│  ├── 覆盖率目标: > 85%                                      │
│  ├── 测试重点: 路由集成、数据加载、布局组合                 │
│  └── 示例: Dashboard, ProjectDetail, Settings               │
│                                                             │
│  Layer 4: 模板组件 (Template Components)                    │
│  ├── 覆盖率目标: > 88%                                      │
│  ├── 测试重点: 布局结构、插槽内容、容器逻辑                 │
│  └── 示例: PageLayout, CardContainer, ModalWrapper          │
│                                                             │
│  Layer 3: 有机体组件 (Organism Components)                  │
│  ├── 覆盖率目标: > 90%                                      │
│  ├── 测试重点: 多组件协作、复杂交互、状态管理               │
│  └── 示例: UserCard, FileUploader, ChatPanel                │
│                                                             │
│  Layer 2: 分子组件 (Molecule Components)                    │
│  ├── 覆盖率目标: > 93%                                      │
│  ├── 测试重点: 组合原子、简单交互、事件传递                 │
│  └── 示例: FormField, ButtonGroup, SearchInput              │
│                                                             │
│  Layer 1: 原子组件 (Atom Components)                        │
│  ├── 覆盖率目标: > 98%                                      │
│  ├── 测试重点: Props渲染、样式应用、基础交互                 │
│  └── 示例: Button, Input, Icon, Badge                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 覆盖率分布矩阵

```
┌──────────────────┬────────┬────────┬────────┬────────┬────────┐
│   组件类型       │  数量  │ 覆盖率  │ 通过率 │ 平均耗时│ 优先级 │
├──────────────────┼────────┼────────┼────────┼────────┼────────┤
│  原子组件 (Atoms)│  ≥50   │ > 98%  │ > 99%  │  <20ms │  P0    │
│  分子组件 (Molecules)│≥30 │ > 93%  │ > 97%  │  <50ms │  P0    │
│  有机体 (Organisms)│ ≥20  │ > 90%  │ > 95%  │  <100ms│  P0    │
│  模板 (Templates) │  ≥10  │ > 88%  │ > 92%  │  <150ms│  P1    │
│  页面 (Pages)     │  ≥15  │ > 85%  │ > 90%  │  <200ms│  P1    │
└──────────────────┴────────┴────────┴────────┴────────┴────────┘
```

### 属性维度评估

#### 质量属性指标

| 属性类别       | 具体指标                   | 目标值   | 权重   | 测量方法                      |
| -------------- | -------------------------- | -------- | ------ | ----------------------------- |
| **渲染正确性**  | 正常状态渲染通过率          | 100%     | 15%    | render() + screen queries     |
|                | 边界条件渲染通过率          | > 98%    | 10%    | edge case testing              |
|                | 错误状态渲染通过率          | 100%     | 10%    | error boundary testing         |
| **交互可靠性**  | 用户事件处理正确率          | > 99%    | 15%    | userEvent simulation           |
|                | 表单提交成功率              | > 99%    | 10%    | form submission testing        |
|                | 异步操作完成率              | > 98%    | 10%    | waitFor + async testing        |
| **状态一致性**  | Props变化响应正确率         | 100%     | 10%    | rerender on props change       |
|                | Context消费正确率           | > 98%    | 5%     | context provider testing       |
|                | State转换正确率             | > 97%    | 5%     | state machine testing          |
| **可访问性**    | ARIA属性完整性              | 100%     | 10%    | axe-core / jest-axe            |
|                | 键盘导航可用性              | 100%     | 5%     | keyboard navigation test       |
|                | 屏幕阅读器兼容性            | > 98%    | 5%     | role/label testing             |

### 事件维度评估

#### 用户交互事件矩阵

| 事件类别       | 触发方式                   | 测试要点                     | 必须覆盖的场景           | 优先级 |
| -------------- | -------------------------- | ---------------------------- | ------------------------ | ------ |
| **点击事件**   | click, doubleClick         | 回调触发、防重复、禁用态     | 正常点击、快速双击、禁用 | P0     |
| **输入事件**   | change, input, focus       | 值更新、校验、格式化         | 正常输入、清空、粘贴     | P0     |
| **键盘事件**   | keyDown, keyUp, keyPress   | 快捷键、Tab导航、Enter提交   | Enter、Escape、Tab顺序   | P0     |
| **表单事件**   | submit, reset, invalid     | 提交逻辑、重置、校验错误     | 成功提交、校验失败、重置 | P0     |
| **拖拽事件**   | dragStart, dragEnd, drop   | 拖拽排序、文件拖入           | 开始拖拽、悬停、放置     | P1     |
| **滚动事件**   | scroll, wheel              | 无限加载、吸顶效果           | 到底部、向上滚动         | P1     |
| **触摸事件**   | touchStart, touchEnd       | 手势识别、移动端交互         | 点击、长按、滑动         | P2     |
| **焦点事件**   | focus, blur, focusIn       | 焦点陷阱、自动聚焦           | 获焦、失焦、焦点恢复     | P1     |

### 关联维度评估

#### 组件依赖关系图

```
┌─────────────────────────────────────────────────────────────┐
│                  组件依赖关系矩阵                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  原子层 (Atoms)                                              │
│  ├── 无外部组件依赖                                         │
│  ├── 仅依赖 UI 库 (Radix, shadcn)                          │
│  └── 可独立测试                                             │
│                                                             │
│  分子层 (Molecules)                                          │
│  ├── 组合多个原子组件                                       │
│  ├── 内部状态管理                                           │
│  └── Mock 子组件进行测试                                    │
│                                                             │
│  有机体层 (Organisms)                                        │
│  ├── 组合分子和原子                                         │
│  ├── 依赖 Context/Hooks                                     │
│  └── 需要 Provider 包装                                     │
│                                                             │
│  模板层 & 页面层                                             │
│  ├── 完整页面布局                                           │
│  ├── 依赖路由和数据获取                                     │
│  └── 需要 MSW + Router Mock                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧩 组件分类体系

### 1. 原子组件 (Atoms)

#### 1.1 Button组件测试

```tsx
// src/components/ui/Button/__tests__/Button.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Button } from '../Button';

describe('Button 组件', () => {
  const user = userEvent.setup();

  it('应正确渲染文本内容', () => {
    render(<Button>Click me</Button>);

    expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument();
  });

  it('应在点击时调用 onClick 回调', async () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click me</Button>);

    await user.click(screen.getByRole('button'));

    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('应支持不同变体样式', () => {
    const { rerender } = render(<Button variant="default">Default</Button>);
    expect(screen.getByRole('button')).toHaveClass('bg-primary');

    rerender(<Button variant="destructive">Destructive</Button>);
    expect(screen.getByRole('button')).toHaveClass('bg-destructive');

    rerender(<Button variant="outline">Outline</Button>);
    expect(screen.getByRole('button')).toHaveClass('border-input');
  });

  it('应支持不同尺寸', () => {
    const { rerender } = render(<Button size="default">Default</Button>);
    expect(screen.getByRole('button')).toHaveClass('h-10');

    rerender(<Button size="sm">Small</Button>);
    expect(screen.getByRole('button')).toHaveClass('h-9');

    rerender(<Button size="lg">Large</Button>);
    expect(screen.getByRole('button')).toHaveClass('h-11');

    rerender(<Button size="icon">Icon</Button>);
    expect(screen.getByRole('button')).toHaveClass('h-10 w-10');
  });

  it('禁用状态下不应触发点击', async () => {
    const handleClick = jest.fn();
    render(<Button disabled onClick={handleClick}>Disabled</Button>);

    await user.click(screen.getByRole('button'));

    expect(handleClick).not.toHaveBeenCalled();
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('加载状态下应显示 Spinner 并禁用点击', async () => {
    const handleClick = jest.fn();
    render(<Button isLoading onClick={handleClick}>Loading</Button>);

    expect(screen.getByTestId('spinner')).toBeInTheDocument();
    await user.click(screen.getByRole('button'));
    expect(handleClick).not.toHaveBeenCalled();
  });

  it('作为链接时应渲染为 <a> 标签', () => {
    render(<Button asChild><a href="/test">Link</a></Button>);

    expect(screen.getByRole('link')).toHaveAttribute('href', '/test');
  });
});
```

#### 1.2 Input组件测试

```tsx
// src/components/ui/Input/__tests__/Input.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Input } from '../Input';

describe('Input 组件', () => {
  const user = userEvent.setup();

  it('应正确渲染并接受用户输入', async () => {
    const handleChange = jest.fn();
    render(<Input onChange={handleChange} placeholder="Enter text" />);

    const input = screen.getByPlaceholderText('Enter text');
    await user.type(input, 'Hello World');

    expect(input).toHaveValue('Hello World');
    expect(handleChange).toHaveBeenCalled();
  });

  it('应支持受控模式', async () => {
    const { rerender } = render(<Input value="" readOnly />);

    const input = screen.getByRole('textbox');
    expect(input).toHaveValue('');

    rerender(<Input value="Controlled" readOnly />);
    expect(input).toHaveValue('Controlled');
  });

  it('应显示错误状态', () => {
    render(<Input error="This field is required" />);

    expect(screen.getByRole('alert')).toHaveTextContent('This field is required');
    expect(screen.getByRole('textbox')).toHaveAttribute('aria-invalid', 'true');
  });

  it('应支持不同类型', () => {
    const { rerender } = render(<Input type="text" />);
    expect(screen.getByRole('textbox')).toHaveAttribute('type', 'text');

    rerender(<Input type="password" />);
    expect(screen.getByLabelText(/password/i)).toHaveAttribute('type', 'password');

    rerender(<Input type="email" />);
    expect(screen.getByRole('textbox')).toHaveAttribute('type', 'email');
  });

  it('应支持前缀和后缀图标', () => {
    render(
      <Input
        prefix={<span data-testid="prefix">🔍</span>}
        suffix={<span data-testid="suffix">✓</span>}
      />
    );

    expect(screen.getByTestId('prefix')).toBeInTheDocument();
    expect(screen.getByTestId('suffix')).toBeInTheDocument();
  });

  it('清除按钮应能清空输入', async () => {
    const onClear = jest.fn();
    render(<Input defaultValue="text" clearable onClear={onClear} />);

    await user.click(screen.getByTestId('clear-button'));

    expect(screen.getByRole('textbox')).toHaveValue('');
    expect(onClear).toHaveBeenCalledTimes(1);
  });
});
```

### 2. 分子组件 (Molecules)

#### 2.1 FormField组件测试

```tsx
// src/components/ui/FormField/__tests__/FormField.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FormField } from '../FormField';

describe('FormField 组件', () => {
  const user = userEvent.setup();

  it('应正确渲染标签和输入框', () => {
    render(
      <FormField label="Username" name="username">
        <input data-testid="input" />
      </FormField>
    );

    expect(screen.getByText('Username')).toBeInTheDocument();
    expect(screen.getByTestId('input')).toBeInTheDocument();
    expect(screen.getByLabelText('Username')).toBeVisible();
  });

  it('必填字段应显示星号标记', () => {
    render(
      <FormField label="Email" name="email" required>
        <input data-testid="input" />
      </FormField>
    );

    expect(screen.getByText('*')).toBeInTheDocument();
    expect(screen.getByTestId('input')).toBeRequired();
  });

  it('应显示帮助文本', () => {
    render(
      <FormField label="Password" name="password" helperText="至少8个字符">
        <input data-testid="input" />
      </FormField>
    );

    expect(screen.getByText('至少8个字符')).toBeInTheDocument();
  });

  it('应显示错误信息', () => {
    render(
      <FormField
        label="Email"
        name="email"
        error="请输入有效的邮箱地址"
      >
        <input data-testid="input" />
      </FormField>
    );

    expect(screen.getByText('请输入有效的邮箱地址')).toBeInTheDocument();
    expect(screen.getByRole('alert')).toBeInTheDocument();
  });

  it('标签应为 input 的关联标签', () => {
    render(
      <FormField label="Search" name="search">
        <input data-testid="input" />
      </FormField>
    );

    const label = screen.getByText('Search');
    const input = screen.getByTestId('input');

    expect(label).toHaveAttribute('for', input.id);
    expect(input).toHaveAttribute('id');
  });
});
```

#### 2.2 Modal对话框组件测试

```tsx
// src/components/ui/Modal/__tests__/Modal.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Modal } from '../Modal';

describe('Modal 组件', () => {
  const user = userEvent.setup();

  beforeEach(() => {
    // 创建 portal container
    const modalRoot = document.createElement('div');
    modalRoot.setAttribute('id', 'modal-root');
    document.body.appendChild(modalRoot);
  });

  afterEach(() => {
    const modalRoot = document.getElementById('modal-root');
    if (modalRoot) document.body.removeChild(modalRoot);
  });

  it('打开时应显示内容', () => {
    render(
      <Modal isOpen onClose={jest.fn()} title="Test Modal">
        <p>Modal content</p>
      </Modal>
    );

    expect(screen.getByText('Test Modal')).toBeInTheDocument();
    expect(screen.getByText('Modal content')).toBeInTheDocument();
  });

  it('关闭时不应显示', () => {
    const { rerender } = render(
      <Modal isOpen={true} onClose={jest.fn()} title="Test Modal">
        <p>Content</p>
      </Modal>
    );

    expect(screen.getByText('Test Modal')).toBeInTheDocument();

    rerender(
      <Modal isOpen={false} onClose={jest.fn()} title="Test Modal">
        <p>Content</p>
      </Modal>
    );

    expect(screen.queryByText('Test Modal')).not.toBeInTheDocument();
  });

  it('点击遮罩层应调用 onClose', async () => {
    const handleClose = jest.fn();
    render(
      <Modal isOpen onClose={handleClose} title="Test Modal">
        <p>Content</p>
      </Modal>
    );

    // 点击 overlay
    const overlay = screen.getByTestId('modal-overlay');
    await user.click(overlay);

    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it('按 Escape 键应关闭', async () => {
    const handleClose = jest.fn();
    render(
      <Modal isOpen onClose={handleClose} title="Test Modal">
        <p>Content</p>
      </Modal>
    );

    fireEvent.keyDown(document, { key: 'Escape' });

    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it('打开时应聚焦到第一个可交互元素', () => {
    render(
      <Modal isOpen onClose={jest.fn()} title="Confirm Action">
        <button>Cancel</button>
        <button data-testid="confirm-btn">Confirm</button>
      </Modal>
    );

    // 第一个按钮应该获得焦点
    expect(screen.getByText('Cancel')).toHaveFocus();
  });

  it('关闭时应恢复之前的焦点', async () => {
    const handleClose = jest.fn();

    render(
      <>
        <button data-testid="outside-btn">Outside</button>
        <Modal isOpen onClose={handleClose} title="Test">
          <p>Content</p>
        </Modal>
      </>
    );

    // 先让外部按钮获得焦点
    await user.click(screen.getByTestId('outside-btn'));
    expect(screen.getByTestId('outside-btn')).toHaveFocus();

    // 关闭 modal
    act(() => {
      handleClose();
    });

    // 焦点应该回到外部按钮
    expect(screen.getByTestId('outside-btn')).toHaveFocus();
  });
});
```

### 3. 有机体组件 (Organisms)

#### 3.1 用户卡片组件测试

```tsx
// src/components/UserCard/__tests__/UserCard.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { UserCard } from '../UserCard';

const mockUser = {
  id: '1',
  name: '张三',
  email: 'zhangsan@example.com',
  avatar: '/avatar.jpg',
  role: 'admin' as const,
  status: 'online' as const,
  lastActiveAt: '2026-05-25T10:00:00Z',
};

describe('UserCard 组件', () => {
  const user = userEvent.setup();

  it('应显示用户基本信息', () => {
    render(<UserCard user={mockUser} />);

    expect(screen.getByText('张三')).toBeInTheDocument();
    expect(screen.getByText('zhangsan@example.com')).toBeInTheDocument();
    expect(screen.getByAltText(`${mockUser.name}的头像`))
      .toHaveAttribute('src', mockUser.avatar);
  });

  it('应显示在线状态指示器', () => {
    render(<UserCard user={mockUser} />);

    const statusIndicator = screen.getByTestId('status-indicator');
    expect(statusIndicator).toHaveClass('bg-green-500');
  });

  it('应显示管理员徽章', () => {
    render(<UserCard user={mockUser} />);

    expect(screen.getByText('管理员')).toBeInTheDocument();
  });

  it('点击应调用 onSelect 回调', async () => {
    const handleSelect = jest.fn();
    render(<UserCard user={mockUser} onSelect={handleSelect} />);

    await user.click(screen.getByRole('button'));

    expect(handleSelect).toHaveBeenCalledWith(mockUser);
  });

  it('悬浮应显示最后活跃时间', async () => {
    render(<UserCard user={mockUser} />);

    await user.hover(screen.getByRole('button'));

    await waitFor(() => {
      expect(screen.getByText(/最后活跃/i)).toBeInTheDocument();
    });
  });

  it('加载状态应显示 Skeleton', () => {
    render(<UserCard isLoading />);

    expect(screen.getAllByTestId('skeleton')).toHaveLength(4);
  });

  it('错误状态应显示错误信息', () => {
    render(<UserCard error="用户数据加载失败" />);

    expect(screen.getByText('用户数据加载失败')).toBeInTheDocument();
    expect(screen.getByRole('alert')).toBeInTheDocument();
  });
});
```

#### 3.2 文件上传组件测试

```tsx
// src/components/FileUploader/__tests__/FileUploader.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FileUploader } from '../FileUploader';

describe('FileUploader 组件', () => {
  const user = userEvent.setup();

  const defaultProps = {
    onUpload: jest.fn(),
    maxSize: 10 * 1024 * 1024, // 10MB
    accept: '.pdf,.doc,.docx,.txt',
    maxFiles: 5,
  };

  it('应显示上传区域', () => {
    render(<FileUploader {...defaultProps} />);

    expect(screen.getByText(/拖拽文件到此处/i)).toBeInTheDocument();
    expect(screen.getByText(/或点击选择/i)).toBeInTheDocument();
  });

  it('点击应触发文件选择', async () => {
    render(<FileUploader {...defaultProps} />);

    const input = screen.getByTestId('file-input');
    const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });

    Object.defineProperty(input, 'files', {
      value: [file],
    });

    fireEvent.change(input);

    await waitFor(() => {
      expect(defaultProps.onUpload).toHaveBeenCalledWith([file]);
    });
  });

  it('应验证文件大小限制', async () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
    render(<FileUploader {...defaultProps} />);

    const input = screen.getByTestId('file-input');
    const largeFile = new File(['x'.repeat(11 * 1024 * 1024)], 'large.pdf', {
      type: 'application/pdf',
    });

    Object.defineProperty(input, 'files', {
      value: [largeFile],
    });

    fireEvent.change(input);

    await waitFor(() => {
      expect(screen.getByText(/文件大小超过限制/i)).toBeInTheDocument();
    });

    consoleSpy.mockRestore();
  });

  it('应验证文件类型', async () => {
    render(<FileUploader {...defaultProps} />);

    const input = screen.getByTestId('file-input');
    const invalidFile = new File(['content'], 'image.png', {
      type: 'image/png',
    });

    Object.defineProperty(input, 'files', {
      value: [invalidFile],
    });

    fireEvent.change(input);

    await waitFor(() => {
      expect(screen.getByText(/不支持的文件类型/i)).toBeInTheDocument();
    });
  });

  it('应显示已上传的文件列表', () => {
    const uploadedFiles = [
      { id: '1', name: 'document.pdf', size: 1024000, status: 'completed' as const },
      { id: '2', name: 'report.docx', size: 2048000, status: 'uploading' as const },
    ];

    render(<FileUploader {...defaultProps} files={uploadedFiles} />);

    expect(screen.getByText('document.pdf')).toBeInTheDocument();
    expect(screen.getByText('report.docx')).toBeInTheDocument();
    expect(screen.getByTestId('progress-bar')).toBeInTheDocument();
  });

  it('应支持删除已上传文件', async () => {
    const handleDelete = jest.fn();
    const files = [{ id: '1', name: 'test.pdf', size: 1024, status: 'completed' as const }];

    render(<FileUploader {...defaultProps} files={files} onDelete={handleDelete} />);

    await user.click(screen.getByTestId('delete-file-1'));

    expect(handleDelete).toHaveBeenCalledWith('1');
  });
});
```

---

## ✅ 测试场景矩阵

### 必测场景清单 (P0 - Must Have)

| 场景编号 | 场景名称               | 测试类型     | 验证点                           | 优先级 |
| -------- | ---------------------- | ------------ | -------------------------------- | ------ |
| CS-001   | 正常渲染               | Render Test  | 元素存在、文本正确、样式应用     | P0     |
| CS-002   | Props传入              | Props Test   | Props正确接收和应用               | P0     |
| CS-003   | 空数据处理             | Edge Case    | undefined/null/空数组处理        | P0     |
| CS-004   | 加载状态               | State Test   | Loading indicator显示             | P0     |
| CS-005   | 错误状态               | Error Test   | Error message显示、Error Boundary | P0     |
| CS-006   | 点击交互               | Event Test   | onClick回调触发、参数正确         | P0     |
| CS-007   | 表单输入               | Form Test   | 值更新、onChange回调、校验        | P0     |
| CS-008   | 禁用状态               | Disabled Test| 不可交互、视觉反馈                | P0     |
| CS-009   | 键盘导航               | A11y Test    | Tab顺序、Enter/Space激活          | P0     |
| CS-010   | ARIA属性               | A11y Test    | role、label、description正确      | P0     |

### 推荐场景清单 (P1 - Should Have)

| 场景编号 | 场景名称               | 测试类型     | 验证点                           | 优先级 |
| -------- | ---------------------- | ------------ | -------------------------------- | ------ |
| CS-011   | 异步数据加载           | Async Test   | loading → success/error 状态流转 | P1     |
| CS-012   | Props变化响应          | Re-render    | 新Props正确渲染、旧状态清理       | P1     |
| CS-013   | 列表渲染               | List Test    | 空列表、单条、多条、超长列表     | P1     |
| CS-014   | 分页功能               | Pagination   | 页码切换、数据刷新               | P1     |
| CS-015   | 搜索过滤               | Filter Test  | 实时搜索、防抖、结果高亮         | P1     |
| CS-016   | 排序功能               | Sort Test    | 升序/降序、多字段排序            | P1     |
| CS-017   | 模态框焦点管理         | Focus Trap   | 打开聚焦、关闭恢复、Tab循环      | P1     |
| CS-018   | Tooltip提示            | Tooltip Test | 悬浮显示、隐藏延迟、位置正确     | P1     |
| CS-019   | 响应式布局             | Responsive   | 断点切换、元素隐藏/显示           | P1     |
| CS-020   | 主题切换               | Theme Test   | 明暗主题、颜色变量应用            | P1     |

### 可选场景清单 (P2 - Nice to Have)

| 场景编号 | 场景名称               | 测试类型     | 验证点                           | 优先级 |
| -------- | ---------------------- | ------------ | -------------------------------- | ------ |
| CS-021   | 动画过渡               | Animation    | 入场/退场动画、时长正确           | P2     |
| CS-022   | 拖拽排序               | DragDrop     | 拖拽开始/结束、位置交换           | P2     |
| CS-023   | 虚拟滚动               | Virtual Scroll| 大数据量渲染性能                | P2     |
| CS-024   | 国际化(i18n)           | i18n Test    | 多语言切换、日期格式化            | P2     |
| CS-025   | 快捷键                 | Shortcut     | Ctrl+S/Ctrl+Z等全局快捷键        | P2     |
| CS-026   | 剪贴板操作             | Clipboard    | 复制/粘贴、格式保留               | P2     |
| CS-027   | 打印优化               | Print Test   | 打印样式、分页符                  | P2     |
| CS-028   | 截图分享               | Screenshot   | html2canvas/dom-to-image          | P2     |

---

## ⚙️ 测试工具链配置

### Vitest + RTL 配置

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
    environment: 'jsdom',

    setupFiles: ['./src/test/setup.ts'],

    include: ['src/**/*.{test,spec}.{ts,tsx}'],

    css: {
      modules: {
        classNameStrategy: 'non-scoped',
      },
    },

    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'lcov'],

      thresholds: {
        statements: 80,
        branches: 75,
        functions: 85,
        lines: 80,
      },

      exclude: [
        'src/**/*.test.{ts,tsx}',
        'src/**/*.spec.{ts,tsx}',
        'src/mocks/**',
        'src/types/**',
        '**/*.d.ts',
      ],
    },
  },
});
```

### 测试工具函数库

```typescript
// src/test/component-test-utils.ts
import { render, RenderOptions } from '@testing-library/react';
import { FC, ReactElement } from 'react';

/**
 * 自定义render函数，自动包装Provider
 */
const AllProviders: FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <ThemeProvider attribute="class" defaultTheme="system">
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    </ThemeProvider>
  );
};

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllProviders, ...options });

export * from '@testing-library/react';
export { customRender as render };
```

---

## 🎨 样式与视觉回归

### CSS-in-JS 测试

```tsx
// src/components/Button/__tests__/Button.styles.test.tsx
import { render, screen } from '@testing-library/react';
import { Button } from '../Button';

describe('Button 样式测试', () => {
  it('默认变体应有正确的背景色', () => {
    render(<Button>Default</Button>);
    const button = screen.getByRole('button');

    expect(button).toHaveClass('bg-primary');
    expect(button).toHaveClass('text-primary-foreground');
    expect(button).toHaveClass('inline-flex');
  });

  it('destructive 变体应有红色背景', () => {
    render(<Button variant="destructive">Delete</Button>);
    const button = screen.getByRole('button');

    expect(button).toHaveClass('bg-destructive');
    expect(button).toHaveClass('text-destructive-foreground');
  });

  it('尺寸变体应有正确的 padding', () => {
    const { rerender } = render(<Button size="sm">Small</Button>);
    let button = screen.getByRole('button');
    expect(button).toHaveClass('h-9 px-3');

    rerender(<Button size="lg">Large</Button>);
    button = screen.getByRole('button');
    expect(button).toHaveClass('h-11 px-8');
  });

  it('全宽模式应占满容器宽度', () => {
    render(<Button fullWidth>Full Width</Button>);

    expect(screen.getByRole('button')).toHaveClass('w-full');
  });
});
```

### 快照测试策略

```tsx
// src/components/Card/__tests__/Card.snapshot.test.tsx
import { render } from '../test-utils';
import { Card } from '../Card';

describe('Card 快照测试', () => {
  it('基本卡片应匹配快照', () => {
    const { asFragment } = render(
      <Card>
        <CardHeader>
          <CardTitle>Card Title</CardTitle>
          <CardDescription>Card description text</CardDescription>
        </CardHeader>
        <CardContent>
          <p>Card content goes here</p>
        </CardContent>
        <CardFooter>
          <Button>Action</Button>
        </CardFooter>
      </Card>
    );

    expect(asFragment()).toMatchSnapshot();
  });

  it('带图片的卡片应匹配快照', () => {
    const { asFragment } = render(
      <Card>
        <img src="/card-image.jpg" alt="Card image" />
        <CardContent>
          <h3>Title</h3>
          <p>Description</p>
        </CardContent>
      </Card>
    );

    expect(asFragment()).toMatchSnapshot();
  });
});
```

---

## ♿ 无障碍测试标准

### axe-core 集成

```tsx
// src/test/accessibility.ts
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

/**
 * 无障碍测试辅助函数
 */
export async function testAccessibility(html: HTMLElement) {
  const results = await axe(html);
  expect(results).toHaveNoViolations();
}
```

### 无障碍测试示例

```tsx
// src/components/Form/__tests__/Form.accessibility.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LoginForm } from '../LoginForm';
import { testAccessibility } from '@/test/accessibility';

describe('LoginForm 无障碍测试', () => {
  const user = userEvent.setup();

  it('应通过axe-core无障碍检查', async () => {
    const { container } = render(<LoginForm />);

    await testAccessibility(container);
  });

  it('所有表单字段都应有正确的label', () => {
    render(<LoginForm />);

    const emailInput = screen.getByLabelText(/邮箱/i);
    const passwordInput = screen.getByLabelText(/密码/i);

    expect(emailInput).toBeInTheDocument();
    expect(passwordInput).toBeInTheDocument();
  });

  it('错误消息应有关联的 aria-live 区域', () => {
    render(<LoginForm onSubmit={jest.fn()} />);

    // 提交空表单以触发验证错误
    const submitButton = screen.getByRole('button', { name: /登录/i });
    user.click(submitButton);

    // 验证错误消息在 alert role 中
    const errorMessage = screen.getByRole('alert');
    expect(errorMessage).toBeInTheDocument();
  });

  it('应支持完整的键盘导航', async () => {
    render(<LoginForm />);

    // Tab 应该按顺序遍历表单字段
    await user.tab();
    expect(screen.getByLabelText(/邮箱/i)).toHaveFocus();

    await user.tab();
    expect(screen.getByLabelText(/密码/i)).toHaveFocus();

    await user.tab();
    expect(screen.getByRole('checkbox')).toHaveFocus(); // 记住我

    await user.tab();
    expect(screen.getByRole('button', { name: /登录/i })).toHaveFocus();
  });

  it('提交按钮应有描述性的 accessible name', () => {
    render(<LoginForm />);

    const submitButton = screen.getByRole('button', { name: /登录/i });
    expect(submitButton).toBeInTheDocument();
  });

  it('密码字段应有切换可见性按钮', () => {
    render(<LoginForm />);

    const passwordInput = screen.getByLabelText(/密码/i);
    const toggleButton = screen.getByLabelText(/显示密码/i); // 或 /隐藏密码/i

    expect(toggleButton).toBeInTheDocument();
  });
});
```

### WCAG 2.1 AA 合规检查清单

| 原则         | 准则                         | 检查项                             | 测试方法           |
| ------------ | ---------------------------- | ---------------------------------- | ------------------ |
| 可感知性     | 1.1.1 非文本内容             | 图片有 alt 文本                    | alt 属性检查       |
|              | 1.3.1 信息与关系             | 表单 label 正确关联                | label/for 检查     |
|              | 1.4.3 对比度（最小）         | 文本对比度 >= 4.5:1               | axe-core 自动检测  |
|              | 1.4.11 非文本对比度           | UI组件对比度 >= 3:1               | axe-core 自动检测  |
| 可操作性     | 2.1.1 键盘                   | 所有功能可通过键盘访问             | Tab 导航测试       |
|              | 2.4.7 焦点可见               | 焦点指示器清晰可见                 | :focus-visible     |
|              | 2.5.3 输入助手的标签          | name 属性有意义                    | name 属性检查      |
| 可理解性     | 3.2.2 输入时的帮助            | 表单字段有帮助文本或说明           | helper text 检查   |
|              | 3.3.1 错误建议               | 错误消息包含修正建议               | error message 检查 |
| 健壮性       | 4.1.2 名称、角色、值          | ARIA 属性正确使用                  | axe-core 自动检测  |

---

## ✅ 验收标准体系

### 总体验收标准

| 标准编号 | 验收项                        | 目标值       | 优先级 | 是否通过 | 实际值   |
| -------- | ----------------------------- | ------------ | ------ | -------- | -------- |
| COMP-01  | 原子组件覆盖率                | > 98%        | P0     | □        | XX%      |
| COMP-02  | 分子组件覆盖率                | > 93%        | P0     | □        | XX%      |
| COMP-03  | 有机体组件覆盖率              | > 90%        | P0     | □        | XX%      |
| COMP-04  | 模板组件覆盖率                | > 88%        | P1     | □        | XX%      |
| COMP-05  | 页面组件覆盖率                | > 85%        | P1     | □        | XX%      |
| COMP-06  | 交互测试通过率                | > 99%        | P0     | □        | XX%      |
| COMP-07  | 无障碍合规率                  | > 98%        | P0     | □        | XX%      |
| COMP-08  | 快照测试通过率                | 100%         | P1     | □        | XX%      |
| COMP-09  | 样式回归测试通过率            | 100%         | P1     | □        | XX%      |
| COMP-10  | 错误边界覆盖率                | 100%         | P0     | □        | XX%      |

### 分级验收准则

#### 🔴 P0 - 必须通过（Blocking）

以下任一条件不满足即**阻断发布**：

- [ ] 所有原子组件覆盖率 > 98%
- [ ] 所有分子/有机体组件覆盖率 > 90%
- [ ] 交互测试通过率 > 99%
- [ ] 无障碍合规率 > 98%（axe-core零违规）
- [ ] Error Boundary 100%覆盖关键组件
- [ ] 表单组件100%支持键盘操作

#### 🟡 P1 - 强烈建议通过（Warning）

以下条件不满足将**降低质量评级**：

- [ ] 模板/页面组件覆盖率 > 85%
- [ ] 快照测试100%通过（或已review确认）
- [ ] 样式回归测试通过
- [ ] 响应式断点测试完成
- [ ] 主题切换测试通过

#### 🟢 P2 - 建议优化（Optional）

以下条件满足将**提升至优秀级别**：

- [ ] 视觉回归测试自动化（Percy/Chromatic）
- [ ] 国际化多语言测试覆盖
- [ ] 动画/过渡效果测试完善
- [ ] 性能指标（渲染耗时）纳入测试
- [ ] Storybook Interaction测试100%通过

---

## 📋 输出报告模板

### 组件测试验收报告结构

```markdown
# YYC³ 组件测试验收报告

## 📋 报告概要

| 属性           | 值                                      |
| -------------- | --------------------------------------- |
| **报告编号**   | RPT-COMP-{YYYYMMDD}-{SEQUENCE}          |
| **项目名称**   | {PROJECT_NAME}                          |
| **报告日期**   | {YYYY-MM-DD HH:MM}                      |
| **验收阶段**   | 第四类：组件测试验收                     |
| **测试负责人** | {TEST_LEADER_NAME}                      |
| **Git Commit** | {COMMIT_HASH}                           |
| **测试环境**   | Node {VERSION}, React {VERSION}, RTL {VERSION} |

---

## 📊 组件测试总览

| 组件类型       | 总数   | 已测试数 | 覆盖率 | 通过率 | 失败数 | 执行耗时 |
| -------------- | ------ | -------- | ------ | ------ | ------ | -------- |
| **原子组件**   | XX     | XX       | XX.X%  | XX.X%  | X      | XXs      |
| **分子组件**   | XX     | XX       | XX.X%  | XX.X%  | X      | XXs      |
| **有机体组件** | XX     | XX       | XX.X%  | XX.X%  | X      | XXs      |
| **模板组件**   | XX     | XX       | XX.X%  | XX.X%  | X      | XXs      |
| **页面组件**   | XX     | XX       | XX.X%  | XX.X%  | X      | XXs      |
| **总计**       | XXX    | XXX      | XX.X%  | XX.X%  | XX     | XXmXXs   |

---

## 🧩 各组件详细结果

### 1. 原子组件 (Atoms)

| 组件名称       | 文件路径                          | 测试数 | 通过 | 失败 | 覆盖率 | 状态   |
| -------------- | --------------------------------- | ------ | ---- | ---- | ------ | ------ |
| Button         | src/components/ui/Button.tsx      | XX     | XX   | X    | XX.X%  | ✅/❌  |
| Input          | src/components/ui/Input.tsx       | XX     | XX   | X    | XX.X%  | ✅/❌  |
| Select         | src/components/ui/Select.tsx      | XX     | XX   | X    | XX.X%  | ✅/❌  |
| Checkbox       | src/components/ui/Checkbox.tsx    | XX     | XX   | X    | XX.X%  | ✅/❌  |
| ...            | ...                               | ...    | ...  | ...  | ...    | ...    |

### 2. 分子组件 (Molecules)

| 组件名称       | 文件路径                          | 测试数 | 通过 | 失败 | 覆盖率 | 状态   |
| -------------- | --------------------------------- | ------ | ---- | ---- | ------ | ------ |
| FormField      | src/components/FormField.tsx      | XX     | XX   | X    | XX.X%  | ✅/❌  |
| SearchInput    | src/components/SearchInput.tsx    | XX     | XX   | X    | XX.X%  | ✅/❌  |
| ...            | ...                               | ...    | ...  | ...  | ...    | ...    |

### 3. 有机体组件 (Organisms)

| 组件名称       | 文件路径                          | 测试数 | 通过 | 失败 | 覆盖率 | 状态   |
| -------------- | --------------------------------- | ------ | ---- | ---- | ------ | ------ |
| UserCard       | src/components/UserCard.tsx       | XX     | XX   | X    | XX.X%  | ✅/❌  |
| FileUploader   | src/components/FileUploader.tsx   | XX     | XX   | X    | XX.X%  | ✅/❌  |
| ...            | ...                               | ...    | ...  | ...  | ...    | ...    |

---

## ♿ 无障碍审计结果

### axe-core 违规统计

| 严重程度   | 违规数量 | 主要违规项                                   | 影响组件               |
| ---------- | -------- | -------------------------------------------- | ---------------------- |
| Critical   | 0        | -                                            | -                      |
| Serious    | X        | {具体违规描述}                                | {ComponentName}        |
| Moderate   | X        | {具体违规描述}                                | {ComponentName}        |
| Minor      | X        | {具体违规描述}                                | {ComponentName}        |

### WCAG 2.1 合规情况

| 原则         | 通过准则数 | 总准则数 | 合格率 | 状态   |
| ------------ | ---------- | -------- | ------ | ------ |
| 可感知性     | XX/XX      | XX       | XX.X%  | ✅/❌  |
| 可操作性     | XX/XX      | XX       | XX.X%  | ✅/❌  |
| 可理解性     | XX/XX      | XX       | XX.X%  | ✅/❌  |
| 健壮性       | XX/XX      | XX       | XX.X%  | ✅/❌  |

---

## 🎨 样式回归结果

| 检查项               | 结果   | 备注                       |
| -------------------- | ------ | -------------------------- |
| Tailwind 类名正确性   | ✅/❌  | {具体说明}                 |
| CSS Variables 应用   | ✅/❌  | {具体说明}                 |
| 响应式断点           | ✅/❌  | {具体说明}                 |
| 主题切换             | ✅/❌  | {具体说明}                 |
| 快照对比             | ✅/❌  | {具体说明}                 |

---

## ❌ 失败用例分析

### 失败组件列表

| 组件名称   | 失败用例数 | 主要失败原因               | 严重程度 | 修复负责人 | 截止日期 |
| ---------- | ---------- | -------------------------- | -------- | ---------- | -------- |
| ComponentA | X          | {原因描述}                 | High     | 张三       | YYYY-MM-DD|
| ComponentB | X          | {原因描述}                 | Medium   | 李四       | YYYY-MM-DD|

### 修复计划

| 用例ID   | 问题根因 | 修复方案                   | 验证方式 | 状态   |
| -------- | -------- | -------------------------- | -------- | ------ |
| CT-001   | 异步时序问题 | 增加 waitFor + act()包裹 | 手动+CI | 进行中 |
| CT-002   | Mock不完整 | 补充 Provider 和 Context | CI自动 | 待开始 |

---

## ✅ 验收结论

### 决策结果

- **综合得分**: XX/100
- **评级**: 优秀 / 良好 / 合格 / 不合格
- **决策**: ✅ 准予发布 / ⚠️ 有条件发布 / 🚫 不通过

### 通过条件确认

- [ ] 原子组件覆盖率 > 98%
- [ ] 分子/有机体组件覆盖率 > 90%
- [ ] 交互测试通过率 > 99%
- [ ] 无障碍合规率 > 98%（零Critical/Serious违规）
- [ ] Error Boundary 覆盖关键路径

### 质量提升建议

1. **短期优化（1周内）**:
   - 修复所有失败的组件测试
   - 补充遗漏的无障碍属性
   - 更新过期的快照测试

2. **中期改进（1月内）**:
   - 引入视觉回归测试平台
   - 完善 Storybook 交互测试
   - 建立组件测试最佳实践文档

3. **长期规划（季度计划）**:
   - 实现 Design Token 驱动的视觉测试
   - 建设组件性能基准测试
   - AI辅助生成组件测试用例

---

## 📝 签字确认

| 角色           | 姓名   | 日期       | 意见   |
| -------------- | ------ | ---------- | ------ |
| 前端负责人     |        | YYYY-MM-DD |        |
| UI/UX设计师   |        | YYYY-MM-DD |        |
| QA工程师       |        | YYYY-MM-DD |        |
| 技术负责人     |        | YYYY-MM-DD |        |

---

**报告生成时间**: {YYYY-MM-DD HH:MM:SS}
**报告有效期**: 至下一版本发布
**下次复验建议**: {YYYY-MM-DD}
```

---

## 🔄 闭环验证机制

### GitHub Actions 工作流

```yaml
# .github/workflows/component-test.yml
name: Component Tests

on:
  pull_request:
    branches: [main, develop]
    paths:
      - 'src/components/**'
      - 'src/**/*.{test,spec}.{ts,tsx}'

jobs:
  component-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: pnpm/action-setup@v2
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'pnpm'

      - run: pnpm install --frozen-lockfile

      - name: Run component tests with coverage
        run: pnpm test:component -- --coverage --reporter=verbose

      - name: Check coverage threshold
        run: |
          COVERAGE=$(cat coverage/coverage-summary.json | jq '.total.lines.pct')
          echo "Line coverage: ${COVERAGE}%"
          if (( $(echo "$COVERAGE < 90" | bc -l) )); then
            echo "::error::Coverage ${COVERAGE}% is below threshold 90%"
            exit 1
          fi

      - name: Run accessibility audit
        run: pnpm test:a11y

      - name: Upload coverage report
        uses: codecov/codecov-action@v3
        if: always()
        with:
          files: ./coverage/lcov.info

      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: component-test-results
          path: |
            coverage/
            test-results/
```

---

## 📚 附录

### A. 组件测试最佳实践

1. **测试行为而非实现**: 关注用户看到什么和做什么，而非内部状态
2. **使用语义化查询**: 优先 getByRole, getByLabelText，避免 getByTestId
3. **真实模拟用户交互**: 使用 userEvent 而非 fireEvent
4. **等待异步操作**: 使用 waitFor, findBy* 处理异步
5. **合理Mock外部依赖**: 只Mock必要的，保持测试真实性
6. **保持测试独立**: 每个测试自包含，无执行顺序依赖
7. **有意义的断言**: 验证业务含义，而非DOM细节

### B. 相关文档索引

- [YYC3-测试用例-审核验收.md](./YYC3-测试用例-审核验收.md) - 前置阶段
- [YYC3-单元框架-审核验收.md](./YYC3-单元框架-审核验收.md) - 后续阶段
- [YYC3-闭环验证-验收标准.md](./YYC3-闭环验证-验收标准.md) - 闭环机制

### C. 版本历史

| 版本   | 日期       | 变更内容                       | 作者                |
| ------ | ---------- | -------------------------------- | ------------------- |
| v1.0.0 | 2026-05-25 | 初始版本，建立组件测试验收标准 | YanYuCloudCube Team |

---

<div align="center">

**© 2026 YanYuCloudCube Team**
**言启象限 | 语枢未来**
**Words Initiate Quadrants, Language Serves as Core for Future**

</div>
