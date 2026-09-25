# 00 公共基座 BaseAgent 接口文档

> 版本 v1.0.0 | 更新 2026-09-24 | 代码 [base_agent.py](base_agent.py)
> 示例前提：所有代码文件位于同一 Python 包目录（见主 README 部署说明）

## 一、统一错误码规范（全项目通用）

| 错误码 | 含义 | 触发条件 | 处理建议 |
| ------ | ---- | -------- | -------- |
| YYC3-AGT-4001 | 参数错误 | 必填参数缺失或类型不符 | 检查入参 |
| YYC3-AGT-4002 | LLM调用失败 | NIM服务不可达/超时 | 自动降级Mock；检查 `LLM_BASE_URL` |
| YYC3-AGT-4003 | 结构化解析失败 | 模型输出非合法JSON | 已内置兜底逻辑，建议复检提示词 |
| YYC3-AGT-5001 | 向量库连接失败 | Milvus不可达 | 检查 `MILVUS_HOST/PORT` |
| YYC3-AGT-5101 | 消息队列连接失败 | Redis不可达 | 检查 `REDIS_HOST/PORT` |

## 二、接口清单

| 接口名称 | 签名 | 功能简述 |
| -------- | ---- | -------- |
| `__init__` | `(name, role, system_prompt)` | Agent 三要素初始化 |
| `run` | `(prompt, context="") -> str` | 统一 LLM 调用入口 |
| `_mock_run` | `(prompt) -> str` | 离线兜底输出 |
| `heartbeat` | `() -> dict` | 心跳信息上报 |

## 三、接口详情

### 3.1 `__init__` — 初始化 Agent

**功能描述**：以「人格化名称 + 角色定位 + 系统提示词」三要素构建 Agent 实例，加载环境变量配置。

**请求参数**：

| 参数名 | 类型 | 必填 | 描述 |
| ------ | ---- | ---- | ---- |
| name | str | 是 | 人格化名称，如「元启·天枢」 |
| role | str | 是 | 角色定位，如「总指挥·决策中枢」 |
| system_prompt | str | 是 | 系统提示词，定义能力边界与输出规范 |

**返回参数**：实例自身（副作用：初始化 `self.name/role/system_prompt/_client=None`）

**错误码**：YYC3-AGT-4001（任一参数为空）

**调用示例**：

```python
from base_agent import BaseAgent

agent = BaseAgent(
    name="测试助手",
    role="通用问答",
    system_prompt="你是YYC³测试助手，简洁回答问题。",
)
print(agent.name, agent.role)
```

预期返回（控制台）：`测试助手 通用问答`

### 3.2 `run` — 统一 LLM 调用

**功能描述**：拼接 context 与 prompt 调用 OpenAI 兼容接口（NIM 服务）；失败时自动降级 `_mock_run`，保障链路可用。

**请求参数**：

| 参数名 | 类型 | 必填 | 描述 |
| ------ | ---- | ---- | ---- |
| prompt | str | 是 | 任务提示词 |
| context | str | 否 | RAG 注入上下文，格式 `[来源：xxx] 内容`，默认空 |

**返回参数**：

| 参数名 | 类型 | 描述 |
| ------ | ---- | ---- |
| （返回值） | str | 模型输出文本；降级时带 `[Agent名\|Mock]` 前缀 |

**错误码**：YYC3-AGT-4002（触发降级，不抛异常）

**环境变量**：`LLM_BASE_URL`（默认 `http://localhost:8000/v1`）、`LLM_API_KEY`、`LLM_MODEL`（默认 `deepseek-v4-pro`）、`LLM_TEMPERATURE`（默认 0.3）

**调用示例**：

```python
# 场景1：带知识库上下文的问答
answer = agent.run(
    prompt="本季度营收趋势如何？",
    context="[来源：2026Q2经营报告.pdf] Q2营收同比增长32%",
)

# 场景2：纯通用问答（无上下文）
answer2 = agent.run(prompt="用一句话介绍多Agent协同")
```

预期返回：

```text
场景1：根据Q2经营报告，营收同比增长32%，呈上升趋势...
场景2：多Agent协同指多个专业化智能体分工协作完成复杂任务...
（LLM不可用时）场景1：[测试助手|Mock] 已接收任务：本季度营收趋势如何？...
```

### 3.3 `heartbeat` — 心跳上报

**功能描述**：返回 Agent 在线状态摘要，供 A2A 注册中心心跳保活使用。

**请求参数**：无

**返回参数**：

| 参数名 | 类型 | 描述 |
| ------ | ---- | ---- |
| agent_name | str | Agent 名称 |
| role | str | 角色定位 |
| status | str | 固定 `online` |

**调用示例**：

```python
print(agent.heartbeat())
```

预期返回：`{'agent_name': '测试助手', 'role': '通用问答', 'status': 'online'}`

---

*© 2025-2026 YYC³ Team. All Rights Reserved.*
