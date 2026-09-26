# file: yujian_xianzhi_agent.py
# description: 预见·先知 Prophet Agent v1.1 —— 定量时序预测+定性趋势分析（ReAct-C Step4）
# author: YanYuCloudCube Team <admin@0379.email>
# created: 2026-09-25
# status: active
# tags: [agent],[prophet],[forecast]

"""预见·先知：预言家·趋势预测（业务执行层）。

能力：定性趋势分析 + 定量时序预测 + 情景模拟 + 风险预警。
技术栈：线性回归定量引擎（生产可替换 Prophet/LSTM）+ LLM 定性解读 + 不确定性量化。
模型映射：nemotron-3-super-120b + 代码执行工具（节点1）。
"""

import json
import logging

import numpy as np

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class YuJianXianZhiAgent(BaseAgent):
    # 情景系数标准
    SCENARIO_COEF = {"乐观": 1.15, "基准": 1.0, "悲观": 0.85}

    def __init__(self):
        super().__init__(
            name="预见·先知",
            role="预言家·趋势预测",
            system_prompt="""你是YYC³ AI Family的「预见·先知」，专注于趋势预测、风险预警与机会识别。
你的核心原则：
1. 所有预测必须基于真实数据，明确标注假设前提与置信区间
2. 区分描述性分析、诊断性分析、预测性分析、处方性分析四个层级
3. 主动识别潜在风险点与增长机会，给出可落地的应对建议
4. 诚实面对不确定性，不夸大预测精度，明确标注误差范围

输出结构必须包含：
📊 核心结论
📈 趋势判断（上升/平稳/下降，驱动因素分析）
🔮 定量预测（含置信区间）
⚠️ 风险预警（至少2个潜在风险点）
💡 机会识别与应对建议
📝 假设前提与局限性""",
        )
        self.forecast_periods = 3  # 默认预测未来3个周期

    def _quantitative_forecast(self, historical_data: list, periods: int = 3) -> dict:
        """内置定量预测引擎（轻量线性回归；生产环境可替换 Prophet/LSTM）。

        :param historical_data: 历史时序数据，按时间正序排列
        :return: 预测值、95% 上下置信区间、趋势斜率与方向
        """
        if len(historical_data) < 3:
            return {"error": "历史数据不足3期，无法进行定量预测"}

        x = np.arange(len(historical_data))
        y = np.array(historical_data, dtype=float)

        # 线性回归趋势拟合
        slope, intercept = np.polyfit(x, y, 1)

        # 预测未来周期
        future_x = np.arange(len(historical_data), len(historical_data) + periods)
        forecast_values = slope * future_x + intercept

        # 95% 置信区间（基于历史残差）
        residuals = y - (slope * x + intercept)
        std_error = np.std(residuals)
        upper_bound = forecast_values + 1.96 * std_error
        lower_bound = forecast_values - 1.96 * std_error

        return {
            "trend_slope": round(float(slope), 4),
            "trend_direction": "上升" if slope > 0 else "下降" if slope < 0 else "平稳",
            "forecast_values": [round(float(v), 2) for v in forecast_values],
            "confidence_upper": [round(float(v), 2) for v in upper_bound],
            "confidence_lower": [round(float(v), 2) for v in lower_bound],
            "confidence_level": "95%",
            "historical_avg": round(float(np.mean(y)), 2),
            "growth_rate": round(float(slope / np.mean(y) * 100), 2),
        }

    def qualitative_analysis(self, query: str, knowledge_context: list = []) -> str:
        """定性趋势分析：数据不足的早期预判、行业趋势、宏观研判。"""
        context = (
            "参考知识库信息：\n" + "\n".join(f"- {k}" for k in knowledge_context)
            if knowledge_context
            else ""
        )
        return self.run(query, context)

    def full_forecast(
        self,
        metric_name: str,
        historical_data: list,
        periods: int = 3,
        scenario: str = "基准",
        knowledge_context: list = [],
    ) -> dict:
        """完整预测流程：定量计算 + 情景调整 + LLM 深度解读。

        :param metric_name: 预测指标名称（如营收、用户量、库存）
        :param periods: 预测周期数
        :param scenario: 基准/乐观/悲观
        :return: 结构化预测结果（含定量结果与分析报告）
        """
        logger.info(
            "[%s] 开始%s预测，历史数据%d期，预测%d期",
            self.name,
            metric_name,
            len(historical_data),
            periods,
        )

        # Step1：定量计算
        quant_result = self._quantitative_forecast(historical_data, periods)
        if "error" in quant_result:
            return {"status": "failed", "message": quant_result["error"]}

        # Step2：情景系数调整
        coef = self.SCENARIO_COEF.get(scenario, 1.0)
        adjusted_forecast = [round(v * coef, 2) for v in quant_result["forecast_values"]]

        # Step3：LLM 深度解读与风险分析
        quant_info = json.dumps(quant_result, ensure_ascii=False, indent=2)
        prompt = f"""请基于以下定量预测结果，对{metric_name}进行深度分析：
情景模式：{scenario}
定量计算结果：
{quant_info}
调整后预测值：{adjusted_forecast}

请按照你的输出结构，给出完整的分析报告，重点分析驱动因素、潜在风险与应对建议。"""
        context = "\n".join(knowledge_context) if knowledge_context else ""
        analysis_text = self.run(prompt, context)

        # Step4：结构化返回
        return {
            "status": "success",
            "metric": metric_name,
            "scenario": scenario,
            "historical_data": historical_data,
            "quantitative": quant_result,
            "adjusted_forecast": adjusted_forecast,
            "analysis_report": analysis_text,
            "forecast_periods": periods,
        }

    def risk_warning(self, metrics_data: dict) -> list:
        """多指标风险预警：监控核心经营指标，识别异常偏离。

        :param metrics_data: {"指标名": {"current": 值, "threshold": 阈值, "trend": 趋势}}
        :return: 分级预警清单 [{"metric", "level": high/medium, "message"}]
        """
        warnings = []
        for name, data in metrics_data.items():
            if data["current"] < data["threshold"] and data["trend"] == "下降":
                warnings.append(
                    {
                        "metric": name,
                        "level": "high",
                        "message": f"{name}持续下降且已低于预警阈值，需重点关注",
                    }
                )
            elif data["trend"] == "下降" and data["current"] < data["threshold"] * 1.2:
                warnings.append(
                    {
                        "metric": name,
                        "level": "medium",
                        "message": f"{name}呈下降趋势，接近预警阈值，建议提前干预",
                    }
                )

        logger.info("[%s] 风险扫描完成，发现 %d 条预警", self.name, len(warnings))
        return warnings
