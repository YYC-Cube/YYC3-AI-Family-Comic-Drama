# 06 语枢·万物 接口文档

> 版本 v1.0.0 | 更新 2026-09-24 | 代码 [yushu_wanwu_agent.py](yushu_wanwu_agent.py) | 继承 [BaseAgent](../00-公共基座/API.md)
> 示例前提：所有代码文件位于同一 Python 包目录

## 一、接口清单

| 接口名称 | 签名 | 功能简述 |
| -------- | ---- | -------- |
| `analyze` | `(query, knowledge_context=None) -> str` | 数据分析主入口（Step4） |
| `decompose_problem` | `(complex_problem) -> list[dict]` | 复杂问题分解 |

## 二、接口详情

### 2.1 `analyze` — 数据分析

**功能描述**：按四段式标准输出分析报告（📌核心结论/📊数据支撑/🔍逻辑论证/💡行动建议），引用知识时保留来源标识，禁止虚构数值。

**请求参数**：

| 参数名 | 类型 | 必填 | 描述 |
| ------ | ---- | ---- | ---- |
| query | str | 是 | 分析请求，如「分析本季度营收情况」 |
| knowledge_context | list[str] | 否 | RAG 注入的带来源知识片段 |

**返回参数**：

| 参数名 | 类型 | 描述 |
| ------ | ---- | ---- |
| （返回值） | str | 四段式分析报告 |

**调用示例**：

```python
from yushu_wanwu_agent import YuShuWanWuAgent

thinker = YuShuWanWuAgent()

# 场景1：带知识库的经营分析
report = thinker.analyze(
    query="分析本季度营收增长驱动因素",
    knowledge_context=[
        "[来源：2026Q2经营报告.pdf] Q2营收同比增长32%，云业务占比65%",
        "[来源：CRM导出.xlsx] 企业级客户新增240家",
    ],
)

# 场景2：无知识通用分析（如代码逻辑分析）
report2 = thinker.analyze(query="对比快速排序与归并排序的时间复杂度")
```

预期返回：

```text
📌 核心结论：本季度营收增长主要由云业务驱动（贡献率65%）...
📊 数据支撑：同比增长32% [来源：2026Q2经营报告.pdf]；企业级客户新增240家 [来源：CRM导出.xlsx]
🔍 逻辑论证：客户扩张→订阅收入增长→营收提升，传导链完整...
💡 行动建议：1.加大企业级销售投入（高优先级）...
```

### 2.2 `decompose_problem` — 复杂问题分解

**请求参数**：

| 参数名 | 类型 | 必填 | 描述 |
| ------ | ---- | ---- | ---- |
| complex_problem | str | 是 | 复杂问题描述 |

**返回参数**：

| 参数名 | 类型 | 描述 |
| ------ | ---- | ---- |
| （返回值） | list[dict] | 元素含 `sub_problem`（子问题）/ `method`（分析方法）/ `priority`（高/中/低） |

**错误码**：YYC3-AGT-4003（非JSON时兜底为单元素清单）

**调用示例**：

```python
subs = thinker.decompose_problem("评估是否进入企业知识管理市场")
print(subs[0])
```

预期返回：`{'sub_problem': '市场规模与增速测算', 'method': '行业报告+RAG检索', 'priority': '高'}`

---

*© 2025-2026 YYC³ Team. All Rights Reserved.*
