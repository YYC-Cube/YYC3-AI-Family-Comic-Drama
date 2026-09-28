# YYC³ HTML 设计指导文档

> **版本**: v1.0
> **基于**: DGX-SPARK-HUB.html / DGX-SPARK-HUB-OFFLINE.html / YYC3-管理思维-智能一体化转型.html
> **定位**: YYC³ 全系 HTML 应用的统一设计规范（Design System）
> **作者**: YanYuCloudCube™ — 言启象限 · 语枢未来

---

## 一、设计哲学

### 1.1 核心理念

```
                    ┌──────────────────────────────────┐
                    │       YYC³ 设计哲学 · 四维统一       │
                    └───────────────┬──────────────────┘
                                    │
          ┌─────────────┬───────────┼───────────┬────────────┐
          ▼             ▼           ▼           ▼            ▼
    ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
    │  暗色优先  │ │ 数据驱动  │ │ 交互闭环  │ │ 单文件架构 │ │ 移动适配  │
    │ Dark First│ │Data Driven│ │Interactive│ │Single File│ │Responsive │
    └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘
```

| 原则 | 说明 | 实现体现 |
| ------ | ------ | ---------- |
| **暗色优先** | 深色背景为默认主题，提供沉浸式视觉体验；浅色为可切换备选 | `--bg: #0a0a0f` 为默认，`.light` 类切换 |
| **数据驱动** | 所有内容由 JS 数据结构渲染，HTML 仅作为骨架容器 | `GUIDES[]` / `DIMENSIONS[]` 数据数组驱动渲染 |
| **交互闭环** | 每个元素都有明确的交互反馈：hover、click、progress、state | 卡片悬浮、步骤折叠、进度追踪、主题切换 |
| **单文件架构** | CSS + HTML + JS 全部内联在一个 `.html` 文件中，零依赖零构建 | 无外部 CDN、无 npm、无构建步骤 |
| **移动适配** | 768px 断点自动切换布局，侧边栏折叠、网格自适应 | `@media (max-width: 768px)` |

### 1.2 视觉语言

