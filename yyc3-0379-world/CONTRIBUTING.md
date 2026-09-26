---
file: CONTRIBUTING.md
description: YYC³ 0379-world 项目贡献指南
author: YanYuCloudCube Team <admin@0379.email>
version: v2.0.0
created: 2026-04-04
updated: 2026-07-10
status: active
tags: [contributing],[guide],[development]
category: guide
language: zh-CN
---

> ***YanYuCloudCube***
> *言启象限 | 语枢未来*
> ***Words Initiate Quadrants, Language Serves as Core for Future***
> *万象归元于云枢 | 深栈智启新纪元*
> ***All things converge in cloud pivot; Deep stacks ignite a new era of intelligence***

---

# 贡献指南 (Contributing Guide)

感谢您考虑为 YYC³ 0379-world 项目做出贡献！本文档将帮助您了解如何参与项目开发。

---

## 📋 目录

- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
- [开发流程](#开发流程)
- [代码规范](#代码规范)
- [提交规范](#提交规范)
- [文档规范](#文档规范)
- [测试规范](#测试规范)
- [问题反馈](#问题反馈)

---

## 行为准则

### 我们的承诺

为了营造一个开放和友好的环境，我们承诺：无论年龄、体型、残疾、种族、性别认同和表达、经验水平、教育程度、国籍、外貌、种族、宗教或性取向如何，参与我们的项目和社区都将为每个人提供无骚扰的体验。

### 我们的标准

积极行为示例：

- 使用友好和包容的语言
- 尊重不同的观点和经验
- 优雅地接受建设性批评
- 关注对社区最有利的事情
- 对其他社区成员表示同理心

---

## 如何贡献

### 报告 Bug

如果您发现了 bug，请通过 [GitHub Issues](https://github.com/YYC-Cube/yyc3-api-world/issues) 提交报告。

**Bug 报告应包含：**

1. **标题**: 简洁明了的描述
2. **描述**: 详细的问题描述
3. **复现步骤**:
   - 步骤 1
   - 步骤 2
   - ...
4. **期望行为**: 应该发生什么
5. **实际行为**: 实际发生了什么
6. **环境信息**:
   - 操作系统: [例如 macOS 14.0]
   - Python 版本: [例如 3.11.0]
   - 项目版本: [例如 v1.0.0]
7. **截图**: 如果适用，添加截图帮助解释问题
8. **其他信息**: 任何其他有助于解决问题的信息

### 建议新功能

我们欢迎新功能建议！请在 [GitHub Issues](https://github.com/YYC-Cube/yyc3-api-world/issues) 中创建一个功能请求。

**功能请求应包含：**

1. **标题**: 清晰的功能描述
2. **描述**: 详细的功能描述
3. **动机**: 为什么需要这个功能
4. **解决方案**: 您建议的实现方式
5. **替代方案**: 您考虑过的其他方案
6. **其他信息**: 任何其他相关信息

### 提交代码

1. **Fork 项目**

   ```bash
   # 在 GitHub 上 Fork 项目
   git clone https://github.com/YOUR_USERNAME/yyc3-api-world.git
   cd yyc3-api-world
   ```

2. **创建分支**

   ```bash
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b fix/your-bug-fix
   ```

3. **进行更改**
   - 遵循代码规范
   - 添加必要的测试
   - 更新相关文档

4. **提交更改**

   ```bash
   git add .
   git commit -m "feat: 添加新功能描述"
   ```

5. **推送到 GitHub**

   ```bash
   git push origin feature/your-feature-name
   ```

6. **创建 Pull Request**
   - 在 GitHub 上创建 Pull Request
   - 填写 PR 模板
   - 等待代码审查

---

## 开发流程

### 环境设置

1. **克隆项目**

   ```bash
   git clone https://github.com/YYC-Cube/yyc3-api-world.git
   cd yyc3-api-world
   ```

2. **创建虚拟环境**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # macOS/Linux
   # 或
   .venv\Scripts\activate  # Windows
   ```

3. **安装依赖**

   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # 开发依赖
   ```

4. **配置环境变量**

   ```bash
   cp .env.example .env
   # 编辑 .env 文件，配置必要的环境变量
   ```

5. **启动服务**

   ```bash
   # 启动数据库服务
   docker-compose -f core/database/docker/docker-compose.stable.yml up -d

   # 启动 API 服务
   cd core/api
   python main.py
   ```

### 分支策略

- `main`: 主分支，稳定版本
- `develop`: 开发分支，最新功能
- `feature/*`: 功能分支
- `fix/*`: 修复分支
- `release/*`: 发布分支
- `hotfix/*`: 紧急修复分支

---

## 代码规范

### Python 代码规范

遵循 PEP 8 规范，并使用以下工具进行检查：

```bash
# 代码格式化
black .

# 代码检查
flake8 .

# 类型检查
mypy .
```

### 文件标头规范

所有 Python 文件必须包含 `#` 注释风格的标头：

```python
# file: example.py
# description: 示例模块描述
# author: Your Name <your.email@example.com>
# version: v1.0.0
# created: 2026-04-04
# updated: 2026-04-04
# status: active
# tags: [example],[module]

def example_function():
    """示例函数"""
    pass
```

> **注意**: 不要使用 `/** ... */` JSDoc 风格注释，它在 Python 中是非法语法。

### 命名规范

- **文件名**: snake_case（例如：`user_service.py`）
- **类名**: PascalCase（例如：`UserService`）
- **函数名**: snake_case（例如：`get_user_by_id`）
- **变量名**: snake_case（例如：`user_name`）
- **常量**: UPPER_SNAKE_CASE（例如：`MAX_RETRY_COUNT`）

### 代码注释

- 使用中文注释
- 函数和类必须有文档字符串
- 复杂逻辑必须有注释说明

```python
def calculate_total_price(items: list, discount: float = 0.0) -> float:
    """
    计算订单总价

    Args:
        items: 商品列表
        discount: 折扣率（0.0-1.0）

    Returns:
        float: 订单总价

    Example:
        >>> items = [{'price': 100, 'quantity': 2}]
        >>> calculate_total_price(items, 0.9)
        180.0
    """
    total = sum(item['price'] * item['quantity'] for item in items)
    return total * (1 - discount)
```

---

## 提交规范

### 提交消息格式

使用约定式提交（Conventional Commits）规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 提交类型（type）

- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式调整（不影响代码运行）
- `refactor`: 代码重构
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建/工具相关
- `ci`: CI/CD 相关
- `revert`: 回退提交

### 提交范围（scope）

- `api`: API 相关
- `db`: 数据库相关
- `auth`: 认证相关
- `ui`: UI 相关
- `config`: 配置相关
- `docs`: 文档相关

### 示例

```bash
# 新功能
git commit -m "feat(api): 添加用户登录接口"

# Bug 修复
git commit -m "fix(db): 修复数据库连接池泄漏问题"

# 文档更新
git commit -m "docs(readme): 更新安装说明"

# 代码重构
git commit -m "refactor(auth): 重构认证逻辑"

# 性能优化
git commit -m "perf(cache): 优化 Redis 缓存策略"
```

---

## 文档规范

### Markdown 文档规范

所有 Markdown 文档必须包含 YAML Front Matter 标头：

```markdown
---
file: example.md
description: 示例文档描述
author: Your Name <your.email@example.com>
version: v1.0.0
created: 2026-04-04
updated: 2026-04-04
status: active
tags: [example],[documentation]
category: guide
language: zh-CN
---

> ***YanYuCloudCube***
> *言启象限 | 语枢未来*
> ***Words Initiate Quadrants, Language Serves as Core for Future***
> *万象归元于云枢 | 深栈智启新纪元*
> ***All things converge in cloud pivot; Deep stacks ignite a new era of intelligence***

---

# 文档标题

文档内容...
```

### 文档结构

1. **标题**: 清晰简洁
2. **目录**: 长文档必须包含目录
3. **简介**: 简要说明文档内容
4. **正文**: 详细内容
5. **示例**: 代码示例和用法
6. **参考**: 相关文档链接

---

## 测试规范

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_user_service.py

# 运行特定测试函数
pytest tests/test_user_service.py::test_get_user_by_id

# 生成测试覆盖率报告
pytest --cov=core --cov-report=html
```

### 测试命名

- 测试文件: `test_*.py`
- 测试类: `Test*`
- 测试函数: `test_*`

```python
# test_user_service.py

class TestUserService:
    """用户服务测试类"""

    def test_get_user_by_id(self):
        """测试根据 ID 获取用户"""
        # 准备
        user_id = 1

        # 执行
        user = UserService.get_user_by_id(user_id)

        # 断言
        assert user is not None
        assert user.id == user_id

    def test_create_user(self):
        """测试创建用户"""
        # 准备
        user_data = {
            'username': 'testuser',
            'email': 'test@example.com'
        }

        # 执行
        user = UserService.create_user(user_data)

        # 断言
        assert user.id is not None
        assert user.username == 'testuser'
```

---

## 问题反馈

### 创建 Issue

1. 访问 [GitHub Issues](https://github.com/YYC-Cube/yyc3-api-world/issues)
2. 点击 "New Issue"
3. 选择合适的模板（Bug 报告或功能请求）
4. 填写详细信息
5. 提交 Issue

### Issue 标签

- `bug`: Bug 报告
- `enhancement`: 功能增强
- `documentation`: 文档相关
- `good first issue`: 适合新手
- `help wanted`: 需要帮助
- `question`: 问题咨询

---

## 联系方式

- **邮箱**: <admin@0379.email>
- **网站**: <https://0379.world>
- **GitHub**: <https://github.com/YYC-Cube>

---

## 许可证

通过贡献代码，您同意您的代码将根据项目的 MIT 许可证进行许可。

---

**感谢您的贡献！** 🎉

---

**维护团队**: YanYuCloudCube Team
**最后更新**: 2026-04-04
