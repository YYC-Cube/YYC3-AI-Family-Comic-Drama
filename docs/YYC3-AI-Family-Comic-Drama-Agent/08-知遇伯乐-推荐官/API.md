# 08 知遇·伯乐 接口文档

> 版本 v1.0.0 | 更新 2026-09-24 | 代码 [zhiyu_bole_agent.py](zhiyu_bole_agent.py) | 继承 [BaseAgent](../00-公共基座/API.md)
> 示例前提：所有代码文件位于同一 Python 包目录

## 一、接口清单

| 接口名称 | 签名 | 功能简述 |
| -------- | ---- | -------- |
| `build_user_profile` | `(user_id, behavior_data, self_description="") -> dict` | 构建/更新用户画像（Step9） |
| `recommend_content` | `(user_id, scene="学习提升", knowledge_pool=[], top_n=3) -> list` | 个性化内容推荐 |
| `plan_growth_path` | `(user_id, target, time_cycle="3个月") -> dict` | 成长路径规划 |
| `optimize_experience` | `(user_feedback, current_process) -> dict` | 体验优化建议 |

## 二、接口详情

### 2.1 `build_user_profile` — 用户画像

**功能描述**：基于行为数据与自我描述构建结构化画像，写入内存存储（生产切数据库），记录更新时间。

**请求参数**：

| 参数名 | 类型 | 必填 | 描述 |
| ------ | ---- | ---- | ---- |
| user_id | str | 是 | 用户唯一标识 |
| behavior_data | dict | 是 | 行为数据：`{"浏览记录": [], "查询主题": [], "能力标签": [], "使用频率": ""}` |
| self_description | str | 否 | 用户自我描述 |

**返回参数**：

| 参数名 | 类型 | 描述 |
| ------ | ---- | ---- |
| core_tags | list[str] | 3-5个核心能力标签 |
| growth_stage | str | 入门/进阶/资深/专家 |
| interest_areas | list[str] | 兴趣领域 |
| strength / improvement | str | 优势领域 / 待提升方向 |
| learning_style | str | 学习风格偏好 |
| recommended_level | str | 推荐内容难度等级 |
| update_time | str | 更新时间 `YYYY-MM-DD HH:MM:SS` |
| raw_analysis | str | 仅解析失败时返回模型原文 |

**调用示例**：

```python
from zhiyu_bole_agent import ZhiYuBoLeAgent

bole = ZhiYuBoLeAgent()
profile = bole.build_user_profile(
    user_id="manager_001",
    behavior_data={"查询主题": ["经营分析", "趋势预测"], "使用频率": "每日"},
    self_description="10年经验的企业经营分析师",
)
```

预期返回：

```json
{"core_tags": ["数据分析", "经营决策", "AI工具应用"],
 "growth_stage": "资深", "interest_areas": ["商业智能", "预测建模"],
 "strength": "经营指标体系设计", "improvement": "机器学习建模深度",
 "learning_style": "案例驱动", "recommended_level": "进阶",
 "update_time": "2026-09-24 15:30:00"}
```

### 2.2 `recommend_content` — 个性化推荐

**请求参数**：

| 参数名 | 类型 | 必填 | 描述 |
| ------ | ---- | ---- | ---- |
| user_id | str | 是 | 用户ID（无画像时自动构建空画像） |
| scene | str | 否 | 学习提升/工作工具/参考资料/职业发展 |
| knowledge_pool | list | 否 | 候选内容池（RAG检索候选） |
| top_n | int | 否 | 推荐数量，默认3 |

**返回参数**：list[dict]，元素含 `content` / `match_score`(0-100) / `recommend_reason` / `learning_value`；推荐必须附理由与匹配度

**调用示例**：

```python
recs = bole.recommend_content(
    user_id="manager_001", scene="学习提升",
    knowledge_pool=["时序预测实战手册", "SQL性能优化指南", "OKR落地方法"],
    top_n=2)
```

预期返回：

```json
[{"content": "时序预测实战手册", "match_score": 95,
  "recommend_reason": "匹配「趋势预测」高频查询主题", "learning_value": "高"},
 {"content": "OKR落地方法", "match_score": 82, "...": "..."}]
```

### 2.3 `plan_growth_path` — 成长路径规划

**请求参数**：`user_id`（str，必填）、`target`（str，必填，成长目标）、`time_cycle`（str，选填，默认「3个月」）

**返回参数**：dict，含 `overall_goal` / `phases`（数组，元素含 phase_name/duration/core_tasks/milestone/recommended_resources）/ `assessment_method` / `risk_reminder`；解析失败返回 `{"plan_text": 原文}`

**调用示例**：

```python
plan = bole.plan_growth_path(user_id="manager_001",
                             target="掌握Python数据分析", time_cycle="3个月")
print(plan["phases"][0]["milestone"])
```

预期返回：`完成销售数据清洗与可视化看板，通过阶段性代码评审`

### 2.4 `optimize_experience` — 体验优化

**请求参数**：`user_feedback`（str，必填，用户反馈）、`current_process`（str，必填，当前流程描述）

**返回参数**：dict，含 `problem_analysis` / `optimization_suggestions`（数组，元素含 suggestion/expected_effect/priority）/ `priority_order`

**调用示例**：

```python
opt = bole.optimize_experience(
    user_feedback="报告生成要等很久，不知道进行到哪一步",
    current_process="用户提交请求→全链路执行→一次性返回结果")
```

预期返回：

```json
{"problem_analysis": "长任务缺少进度反馈，用户感知等待成本高",
 "optimization_suggestions": [
   {"suggestion": "接入SSE流式进度推送", "expected_effect": "等待感知降低60%", "priority": "高"},
   {"suggestion": "分阶段返回中间结果", "expected_effect": "首字节<2s", "priority": "高"},
   {"suggestion": "增加任务队列可视化面板", "expected_effect": "透明度提升", "priority": "中"}],
 "priority_order": "先做进度推送，再分阶段返回"}
```

---

*© 2025-2026 YYC³ Team. All Rights Reserved.*
