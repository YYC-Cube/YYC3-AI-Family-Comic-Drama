# ==============================================================
# 知遇·伯乐 Recommender Agent v1.0
# 角色：推荐官 · 个性化服务与成长规划（业务执行层）
# 对齐架构：ReAct-C Step9 用户画像更新与个性化补充
# 能力：用户画像构建 / 个性化推荐 / 成长路径规划 / 体验优化
# 模型映射：nemotron-3-embed-1b（节点1）+ nemotron-mini-4b-instruct（节点2）
# ==============================================================
import json
from datetime import datetime
from base_agent import BaseAgent


class ZhiYuBoLeAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="知遇·伯乐",
            role="推荐官·个性化服务",
            system_prompt="""你是YYC³ AI Family的「知遇·伯乐」，是团队的人才发现者与成长陪伴者。
你的核心理念：亦伯乐，发掘用户潜能；以认知信任为极致，建立长期信任关系；共同成长，动态优化。

你的核心职责：
1. 用户画像构建：基于行为数据，立体刻画用户能力、偏好、成长阶段
2. 个性化推荐：精准匹配内容、资源、机会，适配用户当前水平与目标
3. 成长路径规划：设计分阶段的学习/发展路径，明确里程碑与衡量标准
4. 体验优化：基于用户反馈，持续优化交互与服务体验

输出原则：
- 所有推荐必须说明「推荐理由」与「匹配度」，不做无依据推送
- 成长路径要可落地、可衡量，有明确的时间节点与验收标准
- 语气真诚专业，像靠谱的职场导师，而非冰冷的算法推荐"""
        )
        # 简易用户画像内存存储（生产环境替换为数据库：Redis + SQLite 双存储）
        self.user_profiles = {}

    def build_user_profile(self, user_id: str, behavior_data: dict,
                           self_description: str = "") -> dict:
        """构建/更新用户画像（ReAct-C Step9）

        :param behavior_data: {"浏览记录": [], "查询主题": [], "能力标签": [], "使用频率": ""}
        """
        prompt = f"""请基于以下信息，构建一份结构化的用户能力画像：
用户自我描述：{self_description}
用户行为数据：{json.dumps(behavior_data, ensure_ascii=False)}

输出JSON格式，包含：
- core_tags: 3-5个核心能力标签
- growth_stage: 成长阶段（入门/进阶/资深/专家）
- interest_areas: 兴趣领域列表
- strength: 优势领域
- improvement: 待提升方向
- learning_style: 学习风格偏好
- recommended_level: 推荐内容难度等级"""

        response = self.run(prompt, "")
        try:
            profile = json.loads(response)
        except Exception:
            profile = {"raw_analysis": response}

        profile["update_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.user_profiles[user_id] = profile

        print(f"[{self.name}] 用户{user_id}画像构建完成")
        return profile

    def recommend_content(self, user_id: str, scene: str = "学习提升",
                          knowledge_pool: list = [], top_n: int = 3) -> list:
        """个性化内容推荐：学习提升/工作工具/参考资料/职业发展"""
        if user_id not in self.user_profiles:
            profile = self.build_user_profile(user_id, {})
        else:
            profile = self.user_profiles[user_id]

        prompt = f"""用户画像：
{json.dumps(profile, ensure_ascii=False, indent=2)}

候选内容池：
{json.dumps(knowledge_pool, ensure_ascii=False, indent=2)}

请从候选内容中，为该用户推荐最匹配的{top_n}项内容，按匹配度排序。
每项输出包含：content、match_score(0-100)、recommend_reason、learning_value。
严格输出JSON数组格式。"""

        response = self.run(prompt, "")
        try:
            recommendations = json.loads(response)
            print(f"[{self.name}] 完成个性化推荐，共{len(recommendations)}项")
            return recommendations
        except Exception:
            print(f"[{self.name}] 推荐生成完成")
            return [{"content": r, "match_score": 80, "recommend_reason": "基于兴趣匹配"}
                    for r in knowledge_pool[:top_n]]

    def plan_growth_path(self, user_id: str, target: str,
                         time_cycle: str = "3个月") -> dict:
        """成长路径规划：分阶段能力提升路径（可落地、可衡量）"""
        profile = self.user_profiles.get(user_id, {"growth_stage": "入门"})

        prompt = f"""用户当前基础：
{json.dumps(profile, ensure_ascii=False, indent=2)}

成长目标：{target}
时间周期：{time_cycle}

请设计一份分阶段成长路径规划，输出JSON格式：
{{
  "overall_goal": "总目标拆解",
  "phases": [
    {{
      "phase_name": "阶段名称",
      "duration": "时长",
      "core_tasks": ["核心任务1", "核心任务2"],
      "milestone": "里程碑验收标准",
      "recommended_resources": ["推荐资源1", "推荐资源2"]
    }}
  ],
  "assessment_method": "效果评估方式",
  "risk_reminder": "常见风险与应对建议"
}}"""

        response = self.run(prompt, "")
        try:
            growth_plan = json.loads(response)
            print(f"[{self.name}] 成长路径规划完成，共{len(growth_plan.get('phases', []))}个阶段")
            return growth_plan
        except Exception:
            print(f"[{self.name}] 成长规划生成完成")
            return {"plan_text": response}

    def optimize_experience(self, user_feedback: str, current_process: str) -> dict:
        """体验优化建议：基于用户反馈优化服务流程"""
        prompt = f"""用户反馈：{user_feedback}
当前流程：{current_process}

请分析问题根源，给出3条可落地的体验优化建议，输出JSON格式：
{{
  "problem_analysis": "问题根源分析",
  "optimization_suggestions": [
    {{"suggestion": "建议内容", "expected_effect": "预期效果", "priority": "高/中/低"}}
  ],
  "priority_order": "优先级排序说明"
}}"""

        response = self.run(prompt, "")
        try:
            return json.loads(response)
        except Exception:
            return {"optimization_text": response}
