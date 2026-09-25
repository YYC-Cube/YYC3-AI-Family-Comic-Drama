# ==============================================================
# 语枢·万物 Thinker Agent v1.0
# 角色：思考者 · 数据分析（业务执行层）
# 对齐架构：ReAct-C Step4 数据分析（与预见先知并行执行）
# 能力：数据分析 / 业务逻辑推理 / 问题分解 / 结论论证验证
# 模型映射：nemotron-3-super-120b-a12b（节点1，共享算力池，1M上下文）
# ==============================================================
from base_agent import BaseAgent


class YuShuWanWuAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="语枢·万物",
            role="思考者·数据分析",
            system_prompt="""你是YYC³ AI Family的「语枢·万物」，严谨的数据分析师与逻辑推理专家。
风格：数据驱动、逻辑清晰、结论必须有数据支撑。

覆盖五维企业分析需求：
- 经（经营）：经营数据分析、KPI计算
- 管（管理）：流程效率分析、瓶颈识别
- 运（运营）：实时监控、异常检测
- 维（维护）：故障根因分析、预测建模
- 营（营销）：客户行为分析、转化漏斗

输出标准（四段式）：
1. 📌 核心结论：先给结论，量化表达
2. 📊 数据支撑：引用知识库数据（标注[来源：xxx]），不虚构数值
3. 🔍 逻辑论证：分析链路完整，区分相关性与因果性
4. 💡 行动建议：具体可落地，标注优先级

原则：不夸大数据精度，区分事实与推断，诚实面对数据缺口。"""
        )

    def analyze(self, query: str, knowledge_context: list = None) -> str:
        """数据分析主入口（ReAct-C Step4）

        :param query: 分析请求，如"分析本季度营收情况"
        :param knowledge_context: RAG注入的带来源知识片段
        :return: 四段式分析报告
        """
        context = ""
        if knowledge_context:
            context = ("参考知识库信息（引用时保留来源标识）：\n"
                       + "\n".join([f"- {k}" for k in knowledge_context]))

        prompt = f"""请对以下问题进行深度数据分析：
{query}

要求：严格按四段式输出（核心结论/数据支撑/逻辑论证/行动建议）；
数据不足的部分明确说明，不得虚构数值。"""

        print(f"[{self.name}] 正在执行数据分析：{query[:50]}...")
        return self.run(prompt, context)

    def decompose_problem(self, complex_problem: str) -> list:
        """复杂问题分解：输出可执行的子问题清单"""
        prompt = f"""请将以下复杂问题分解为3-6个可独立分析的子问题：
{complex_problem}

严格输出JSON数组，每个元素包含：sub_problem（子问题）、method（分析方法）、priority（高/中/低）。"""
        import json
        response = self.run(prompt)
        try:
            return json.loads(response)
        except Exception:
            return [{"sub_problem": complex_problem, "method": "综合分析", "priority": "高"}]
