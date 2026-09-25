# 05 言启·千行 接口文档

> 版本 v1.0.0 | 更新 2026-09-24 | 代码 [yanqi_qianhang_agent.py](yanqi_qianhang_agent.py) | 继承 [BaseAgent](../00-公共基座/API.md)
> 示例前提：所有代码文件位于同一 Python 包目录

## 一、接口清单

| 接口名称 | 签名 | 功能简述 |
| -------- | ---- | -------- |
| `run` | `(prompt, context="") -> dict` | 意图识别与任务路由（重写基类，Step2） |
| `_rule_based_route` | `(user_input) -> dict` | 规则兜底路由（内部方法） |
| `format_output` | `(final_output, confidence=0.0, risk_notes="") -> str` | 结构化格式化输出 |

## 二、接口详情

### 2.1 `run` — 意图识别与任务路由

**功能描述**：LLM 意图分类 → JSON 解析 → 合法性校验 → 自动生成 `trace_id`；LLM/解析失败自动切换规则兜底。返回结构化路由结果（区别于基类返回 str）。

**请求参数**：

| 参数名 | 类型 | 必填 | 描述 |
| ------ | ---- | ---- | ---- |
| prompt | str | 是 | 用户请求原文 |
| context | str | 否 | 兼容基类签名，路由场景通常为空 |

**返回参数**：

| 参数名 | 类型 | 描述 |
| ------ | ---- | ---- |
| intent | str | 意图：data_analysis/trend_forecast/report_polish/creative_brainstorm/personnel_development/knowledge_query/code_development/multi_agent_comprehensive |
| complexity | str | 复杂度：simple/complex/multi_agent |
| need_rag | bool | 是否需要知识检索 |
| trace_id | str | 全链路追踪ID，格式 `trace-YYYYMMDD-xxxxxx` |

**错误码**：YYC3-AGT-4003（触发规则兜底，不抛异常）

**调用示例**：

```python
from yanqi_qianhang_agent import YanQiQianHangAgent

navigator = YanQiQianHangAgent()

# 场景1：综合任务 → 多Agent路由
r1 = navigator.run("生成本季度经营分析报告，包含数据解读、趋势预测、可视化")
# 预期返回：{'intent': 'multi_agent_comprehensive', 'complexity': 'multi_agent',
#            'need_rag': True, 'trace_id': 'trace-20260924-a1b2c3'}

# 场景2：纯技术问题 → 无需RAG
r2 = navigator.run("用Python写一个快速排序")
# 预期返回：{'intent': 'code_development', 'complexity': 'simple',
#            'need_rag': False, 'trace_id': 'trace-20260924-d4e5f6'}

# 场景3：LLM不可用 → 规则兜底仍可用
r3 = navigator.run("分析一下最近销售数据")
# 预期返回：{'intent': 'data_analysis', 'complexity': 'simple', ...}
```

### 2.2 `_rule_based_route` — 规则兜底路由

**功能描述**：基于关键词映射的离线路由，LLM 降级时由 `run` 自动调用。

**请求参数**：`user_input` (str, 必填)

**返回参数**：`{"intent", "complexity", "need_rag"}`（不含 trace_id，由 `run` 统一补充）

**调用示例**：

```python
route = navigator._rule_based_route("帮我策划一个营销活动")
# 预期返回：{'intent': 'creative_brainstorm', 'complexity': 'simple', 'need_rag': True}
```

### 2.3 `format_output` — 结构化输出

**功能描述**：为最终结果添加标题头（含置信度）与风险提示尾（对齐架构 T8 规范）。

**请求参数**：

| 参数名 | 类型 | 必填 | 描述 |
| ------ | ---- | ---- | ---- |
| final_output | str | 是 | 最终输出内容 |
| confidence | float | 否 | 置信度 0~1，默认0 |
| risk_notes | str | 否 | 风险提示，默认「无」 |

**调用示例**：

```python
text = navigator.format_output("Q2营收同比增长32%", confidence=0.92,
                               risk_notes="云业务客户集中度上升")
```

预期返回：

```text
📌 AI FAmily 综合输出（置信度：92%）
========================================
Q2营收同比增长32%
========================================
⚠️ 风险提示：云业务客户集中度上升
```

---

*© 2025-2026 YYC³ Team. All Rights Reserved.*