```
色彩体系
┌─────────────────────────────────────────────────────────────┐
│  主色    --accent-v  #8b5cf6  紫色 (Violet)     品牌/强调/激活  │
│  副色    --accent-c  #06b6d4  青色 (Cyan)       链接/信息/提示  │
│  成功    --accent-e  #22c55e  绿色 (Emerald)    完成/正常/通过  │
│  警告    --accent-o  #f59e0b  橙色 (Orange)     警告/中等难度   │
│  危险    --accent-r  #ef4444  红色 (Red)        错误/高难度/删除 │
│  粉色    --accent-p  #ec4899  粉色 (Pink)       创意/多媒体     │
└─────────────────────────────────────────────────────────────┘

层级体系（暗色模式）
┌─────────────────────────────────────────────────────────────┐
│  --bg        #0a0a0f    页面背景（最深）                       │
│  --bg2       #12121a    侧边栏/顶栏背景                         │
│  --bg3       #1a1a2e    卡片/Hero 渐变背景                      │
│  --surface   rgba(255,255,255,0.03)  卡片表面（微透明白）        │
│  --border    rgba(255,255,255,0.08)  边框（微透明白）           │
│  --text      #f1f1f6    主文字（高对比白）                      │
│  --text2     rgba(255,255,255,0.65)  次要文字                   │
│  --text3     rgba(255,255,255,0.35)  辅助/占位文字               │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、CSS 变量规范

### 2.1 完整变量清单

```css
:root {
  /* ═══ 背景 ═══ */
  --bg: #0a0a0f;              /* 页面背景 */
  --bg2: #12121a;             /* 次级背景（侧边栏/顶栏） */
  --bg3: #1a1a2e;             /* 三级背景（渐变/Hero） */

  /* ═══ 表面与边框 ═══ */
  --surface: rgba(255, 255, 255, 0.03);       /* 卡片表面 */
  --surface-hover: rgba(255, 255, 255, 0.06);  /* 卡片悬浮 */
  --border: rgba(255, 255, 255, 0.08);         /* 默认边框 */
  --border-hover: rgba(255, 255, 255, 0.15);   /* 悬浮边框 */

  /* ═══ 文字 ═══ */
  --text: #f1f1f6;                         /* 主文字 */
  --text2: rgba(255, 255, 255, 0.65);      /* 次要文字 */
  --text3: rgba(255, 255, 255, 0.35);      /* 辅助文字 */

  /* ═══ 强调色 ═══ */
  --accent-v: #8b5cf6;   /* 紫色 — 品牌主色 */
  --accent-c: #06b6d4;   /* 青色 — 信息/链接 */
  --accent-e: #22c55e;   /* 绿色 — 成功/完成 */
  --accent-r: #ef4444;   /* 红色 — 错误/危险 */
  --accent-o: #f59e0b;   /* 橙色 — 警告/中等 */
  --accent-p: #ec4899;   /* 粉色 — 创意/多媒体 */

  /* ═══ 圆角 ═══ */
  --radius: 14px;        /* 大圆角（卡片/Hero） */
  --radius-sm: 8px;      /* 小圆角（按钮/输入框/标签） */

  /* ═══ 阴影 ═══ */
  --shadow: 0 4px 24px rgba(0, 0, 0, 0.3);  /* 暗色阴影 */
  /* 浅色模式: 0 4px 24px rgba(0, 0, 0, 0.08) */

  /* ═══ 字体 ═══ */
  --font: -apple-system, BlinkMacSystemFont, 'Segoe UI',
          'PingFang SC', 'Microsoft YaHei', sans-serif;
  --font-mono: 'SF Mono', 'Fira Code', 'Cascadia Code',
               'JetBrains Mono', 'Consolas', monospace;
}
```

### 2.2 浅色主题覆写

```css
.light {
  --bg: #f5f5f0;
  --bg2: #e8e8e3;
  --bg3: #ddd;
  --surface: rgba(0, 0, 0, 0.02);
  --surface-hover: rgba(0, 0, 0, 0.05);
  --border: rgba(0, 0, 0, 0.08);
  --border-hover: rgba(0, 0, 0, 0.15);
  --text: #1a1a2e;
  --text2: rgba(0, 0, 0, 0.55);
  --text3: rgba(0, 0, 0, 0.3);
  --shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
}
```

### 2.3 主题切换 JS

```javascript
function toggleTheme() {
  var isLight = document.documentElement.classList.toggle('light');
  localStorage.setItem('theme', isLight ? 'light' : 'dark');
}
function initTheme() {
  if (localStorage.getItem('theme') === 'light') toggleTheme();
}
initTheme(); // 页面加载时立即执行，避免闪烁
```

> **关键**：`initTheme()` 在 `<style>` 之后、`<body>` 之前内联执行，防止主题闪烁（FOUC）。

---

## 三、布局架构

### 3.1 三段式布局

```
┌──────────┬──────────────────────────────────────────┐
│          │  ┌─ Topbar (sticky, blur) ──────────────┐ │
│  Sidebar │  │ ☰  标题 · 副标题     🔍 ⏰ 📤 ⬆⬇ ↻ 🌙 │ │
│  (fixed) │  └──────────────────────────────────────┘ │
│  280px   │                                            │
│          │  ┌─ Content (max-width) ────────────────┐ │
│  ┌──────┐│  │                                       │ │
│  │Logo  ││  │  Hero / Dashboard                     │ │
│  ├──────┤│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ │ │
│  │Search││  │  │  Card   │ │  Card   │ │  Card   │ │ │
│  ├──────┤│  │  └─────────┘ └─────────┘ └─────────┘ │ │
│  │Progr.││  │  ┌─────────┐ ┌─────────┐             │ │
│  ├──────┤│  │  │  Card   │ │  Card   │             │ │
│  │  Nav ││  │  └─────────┘ └─────────┘             │ │
│  │      ││  │                                       │ │
│  │ Group││  │  Guide Detail (条件显示)               │ │
│  │ Group││  │                                       │ │
│  │ Group││  └───────────────────────────────────────┘ │
│  └──────┘│                                            │
└──────────┴──────────────────────────────────────────┘
```

### 3.2 关键布局规则

| 组件 | 规则 | CSS 实现 |
| ------ | ------ | ---------- |
| `.app` | flex 容器，`min-height: 100vh` | `display: flex` |
| `.sidebar` | 固定定位，280px 宽，可折叠 | `position: fixed; width: 280px; transition: transform 0.3s` |
| `.main` | 左边距 = 侧边栏宽度，可展开 | `margin-left: 280px; transition: margin-left 0.3s` |
| `.topbar` | sticky 定位，毛玻璃背景 | `position: sticky; backdrop-filter: blur(16px)` |
| `.content` / `.dashboard` | 最大宽度居中 | `max-width: 1400px; margin: 0 auto` |
| `.card-grid` | CSS Grid 自适应 | `grid-template-columns: repeat(auto-fill, minmax(320px, 1fr))` |

### 3.3 移动端断点

```css
@media (max-width: 768px) {
  .sidebar { transform: translateX(-100%); }     /* 默认隐藏 */
  .sidebar.show { transform: translateX(0); }    /* 汉堡按钮展开 */
  .main { margin-left: 0; }                      /* 全宽 */
  .topbar-search { display: block; }             /* 显示顶栏搜索 */
  .card-grid { grid-template-columns: 1fr; }     /* 单列 */
}
```

---

## 四、核心组件规范

### 4.1 卡片（Card）

```
┌─────────────────────────────────────────┐
│ ▔▔▔▔▔▔▔▔▔ ← gc-bar（顶部彩色条 3px）      │
│                                         │
│  ┌────┐  标题文本                  ◯    │  ← gc-head（图标+标题+勾选）
│  │icon│  ⭐⭐ 中等 · ⏱ 20 min            │  ← gc-meta（难度标签+时长）
│  └────┘                                 │
│                                         │
│  描述文本，最多两行截断...                  │  ← gc-desc（-webkit-line-clamp: 2）
│                                         │
│  [tag1] [tag2] [tag3]                   │  ← gc-tags（前置条件标签）
│                                         │
│  ⚡ 操作步骤                             │  ← gc-steps（步骤预览）
│  ① 步骤一  ② 步骤二  ③ 步骤三  查看全部→   │
│                                         │
└─────────────────────────────────────────┘
```

**CSS 关键属性**：

```css
.guide-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);        /* 14px */
  padding: 18px;
  transition: all 0.25s ease;
  animation: fadeUp 0.4s ease both;    /* 入场动画 */
}
.guide-card:hover {
  transform: translateY(-2px);          /* 上浮 2px */
  border-color: var(--border-hover);
  box-shadow: var(--shadow);
}
```

### 4.2 步骤详情（Guide Detail）

```
← 返回操作中心

