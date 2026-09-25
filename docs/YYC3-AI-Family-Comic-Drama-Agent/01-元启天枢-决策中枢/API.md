# 01 元启·天枢 接口文档

> 版本 v1.0.0 | 更新 2026-09-24 | 代码 [yuanqi_tianshu_agent.py](yuanqi_tianshu_agent.py) | 继承 [BaseAgent](../00-公共基座/API.md)
> 示例前提：所有代码文件位于同一 Python 包目录

## 一、接口清单

| 接口名称 | 签名 | 功能简述 |
| -------- | ---- | -------- |
| `plan_tasks` | `(user_input, available_agents=None) -> list[dict]` | 综合任务分解为子任务计划 |
| `synthesize` | `(user_input, agent_outputs) -> str` | 全局汇总与决策升华（Step6） |
| `decide` | `(user_input, knowledge=None) -> dict` | 五步决策框架完整决策 |

## 二、接口详情

### 2.1 `plan_tasks` — 任务分解编排

**功能描述**：将综合复杂任务拆解为可并行/串行执行的子任务计划，供编排引擎或 AsyncOrchestrator 分发。

**请求参数**：

| 参数名 | 类型 | 必填 | 描述 |
| ------ | ---- | ---- | ------ |
| user_input | str | 是 | 综合任务描述 |
| available_agents | list[str] | 否 | 可用能力标签列表，如 `["data_analysis", "trend_forecast"]`，默认空 |

**返回参数**：

| 参数名 | 类型 | 描述 |
| ------ | ---- | ---- |
| （返回值） | list[dict] | 子任务数组，元素含 `agent`（Agent名）/ `task_type`（能力标签）/ `payload`（任务参数）/ `depends_on`（前置依赖下标数组） |

**错误码**：YYC3-AGT-4003（输出非JSON，兜底为单任务计划）

**调用示例**：

```python
from yuanqi_tianshu_agent import YuanQiTianShuAgent

tianshu = YuanQiTianShuAgent()
plan = tianshu.plan_tasks(
    user_input="生成本季度经营分析报告，包含数据解读、趋势预测与可视化",
    available_agents=["data_analysis", "trend_forecast", "report_polish"],
)
print(plan)
```

预期返回：

```json
[
  {"agent": "语枢·万物", "task_type": "data_analysis",
   "payload": {"query": "分析本季度经营数据核心指标"}, "depends_on": []},
  {"agent": "预见·先知", "task_type": "trend_forecast",
   "payload": {"metric": "季度营收", "periods": 3}, "depends_on": [0]},
  {"agent": "创想·灵韵", "task_type": "report_polish",
   "payload": {"raw": "${task_1_output}"}, "depends_on": [0, 1]}
]
```

### 2.2 `synthesize` — 全局汇总与决策升华

**功能描述**：整合多 Agent 产出，校验逻辑一致性，输出🎯核心结论、⚠️风险、💡机会与综合报告。

**请求参数**：

| 参数名 | 类型 | 必填 | 描述 |
| ------ | ---- | ---- | ---- |
| user_input | str | 是 | 原始用户请求 |
| agent_outputs | dict[str, str] | 是 | 各Agent产出，键为产出名（如 `yushu_analysis`） |

**返回参数**：

| 参数名 | 类型 | 描述 |
| ------ | ---- | ---- |
| （返回值） | str | 综合决策报告文本（含🎯/⚠️/💡标记） |

**调用示例**：

```python
summary = tianshu.synthesize(
    user_input="生成本季度经营分析报告",
    agent_outputs={
        "yushu_analysis": "Q2营收同比增长32%，云业务占比65%...",
        "yujian_forecast": "预计Q3营收增长18%~22%，置信区间95%...",
    },
)
print(summary)
```

预期返回：

```text
🎯 核心结论：1.Q2营收同比增长32%... 2.Q3预测增长18%~22%...
⚠️ 风险点：企业级客户集中度上升...
💡 创新机会：云业务与AI订阅打包...
【综合报告】...
```

### 2.3 `decide` — 五步决策框架

**功能描述**：按「问题定义→信息收集→方案生成(≥3)→评估排序→推荐建议」输出完整决策分析，默认标记需人类确认。

**请求参数**：

| 参数名 | 类型 | 必填 | 描述 |
| ------ | ---- | ---- | ---- |
| user_input | str | 是 | 决策事项描述 |
| knowledge | list[str] | 否 | 决策参考知识（RAG检索结果） |

**返回参数**：

| 参数名 | 类型 | 描述 |
| ------ | ---- | ---- |
| decision_report | str | 五步决策完整报告 |
| requires_human_confirm | bool | 固定 `True`（关键决策需人类最终确认） |

**调用示例**：

```python
decision = tianShu.decide(
    user_input="是否将AI客服从试点部门推广至全公司",
    knowledge=["[来源：试点复盘.docx] 试点满意度4.6/5"],
)
print(decision["requires_human_confirm"])
```

预期返回：`True`（`decision_report` 含3个方案与权重评分矩阵）

**错误码**：YYC3-AGT-4002（LLM降级时报告为Mock文本）

---

*© 2025-2026 YYC³ Team. All Rights Reserved.*
