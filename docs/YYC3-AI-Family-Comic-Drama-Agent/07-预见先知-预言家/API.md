# 07 预见·先知 接口文档

> 版本 v1.0.0 | 更新 2026-09-24 | 代码 [yujian_xianzhi_agent.py](yujian_xianzhi_agent.py) | 继承 [BaseAgent](../00-公共基座/API.md)
> 示例前提：所有代码文件位于同一 Python 包目录

## 一、接口清单

| 接口名称 | 签名 | 功能简述 |
| -------- | ---- | -------- |
| `full_forecast` | `(metric_name, historical_data, periods=3, scenario="基准", knowledge_context=[]) -> dict` | 完整预测（定量+情景+LLM解读，Step4） |
| `qualitative_analysis` | `(query, knowledge_context=[]) -> str` | 定性趋势分析 |
| `risk_warning` | `(metrics_data) -> list[dict]` | 多指标风险预警 |
| `_quantitative_forecast` | `(historical_data, periods=3) -> dict` | 定量预测引擎（内部方法） |

## 二、接口详情

### 2.1 `full_forecast` — 完整预测

**功能描述**：四步流水线——定量回归计算 → 情景系数调整（乐观1.15/基准1.0/悲观0.85）→ LLM 深度解读 → 结构化返回；95% 置信区间基于历史残差。

**请求参数**：

| 参数名 | 类型 | 必填 | 描述 |
| ------ | ---- | ---- | ---- |
| metric_name | str | 是 | 预测指标名（营收/用户量/库存） |
| historical_data | list[float] | 是 | 历史时序数据，时间正序，**≥3期** |
| periods | int | 否 | 预测周期数，默认3 |
| scenario | str | 否 | 基准/乐观/悲观，默认基准 |
| knowledge_context | list[str] | 否 | 知识库上下文 |

**返回参数**：

| 参数名 | 类型 | 描述 |
| ------ | ---- | ---- |
| status | str | success / failed |
| metric / scenario / historical_data | str/str/list | 输入回显 |
| quantitative | dict | 定量结果（trend_slope/trend_direction/forecast_values/confidence_upper/confidence_lower/confidence_level/growth_rate） |
| adjusted_forecast | list[float] | 情景调整后预测值 |
| analysis_report | str | LLM 分析报告（📊📈🔮⚠️💡📝 结构） |
| forecast_periods | int | 预测周期数 |
| message | str | 仅 failed 时返回失败原因 |

**错误码**：YYC3-AGT-4001（历史数据不足3期，`status=failed`）

**调用示例**：

```python
from yujian_xianzhi_agent import YuJianXianZhiAgent

prophet = YuJianXianZhiAgent()

# 场景1：基准营收预测
result = prophet.full_forecast(
    metric_name="季度营收", historical_data=[120, 135, 150, 168, 192, 220],
    periods=3, scenario="基准")
print(result["quantitative"]["forecast_values"])
print(result["adjusted_forecast"])

# 场景2：数据不足 → 失败
fail = prophet.full_forecast("新指标", [100, 110])
# 预期返回：{'status': 'failed', 'message': '历史数据不足3期，无法进行定量预测'}
```

预期返回（场景1定量部分）：

```json
{
  "trend_slope": 19.4, "trend_direction": "上升",
  "forecast_values": [251.2, 270.6, 290.0],
  "confidence_upper": [263.05, 282.45, 301.85],
  "confidence_lower": [239.35, 258.75, 278.15],
  "confidence_level": "95%",
  "historical_avg": 164.17, "growth_rate": 11.82
}
```

### 2.2 `qualitative_analysis` — 定性趋势分析

**请求参数**：`query`（str，必填，趋势问题）、`knowledge_context`（list，选填）

**返回参数**：str（📊📈🔮⚠️💡📝 结构化定性研判）

**调用示例**：

```python
view = prophet.qualitative_analysis("下季度ToB市场销售趋势如何")
```

预期返回：含「⚠️ 风险预警（≥2个）」与「📝 假设前提」的趋势研判文本

### 2.3 `risk_warning` — 多指标风险预警

**请求参数**：

| 参数名 | 类型 | 必填 | 描述 |
| ------ | ---- | ---- | ---- |
| metrics_data | dict | 是 | `{"指标名": {"current": 值, "threshold": 阈值, "trend": 趋势}}` |

**返回参数**：list[dict]，元素含 `metric`（指标名）/ `level`（high/medium）/ `message`（预警说明）

**判定标准**：低于阈值且下降 → high；下降且接近阈值（<1.2×阈值）→ medium

**调用示例**：

```python
warnings = prophet.risk_warning({
    "毛利率": {"current": 55, "threshold": 60, "trend": "下降"},
    "客户续费率": {"current": 88, "threshold": 85, "trend": "上升"},
})
```

预期返回：

```json
[{"metric": "毛利率", "level": "high",
  "message": "毛利率持续下降且已低于预警阈值，需重点关注"}]
```

---

*© 2025-2026 YYC³ Team. All Rights Reserved.*