┌─────────────────────────────────────────┐
│  ┌────┐                                  │
│  │icon│  指南标题                         │  ← gd-hero
│  └────┘  描述文本                         │
│          📂 分类 · ⭐ 难度 · ⏱ 时长        │
└─────────────────────────────────────────┘

📊 进度  ████████░░░░░░░░  8/12 步 (67%)    ← gd-progress

📋 前置条件                                ← gd-prereq
  • 条件一
  • 条件二

┌─────────────────────────────────────────┐
│ ① 步骤标题                    ⏱ 5 min  ▶ │  ← step-head（可折叠）
│                                         │
│  步骤内容文本...                          │  ← step-body
│                                         │
│  ┌─ code-block ───────────────────────┐ │  ← 代码块（可复制）
│  │ bash                        📋 复制 │ │
│  │ docker run --gpus all ...          │ │
│  └─────────────────────────────────────┘ │
│                                         │
│  ⚠️ 警告内容                            │  ← step-warning
│  💡 提示内容                             │  ← step-tip
└─────────────────────────────────────────┘
```

### 4.3 难度标签色彩

| 难度 | 色彩 | 背景 | CSS |
| ------ | ------ | ------ | ----- |
| ⭐ 简单 (easy) | `#22c55e` | `rgba(34,197,94,0.12)` | `.gc-tag.easy` |
| ⭐⭐ 中等 (medium) | `#f59e0b` | `rgba(245,158,11,0.12)` | `.gc-tag.medium` |
| ⭐⭐⭐ 高 (hard) | `#ef4444` | `rgba(239,68,68,0.12)` | `.gc-tag.hard` |

