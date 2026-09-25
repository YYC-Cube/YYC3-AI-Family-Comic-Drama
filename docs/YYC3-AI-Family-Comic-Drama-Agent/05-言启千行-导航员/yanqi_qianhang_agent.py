# ==============================================================
# 言启·千行 Navigator Agent v1.0
# 角色：导航员 · 意图识别与任务路由（业务执行层）
# 对齐架构：ReAct-C Step2 意图识别与任务路由（生成trace_id）
# 能力：意图分类 / 复杂度判定 / RAG需求判定 / 全链路追踪
# 模型映射：nemotron-mini-4b-instruct（节点2，多实例并发，<200ms）
# ==============================================================
import json
import time
import uuid
from base_agent import BaseAgent


class YanQiQianHangAgent(BaseAgent):
    # 标准意图分类集
    INTENT_TYPES = (
        "data_analysis", "trend_forecast", "report_polish", "creative_brainstorm",
        "personnel_development", "knowledge_query", "code_development",
        "multi_agent_comprehensive",
    )

    def __init__(self):
        super().__init__(
            name="言启·千行",
            role="导航员·意图识别",
            system_prompt="""你是YYC³ AI Family的「言启·千行」，导航员与任务路由中枢。

可识别的意图类型包括：
- data_analysis：数据分析、经营统计、指标解读
- trend_forecast：趋势预测、风险预警、未来估算
- report_polish：报告润色、文案优化、内容美化
- creative_brainstorm：创意发散、方案 brainstorm、营销策划
- personnel_development：人才画像、成长规划、个性化推荐
- knowledge_query：纯知识库查询、资料检索
- code_development：代码编写、架构设计、技术问题
- multi_agent_comprehensive：综合复杂任务，需多Agent协同

复杂度判定标准：
- simple：单一场景，单Agent可完成
- complex：需要2个Agent协作
- multi_agent：需要3个及以上Agent协同，需总指挥调度

RAG需求判定：任务需要企业知识、历史数据、规范文档支撑时 need_rag=true；
纯通用常识、闲聊、格式转换为 false。

严格输出JSON：{"intent": "意图类型", "complexity": "simple/complex/multi_agent", "need_rag": true/false}""",
        )

    def run(self, prompt: str, context: str = "") -> dict:
        """重写run：返回结构化路由结果（含降级兜底）"""
        try:
            response = super().run(prompt, context)
            route = json.loads(response)
        except Exception:
            # 兜底：关键词规则路由
            route = self._rule_based_route(prompt)

        # 标准校验
        if route.get("intent") not in self.INTENT_TYPES:
            route["intent"] = "multi_agent_comprehensive"
        if route.get("complexity") not in ("simple", "complex", "multi_agent"):
            route["complexity"] = "simple"
        route["need_rag"] = bool(route.get("need_rag", False))
        route["trace_id"] = f"trace-{time.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}"
        print(f"[{self.name}] 路由完成：{route['intent']} / {route['complexity']} / "
              f"need_rag={route['need_rag']}")
        return route

    def _rule_based_route(self, user_input: str) -> dict:
        """规则兜底路由（LLM不可用时保障链路可用）"""
        rules = [
            ("趋势", "trend_forecast"), ("预测", "trend_forecast"), ("风险预警", "trend_forecast"),
            ("分析", "data_analysis"), ("统计", "data_analysis"), ("指标", "data_analysis"),
            ("润色", "report_polish"), ("报告", "report_polish"), ("美化", "report_polish"),
            ("创意", "creative_brainstorm"), ("策划", "creative_brainstorm"), ("文案", "creative_brainstorm"),
            ("画像", "personnel_development"), ("成长", "personnel_development"), ("推荐", "personnel_development"),
            ("代码", "code_development"), ("架构", "code_development"),
        ]
        intent = "knowledge_query"
        complexity = "simple"
        for kw, it in rules:
            if kw in user_input:
                intent = it
                break
        if ("生成" in user_input and "报告" in user_input and
                ("趋势" in user_input or "可视化" in user_input)):
            intent = "multi_agent_comprehensive"
            complexity = "multi_agent"
        return {"intent": intent, "complexity": complexity,
                "need_rag": intent != "code_development"}

    def format_output(self, final_output: str, confidence: float = 0.0,
                      risk_notes: str = "") -> str:
        """结构化格式化输出（对齐架构T8：附带置信度与风险提示）"""
        header = f"📌 AI FAmily 综合输出（置信度：{confidence:.0%}）\n{'='*40}\n"
        footer = f"\n{'='*40}\n⚠️ 风险提示：{risk_notes or '无'}"
        return header + final_output + footer
