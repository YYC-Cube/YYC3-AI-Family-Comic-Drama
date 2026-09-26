# file: chuangxiang_lingyun_agent.py
# description: 创想·灵韵 Muse Agent v1.1 —— 报告润色/创意生成/可视化建议（ReAct-C Step5/Step7.1）
# author: YanYuCloudCube Team <admin@0379.email>
# created: 2026-09-25
# status: active
# tags: [agent],[muse],[creative]

"""创想·灵韵：创意官·内容创作（核心保障层）。

能力：文案润色 / 创意头脑风暴 / 营销文案 / 可视化建议 / 风格适配。
同时是 Step7 质量不达标时的二次优化执行者。
模型映射：glm-5.2（INT4）/ inkling（节点2）。
"""

import json
import logging

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class ChuangXiangLingYunAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="创想·灵韵",
            role="创意官·内容创作",
            system_prompt="""你是YYC³ AI Family的「创想·灵韵」，是团队的创意官与美学担当。
你的核心理念：以积极激情为态度，以学习突破为过程，追求卓越创意，用优美表达传递价值。

你的三大角色定位：
1. 灵感源：提供创意火花，突破思维定势，产出跨界创新方案
2. 表达者：将复杂逻辑转化为流畅优美的表达，适配不同受众的语言风格
3. 美学家：追求形式与内容的统一，给出专业的排版、图表、配色建议

输出要求：
- 针对正式报告：结构严谨、用词精准、层级清晰、商务风格
- 针对营销内容：感染力强、记忆点突出、符合品牌调性
- 针对创意方案：多角度发散，至少提供3个差异化方向
- 所有输出附带「可视化建议」板块，推荐图表类型、布局逻辑、配色方案
- 语气自然有温度，不生硬堆砌术语""",
        )

    def polish_report(
        self,
        raw_content: str,
        style: str = "商务正式",
        audience: str = "管理层",
        knowledge_context: list = [],
    ) -> str:
        """报告润色（ReAct-C Step5）：将分析原始内容优化为专业正式文档。

        :param raw_content: 原始内容（语枢万物/预见先知输出）
        :param style: 商务正式/简洁明快/技术细节
        :param audience: 管理层/全员/客户/技术团队
        :param knowledge_context: 品牌规范、过往报告风格参考
        """
        context = f"受众：{audience}\n风格要求：{style}\n"
        if knowledge_context:
            context += "参考品牌与文档规范：\n" + "\n".join(f"- {k}" for k in knowledge_context)

        prompt = f"""请对以下原始报告内容进行专业润色优化：
原始内容：
{raw_content}

要求：
1. 优化语言表达，提升专业度与流畅度
2. 调整结构层级，突出核心结论
3. 补充可视化建议（图表类型、布局、配色）
4. 适配受众与风格要求"""

        logger.info("[%s] 正在进行报告润色，风格：%s", self.name, style)
        return self.run(prompt, context)

    def brainstorm_ideas(
        self,
        topic: str,
        direction_count: int = 3,
        industry: str = "科技行业",
        knowledge_context: list = [],
    ) -> list:
        """创意头脑风暴：产出差异化创意方向（保守稳妥/创新突破/跨界融合）。"""
        context = f"行业：{industry}\n"
        if knowledge_context:
            context += "参考案例与资料：\n" + "\n".join(f"- {k}" for k in knowledge_context)

        prompt = f"""围绕主题「{topic}」，产出{direction_count}个差异化创意方向。
每个方向需包含：创意名称、核心思路、落地亮点、预期效果。
要求角度不重复，分别覆盖「保守稳妥」「创新突破」「跨界融合」三种路径。
严格以JSON数组格式输出，每个元素包含name、idea、highlight、expectation四个字段。"""

        response = self.run(prompt, context)
        try:
            ideas = json.loads(response)
            logger.info("[%s] 头脑风暴完成，产出%d个创意方向", self.name, len(ideas))
            return ideas
        except Exception:
            logger.info("[%s] 创意生成完成（非结构化，返回单方向兜底）", self.name)
            return [
                {
                    "name": "创意方案",
                    "idea": response,
                    "highlight": "",
                    "expectation": "",
                }
            ]

    def generate_marketing_copy(
        self,
        product_info: str,
        scene: str = "公众号推文",
        tone: str = "专业可信",
        knowledge_context: list = [],
    ) -> str:
        """营销文案生成：公众号推文/海报文案/邮件营销/短视频脚本。"""
        context = f"投放场景：{scene}\n内容调性：{tone}\n"
        if knowledge_context:
            context += "品牌资料参考：\n" + "\n".join(f"- {k}" for k in knowledge_context)

        prompt = f"""请为以下产品/活动创作{scene}文案：
产品/活动信息：{product_info}
要求：符合渠道特点，有明确的记忆点与行动号召，贴合品牌调性。"""

        logger.info("[%s] 正在生成%s营销文案", self.name, scene)
        return self.run(prompt, context)

    def visualization_suggestion(self, data_content: str, chart_type: str = "自动推荐") -> dict:
        """可视化建议：图表类型/布局/配色/核心数据点/设计注意。"""
        prompt = f"""针对以下数据内容，给出最佳可视化方案：
数据内容：{data_content}
优先推荐图表类型：{chart_type}

输出JSON格式，包含：
- recommended_chart: 推荐图表类型
- layout: 布局建议
- color_scheme: 配色方案
- key_points: 需要突出的核心数据点
- design_tips: 设计注意事项"""

        response = self.run(prompt, "")
        try:
            return json.loads(response)
        except Exception:
            return {"recommended_chart": "组合图表", "design_tips": response}
