# 03 格物·宗师 接口文档

> 版本 v1.0.0 | 更新 2026-09-24 | 代码 [gewu_zongshi_agent.py](gewu_zongshi_agent.py) | 继承 [BaseAgent](../00-公共基座/API.md)
> 示例前提：所有代码文件位于同一 Python 包目录

## 一、接口清单

| 接口名称 | 签名 | 功能简述 |
| -------- | ---- | -------- |
| `validate` | `(content, knowledge_context=None) -> dict` | 质量校验与事实核查（Step7） |
| `review_code` | `(code, language="python") -> str` | 代码质量审计 |

## 二、接口详情

### 2.1 `validate` — 质量校验与事实核查

**功能描述**：按四维标准（数值准确性/逻辑一致性/事实溯源/结构完整性）校验内容，对照 RAG 参考知识核查事实，输出评分与修正建议。通过线 **≥80 分**。

**请求参数**：

| 参数名 | 类型 | 必填 | 描述 |
| ------ | ---- | ---- | ---- |
| content | str | 是 | 待校验核心内容（优先级：polished_report > yuanqi_summary > yushu_analysis） |
| knowledge_context | list[str] | 否 | RAG 检索到的带来源知识片段，用于溯源比对 |

**返回参数**：

| 参数名 | 类型 | 描述 |
| ------ | ---- | ---- |
| score | float | 质量评分 0-100 |
| passed | bool | 是否通过（score ≥ 80） |
| suggestions | str | 逐条修正建议 |
| unverified_claims | list[str] | 无来源支撑的断言清单 |

**错误码**：YYC3-AGT-4003（输出非JSON时兜底 `score=75/passed=False`，原文进 suggestions）

**调用示例**：

```python
from gewu_zongshi_agent import GeWuZongShiAgent

gewu = GeWuZongShiAgent()

# 场景1：有知识溯源的高质量内容 → 通过
r1 = gewu.validate(
    content="Q2营收同比增长32%，其中云业务占比65%（来源：Q2经营报告）",
    knowledge_context=["[来源：2026Q2经营报告.pdf] Q2营收同比增长32%，云业务占比65%"],
)
# 预期返回：{'score': 92, 'passed': True, 'suggestions': '...', 'unverified_claims': []}

# 场景2：含无依据断言 → 不通过，触发二次优化
r2 = gewu.validate(
    content="Q3营收预计增长120%，行业第一",
    knowledge_context=[],
)
# 预期返回：{'score': 45, 'passed': False,
#            'suggestions': '删除无依据的120%预测与行业第一表述，补充数据来源',
#            'unverified_claims': ['Q3营收预计增长120%', '行业第一']}
```

### 2.2 `review_code` — 代码质量审计

**功能描述**：静态扫描、Bug 检测、性能与规范检查，问题按 CRITICAL/HIGH/MEDIUM/LOW 分级。

**请求参数**：

| 参数名 | 类型 | 必填 | 描述 |
| ------ | ---- | ---- | ---- |
| code | str | 是 | 待审计代码文本 |
| language | str | 否 | 语言标识，默认 `python` |

**返回参数**：

| 参数名 | 类型 | 描述 |
| ------ | ---- | ---- |
| （返回值） | str | 问题清单（分级）+ 修复建议 + 优化方案 |

**调用示例**：

```python
report = gewu.review_code("""
def get_user(id):
    q = "SELECT * FROM users WHERE id=" + id
    return db.execute(q)
""", language="python")
print(report)
```

预期返回：

```text
【CRITICAL】SQL注入漏洞：字符串拼接构建查询 → 使用参数化查询
【MEDIUM】缺少类型注解与异常处理 → 补充 typing 与 try/except
【优化建议】指定查询字段替代 SELECT * ...
```

---

*© 2025-2026 YYC³ Team. All Rights Reserved.*