### 4.4 代码块

```css
.code-block {
  border-radius: var(--radius-sm);
  overflow: hidden;
  border: 1px solid var(--border);
}
.code-hdr {
  display: flex;
  justify-content: space-between;
  padding: 6px 12px;
  background: var(--bg2);
}
.code-block pre {
  padding: 12px 14px;
  overflow-x: auto;
  font-family: var(--font-mono);
  font-size: 12px;
  line-height: 1.6;
  background: var(--bg);
}
```

**复制功能**：点击 `📋 复制` 按钮 → `navigator.clipboard.writeText()` → 按钮变为 `✅ 已复制` → 2 秒后恢复。

---

## 五、交互功能矩阵

### 5.1 已实现功能

| 功能 | 触发方式 | 技术实现 | 状态持久化 |
| ------ | ---------- | ---------- | ------------ |
| **主题切换** | 🌙/☀️ 按钮 | `classList.toggle('light')` | `localStorage.theme` |
| **侧边栏折叠** | ☰ 按钮 | `classList.toggle('hidden')` | — |
| **智能搜索** | 搜索框输入 | `smartMatch()` 全/半角模糊匹配 | — |
| **分类筛选** | 筛选按钮 | `filterByCategory()` | — |
| **步骤折叠** | 点击步骤标题 | `classList.toggle('open')` | `localStorage.step-open-{id}-{n}` |
| **步骤完成** | 点击步骤编号 | `toggleStepDone()` | `localStorage.step-done-{id}-{n}` |
| **指南完成** | 卡片勾选圆 | `toggleDone()` | `localStorage.guide-done-{id}` |
| **进度追踪** | 自动计算 | `updateSidebarProgress()` | — |
| **进度导出** | ⬇ 按钮 | `Blob → JSON → download` | 文件下载 |
| **进度导入** | ⬆ 按钮 | `FileReader → JSON → localStorage` | — |
| **进度重置** | ↻ 按钮 | `confirm() → removeAll` | — |
| **步骤预览** | "查看全部 N 步" | Modal 弹窗 | — |
| **代码复制** | 📋 按钮 | `clipboard.writeText()` | — |
| **Hash 路由** | URL hash 变化 | `#guide-{id}` / `#guide-{id}-step-{n}` | URL |
| **分享页面** | 📤 按钮 | `navigator.share()` / `clipboard` | — |
| **实时时钟** | 自动 | `setInterval(updateClock, 1000)` | — |

### 5.2 搜索算法

```javascript
function smartMatch(text, query) {
  if (!query) return true;
  // 1. 全角→半角归一化
  var norm = s => s.replace(/[\uff01-\uff5e]/g, c =>
    String.fromCharCode(c.charCodeAt(0) - 0xfee0)).replace(/\u3000/g, ' ');
  var tn = norm(text.toLowerCase());
  var qn = norm(query.toLowerCase());
  // 2. 逐字符顺序匹配（支持中文字符级、英文词级）
  var pos = 0;
  for (var ch of qn) {
    var idx = tn.indexOf(ch, pos);
    if (idx === -1) {
      if (tn.indexOf(ch) === -1) return false;
      continue;
    }
    pos = idx + 1;
  }
  return true;
}
```

---

## 六、数据结构规范

### 6.1 指南数据（GUIDES）

