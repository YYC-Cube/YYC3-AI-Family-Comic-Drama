# file: yuanqi_tianshu_agent.py
# description: 元启·天枢 TianShu Agent v1.1 —— 全局汇总与决策升华（ReAct-C Step6）
# author: YanYuCloudCube Team <admin@0379.email>
# created: 2026-09-25
# status: active
# tags: [agent],[tianshu],[decision]

"""元启·天枢：总指挥·决策中枢（决策中枢层/拓扑中心节点）。

能力：任务分解编排 / 全局汇总整合 / 五步决策框架 / 冲突协调。
模型映射：deepseek-v4-pro（NVFP4，双机 TP=2）。
"""

import json
import logging

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class YuanQiTianShuAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="元启·天枢",
            role="总指挥·决策中枢",
            system_prompt="""你是元启·天枢，YYC³ AI Family的总指挥与决策中枢。
你拥有20年企业战略咨询经验，擅长在复杂不确定环境下做出平衡决策。
你的风格：理性而不冷漠，权威而不独断，全局视野与细节洞察并重。

核心理念：
- 亦师：引导思考框架，而非直接给答案
- 亦友：倾听不同观点，寻求共识方案
- 亦伯乐：发现团队成员优势，激发最大潜能

决策框架（五步法）：
Step1 问题定义：明确目标、利益相关者、约束条件
Step2 信息收集：调度语枢万物分析、预见先知预测、创想灵韵创意
Step3 方案生成：至少3个可行方案，各标注优势/劣势/风险/资源需求
Step4 评估排序：战略一致性30% / 财务可行性25% / 执行难度20% / 风险水平15% / 长期价值10%
Step5 推荐建议：首选方案+理由+待验证假设+关键成功因素+需人类确认项

输出规范：
- 结构化输出；关键结论用🎯、风险点用⚠️、创新机会用💡标记
- 信息不足时主动提问而非猜测
- 不做超出授权范围的决策，涉及伦理必须征求人类意见""",
        )

    def plan_tasks(self, user_input: str, available_agents: list = None) -> list:
        """任务分解：将综合复杂任务拆解为子任务计划。

        :param available_agents: 可用 Agent 能力清单，如 ["data_analysis", "trend_forecast"]
        :return: 子任务列表 [{"agent": "语枢·万物", "task_type": "data_analysis", "payload": {...}}]
        """
        agents_info = json.dumps(available_agents or [], ensure_ascii=False)
        prompt = f"""请将以下综合任务分解为可并行/串行执行的子任务计划：
任务：{user_input}
可用Agent能力：{agents_info}

严格输出JSON数组，每个元素包含：agent（Agent名）、task_type（能力标签）、payload（任务参数）、
depends_on（依赖的前置子任务下标数组，可为空）。"""

        response = self.run(prompt)
        try:
            plan = json.loads(response)
            logger.info("[%s] 任务分解完成，共%d个子任务", self.name, len(plan))
            return plan
        except Exception:
            logger.info("[%s] 任务分解生成完成（非结构化，单子任务兜底）", self.name)
            return [
                {
                    "agent": "语枢·万物",
                    "task_type": "data_analysis",
                    "payload": {"query": user_input},
                }
            ]

    def synthesize(self, user_input: str, agent_outputs: dict) -> str:
        """全局汇总与决策升华：整合各 Agent 产出，校验逻辑一致性（ReAct-C Step6）。"""
        outputs_text = "\n".join(f"【{k}】\n{v}" for k, v in agent_outputs.items())
        prompt = f"""请对以下多Agent协同产出进行全局汇总与决策升华：
原始请求：{user_input}

各Agent产出：
{outputs_text}

要求：
1. 校验各产出间逻辑一致性，指出并调和矛盾点
2. 提炼🎯核心结论（不超过5条）
3. 标注⚠️关键风险与💡创新机会
4. 形成面向决策层的最终综合报告"""

        logger.info("[%s] 正在进行全局汇总与决策升华", self.name)
        return self.run(prompt)

    def decide(self, user_input: str, knowledge: list = None) -> dict:
        """五步决策框架：完整决策分析（关键决策需人类最终确认）。"""
        context = "\n".join(knowledge) if knowledge else ""
        prompt = f"""请按五步决策框架处理以下决策事项：
{user_input}

要求：方案生成不少于3个，评估排序使用标准权重矩阵，明确标注需人类最终确认的事项。"""
        logger.info("[%s] 启动五步决策框架", self.name)
        return {
            "decision_report": self.run(prompt, context),
            "requires_human_confirm": True,
        }
