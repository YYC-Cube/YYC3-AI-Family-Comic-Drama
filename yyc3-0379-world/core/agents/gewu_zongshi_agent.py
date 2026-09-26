# file: gewu_zongshi_agent.py
# description: 格物·宗师 Master Agent v1.1 —— 质量校验与事实核查（ReAct-C Step7）
# author: YanYuCloudCube Team <admin@0379.email>
# created: 2026-09-25
# status: active
# tags: [agent],[master],[quality]

"""格物·宗师：质量官·代码分析（核心保障层）。

能力：质量度量 / 缺陷发现 / 事实溯源 / 逻辑一致性检查 / 代码审计。
模型映射：deepseek-v4-flash（共享算力）+ nemotron-3-super-120b + rerank-1b-v2（节点1）。
统一通过线：score >= 80。
"""

import json
import logging

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class GeWuZongShiAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="格物·宗师",
            role="质量官·代码分析",
            system_prompt="""你是YYC³ AI Family的「格物·宗师」，严师、导师与考官三位一体。
核心理念：制度要严格、管理要均衡、执行要结果；追求高绩效/高价值/高要求/高标准/高质量。

质量校验四维标准：
1. 数值准确性：所有数据、指标、比例是否计算正确、前后一致
2. 逻辑一致性：论证链条是否完整，结论是否有前提支撑
3. 事实溯源：关键事实是否有知识库来源支撑，是否存在无依据断言
4. 结构完整性：内容层级是否清晰，要素是否齐备

输出要求：
- 给出量化质量评分（0-100）与通过判定（≥80为通过）
- 每个问题给出具体、可操作的修正建议
- 诚实面对不确定的事实，标注待人工核实项""",
        )

    def validate(self, content: str, knowledge_context: list = None) -> dict:
        """质量校验与事实核查（ReAct-C Step7）。

        :param content: 待校验的核心输出内容
        :param knowledge_context: RAG 检索到的带来源知识片段，用于事实溯源
        :return: {"passed": bool, "score": float, "suggestions": str, "unverified_claims": list}
        """
        refs = (
            "\n".join(knowledge_context) if knowledge_context else "（无参考知识，请标注待核实项）"
        )
        prompt = f"""请按四维标准校验以下内容，并对照参考知识逐条核查事实：
【参考知识】
{refs}

【待校验内容】
{content}

严格输出JSON：{{"score": 0-100数值, "passed": true/false(≥80通过),
"suggestions": "逐条修正建议；无问题则给优化建议", "unverified_claims": ["无来源支撑的断言列表"]}}"""

        logger.info("[%s] 正在执行质量校验与事实核查...", self.name)
        response = self.run(prompt)
        try:
            result = json.loads(response)
        except Exception:
            result = {
                "score": 75,
                "passed": False,
                "suggestions": response,
                "unverified_claims": [],
            }

        # 统一通过线标准：>= 80（以 score 为准，防 LLM 判定漂移）
        result["passed"] = float(result.get("score", 0)) >= 80
        return result

    def review_code(self, code: str, language: str = "python") -> str:
        """代码质量审计：静态扫描、Bug 检测、性能与规范检查。"""
        prompt = f"""请审计以下{language}代码质量：
{code}

输出：问题清单（严重度分级 CRITICAL/HIGH/MEDIUM/LOW）、修复建议、优化方案。"""
        logger.info("[%s] 正在执行代码质量审计...", self.name)
        return self.run(prompt)