```javascript
var GUIDES = [
  {
    id: 'g01',              // 唯一标识（用于 localStorage key）
    order: 1,               // 序号（侧边栏显示）
    cat: 'inference',       // 分类 key（对应 getCategoryLabels）
    title: 'vLLM 推理引擎',  // 中文标题
    titleEn: 'vLLM',        // 英文/副标题
    diff: 'medium',         // 'easy' | 'medium' | 'hard'
    time: '20 min',         // 预计时长
    icon: '⚡',             // emoji 图标
    desc: '描述文本',        // 卡片描述（≤100 字）
    prereq: ['Docker'],     // 前置条件数组
    overview: [['端口', '8000']], // 概览键值对
    steps: [                // 步骤数组
      {
        n: 1,               // 步骤编号
        title: '步骤标题',
        time: '5 min',
        content: '步骤说明文本',
        code: [['bash', 'docker run ...']], // [标签, 代码]
        warning: '警告文本',  // 可选
        tip: '提示文本',      // 可选
      }
    ],
    // 或者外部链接型：
    type: 'external',
    externalUrl: 'https://...'
  }
];
```

### 6.2 分类映射

```javascript
function getCategoryLabels() {
  return {
    'cat-key': '🌐 中文标签',  // emoji + 中文名
  };
}
function getCategoryColors() {
  return {
    'cat-key': '#hexcolor',   // 对应卡片顶部条颜色
  };
}
```

---

## 七、动画规范

| 动画 | 触发 | 时长 | CSS |
| ------ | ------ | ------ | ----- |
| 卡片入场 | 页面加载 | 0.4s | `@keyframes fadeUp { opacity:0→1, translateY(10px→0) }` |
| 卡片悬浮 | `:hover` | 0.25s | `transition: all 0.25s ease; transform: translateY(-2px)` |
| 侧边栏滑动 | toggle | 0.3s | `transition: transform 0.3s ease` |
| 进度条填充 | 自动 | 0.6s | `transition: width 0.6s ease` |
| 步骤展开 | click | 0.3s | `transition: max-height 0.3s ease` |
| 脉冲点 | 自动循环 | 2s | `@keyframes pulse-dot { opacity 1→0.3→1 }` |
| Hero 光晕 | 自动循环 | 8s | `@keyframes pulse { opacity 0.5→1→0.5 }` |
| 按钮反馈 | `:hover` | 0.2s | `transition: 0.2s` |

---

## 八、可扩展功能蓝图

### 8.1 短期可扩展（基于现有架构直接添加）

| 功能 | 实现方式 | 复杂度 |
| ------ | ---------- | -------- |
| **书签收藏** | `localStorage.bookmark-{id}` + 卡片星标 | ★☆☆ |
| **暗色/浅色/自动三态** | 新增 `auto` 模式 + `prefers-color-scheme` 媒体查询 | ★☆☆ |
| **多语言切换** | 数据结构新增 `titleEn/descEn` + `lang` 状态切换 | ★★☆ |
| **卡片拖拽排序** | HTML5 Drag API + `localStorage.order` | ★★☆ |
| **步骤评论/笔记** | `localStorage.note-{id}-{n}` + textarea 编辑器 | ★★☆ |
| **快捷键导航** | `keydown` 监听（J/K 上下切换、Enter 打开、Esc 返回） | ★☆☆ |
| **PWA 离线支持** | `manifest.json` + Service Worker（缓存 HTML 自身） | ★★☆ |
| **数据统计图表** | Canvas/SVG 绘制完成率饼图、分类分布柱状图 | ★★☆ |

### 8.2 中期可扩展（需新增组件/模块）

| 功能 | 实现方式 | 复杂度 |
| ------ | ---------- | -------- |
| **全屏阅读模式** | 隐藏侧边栏+顶栏，放大字号，专注内容 | ★★☆ |
| **Markdown 渲染** | 内嵌 `marked.js`（或自写 mini-parser），步骤内容支持 MD 语法 | ★★★ |
| **多用户云同步** | 接入后端 API，`localStorage` 与云端双向同步 | ★★★ |
| **版本对比** | Diff 视图，高亮指南更新内容 | ★★★ |
| **命令终端模拟** | 内嵌 xterm.js，模拟真实终端交互体验 | ★★★ |
| **3D 模型预览** | Three.js 内嵌 3D Viewer（用于 Isaac Sim / Omniverse 内容） | ★★★ |

### 8.3 长期可扩展（架构演进方向）

| 功能 | 实现方式 | 复杂度 |
| ------ | ---------- | -------- |
| **多页面路由** | 从单页 Hash 路由升级为 Multi-Page App | ★★★★ |
| **实时协作** | WebSocket + CRDT，多人同时编辑进度/笔记 | ★★★★ |
| **AI 智能助手** | 集成 NIM API，对话式指南推荐与故障排查 | ★★★★ |
| **插件系统** | 定义插件接口，允许第三方扩展卡片类型/交互 | ★★★★★ |

---

## 九、新页面开发 Checklist

创建新的 YYC³ HTML 页面时，按以下 Checklist 执行：

### 9.1 必须（MUST）

- [ ] 复制完整 `:root` CSS 变量定义
- [ ] 复制 `.light` 浅色主题覆写
- [ ] 实现 `toggleTheme()` + `initTheme()` 主题切换
- [ ] 使用 `--accent-v/c/e/r` 色彩体系，禁止硬编码颜色
- [ ] 使用 `var(--font)` 字体栈
- [ ] `<meta viewport>` 移动端适配
- [ ] `@media (max-width: 768px)` 移动端断点
- [ ] SVG data URI favicon（渐变背景 + 字母）
- [ ] 所有交互元素有 hover 反馈
- [ ] 所有动画使用 CSS `transition`/`animation`（非 JS 驱动）

### 9.2 推荐（SHOULD）

- [ ] 侧边栏导航（280px fixed + 搜索 + 分组）
- [ ] 顶栏 sticky + 毛玻璃 (`backdrop-filter: blur`)
- [ ] Hero 区域（渐变背景 + 统计数字）
- [ ] 卡片网格 (`grid-template-columns: repeat(auto-fill, minmax(320px, 1fr))`)
- [ ] 数据驱动渲染（JS 数据数组 → DOM 生成）
- [ ] `localStorage` 状态持久化
- [ ] `::selection` 选区颜色自定义
- [ ] 自定义滚动条样式（`::-webkit-scrollbar`）

### 9.3 可选（MAY）

- [ ] Hash 路由（`#section-id`）
- [ ] 进度追踪系统
- [ ] 导入/导出功能
- [ ] 实时时钟组件
- [ ] 分享功能（`navigator.share`）
- [ ] 卡片入场动画（`fadeUp`）
- [ ] 脉冲动画装饰

---

## 十、文件命名与组织

```
nvidia-workbench/
├── DGX-SPARK-HUB.html              ← 在线版（加载外部 DATA.js）
├── DGX-SPARK-HUB-OFFLINE.html      ← 离线版（内嵌全量数据）
├── DGX-SPARK-DATA.js               ← 在线版数据源
├── YYC3-管理思维-智能一体化转型.html  ← 管理思维设计文档
└── YYC3-HTML-设计指导文档.md         ← 本文档
```

**命名规范**：

- 主应用：`{产品名}-HUB.html`
- 离线版：`{产品名}-HUB-OFFLINE.html`
- 数据源：`{产品名}-DATA.js`
- 设计文档：`YYC3-{主题}.html`

---

## 附录：色彩速查表

```
紫 #8b5cf6  ██████████  accent-v  品牌 · 强调 · 激活态
青 #06b6d4  ██████████  accent-c  链接 · 信息 · 提示
绿 #22c55e  ██████████  accent-e  成功 · 完成 · 简单
橙 #f59e0b  ██████████  accent-o  警告 · 中等
红 #ef4444  ██████████  accent-r  错误 · 高难度 · 删除
粉 #ec4899  ██████████  accent-p  创意 · 多媒体
```

---

*YanYuCloudCube™ — 言启千行代码，语枢万物智能*
*本文档为 YYC³ 全系 HTML 应用的统一设计规范，新页面开发须严格遵循*
