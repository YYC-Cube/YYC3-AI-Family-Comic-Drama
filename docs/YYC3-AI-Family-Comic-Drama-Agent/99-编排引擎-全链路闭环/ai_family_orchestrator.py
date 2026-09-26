# ==============================================================
# AI FAmily 全链路协同编排引擎 v2.1（闭环审核修复版）
# 整合全部 8 位 Agent + 公共 RAG，实现 ReAct-C 九步全链路闭环
# 链路：输入安全→意图路由→知识检索→任务执行→润色→汇总
#       →质量校验→输出审计→个性化补充
# v2.1 修复（闭环审核 2026-09-24）：
#   F1 execute 新增 scene 参数：A综合/B分析/C创作/D恶意/E匿名/F预测
#      （对齐总纲 §5 场景分支标准 A-F）
#   F2 Step3 RAG 检索降级保护：Milvus 不可达→无RAG直答（YYC3-AGT-5001）
#   F3 Step7 二次优化后自动复检（≤2轮），最终以复检结果为准
#   F4 Step2 路由产生 trace_id 后全链透传（steps 记录携带）
#   F5 Step4 语枢+预见真并行（ThreadPoolExecutor，对齐总纲 §5 性能要求）
#   F6 blocked 输出同样返回 trace_id（审计留痕不缺 trace）
# 部署：与各 Agent 目录代码置于同一包目录（共享 base_agent 等模块）
# 依赖：无新增第三方依赖（concurrent.futures 为标准库）
# ==============================================================
from concurrent.futures import ThreadPoolExecutor

import json

from base_agent import BaseAgent
from yuanqi_tianshu_agent import YuanQiTianShuAgent
from zhiyun_shouhu_agent import ZhiYunShouHuAgent
from gewu_zongshi_agent import GeWuZongShiAgent
from chuangxiang_lingyun_agent import ChuangXiangLingYunAgent
from yanqi_qianhang_agent import YanQiQianHangAgent
from yushu_wanwu_agent import YuShuWanWuAgent
from yujian_xianzhi_agent import YuJianXianZhiAgent
from zhiyu_bole_agent import ZhiYuBoLeAgent
from milvus_retriever import MilvusRetriever


class AIFamilyOrchestrator:
    """AI FAmily 全链路协同编排引擎 v2.1（闭环审核修复版）"""

    MAX_QC_ROUNDS = 2  # 质检二次优化最大轮次（防死循环，超过即放行并标记）

    def __init__(self):
        # ===== 第一层：决策中枢 =====
        self.yuanqi = YuanQiTianShuAgent()

        # ===== 第二层：核心保障 =====
        self.zhiyun = ZhiYunShouHuAgent()            # 安全官
        self.gewu = GeWuZongShiAgent()               # 质量官
        self.chuangxiang = ChuangXiangLingYunAgent() # 创意官

        # ===== 第三层：业务执行 =====
        self.yanqi = YanQiQianHangAgent()            # 导航员·意图识别
        self.yushu = YuShuWanWuAgent()               # 思考者·数据分析
        self.yujian = YuJianXianZhiAgent()           # 预言家·趋势预测
        self.zhiyu = ZhiYuBoLeAgent()                # 伯乐·个性化推荐

        # ===== 公共能力 =====
        self.retriever = MilvusRetriever()           # 知识库检索

    def _get_knowledge(self, query: str, top_k: int = 5, category: str = None) -> tuple:
        """统一知识检索入口（Step3，带降级保护）

        :return: (格式化上下文 list, degraded bool)
                 Milvus 不可达时返回 ([], True)，走无RAG直答（YYC3-AGT-5001）
        """
        try:
            docs = self.retriever.search(query, top_k=top_k, category_filter=category)
            return [f"[来源：{d['source']}] {d['content']}" for d in docs], False
        except Exception as e:
            print(f"[Step3] RAG降级（YYC3-AGT-5001）：{e}，切换无RAG直答")
            return [], True

    def execute(self, user_input: str, user_id: str = "default_user",
                scene: str = None) -> dict:
        """完整全链路执行入口（ReAct-C 九步闭环）

        :param user_input: 用户请求
        :param user_id: 用户标识，用于个性化推荐（Step9）；default_user 跳过
        :param scene: 场景分支标准 A-F（对齐总纲 §5）：
                      A综合（默认，九步全开）｜B分析（裁剪5/6）｜C创作（4只走创想）
                      D恶意（Step1拦截）｜E匿名（跳过Step9）｜F预测（4只走预见）
                      None 时按意图自动路由
        """
        print("=" * 60)
        print(f"[系统] 用户[{user_id}]请求：{user_input}")
        print("=" * 60)

        result = {
            "user_id": user_id,
            "user_input": user_input,
            "scene": scene,
            "steps": [],            # 全链路步骤记录（审计依据）
            "agent_outputs": {},
            "final_output": "",
            "status": "success",
            "trace_id": None,
        }

        # ========== Step1：智云·守护 输入安全三级过滤 ==========
        print("\n[Step1] 输入安全三级过滤...")
        safety_check = self.zhiyun.check_input(user_input)
        result["steps"].append({"step": "input_safety", "result": safety_check})
        if not safety_check["safe"]:
            result["status"] = "blocked"
            result["final_output"] = f"请求已拦截：{safety_check['risk']}"
            return result  # 场景D：拦截即返（无trace，后续Step2才生成）

        # ========== Step2：言启·千行 意图识别与任务路由 ==========
        print("\n[Step2] 言启·千行 意图识别与任务路由...")
        route_result = self.yanqi.run(user_input)
        result["steps"].append({"step": "intent_routing", "result": route_result})
        intent = route_result["intent"]
        complexity = route_result["complexity"]
        need_rag = route_result["need_rag"]
        trace_id = route_result["trace_id"]
        result["trace_id"] = trace_id  # F6：全链路追踪标识上浮到结果顶层

        # ========== Step3：公共RAG 知识检索与上下文注入（F2 降级保护） ==========
        knowledge, rag_degraded = ([], False)
        if need_rag and scene != "C":  # C创作场景纯发散，跳过RAG
            print("\n[Step3] 知识库语义检索...")
            knowledge, rag_degraded = self._get_knowledge(user_input)
            result["steps"].append({"step": "rag_retrieve",
                                    "result_count": len(knowledge),
                                    "degraded": rag_degraded})

        # ========== Step4：分场景任务执行（F5 语枢+预见真并行） ==========
        print("\n[Step4] 任务执行...")
        outputs = result["agent_outputs"]

        # —— 场景分支裁剪：显式 scene 优先于意图路由（对齐总纲 §5） ——
        scene = scene or {
            "data_analysis": "B", "trend_forecast": "F",
            "creative_brainstorm": "C",
        }.get(intent, "A" if complexity == "multi_agent" else "B")

        # —— F5：语枢+预见 并行执行（场景A/F；场景B只走语枢） ——
        if scene in ("A", "F"):
            with ThreadPoolExecutor(max_workers=2) as pool:
                fut_analysis = pool.submit(self.yushu.analyze, user_input, knowledge)
                if scene == "F":
                    fut_forecast = pool.submit(
                        self.yujian.full_forecast, "核心指标",
                        [120, 135, 150, 168, 192, 220], 3, "基准", knowledge)
                outputs["yushu_analysis"] = fut_analysis.result()
                if scene == "F":
                    outputs["yujian_forecast"] = fut_forecast.result()["analysis_report"]
        elif scene == "B":
            outputs["yushu_analysis"] = self.yushu.analyze(user_input, knowledge)
        elif scene == "C":
            outputs["creative_ideas"] = self.chuangxiang.brainstorm_ideas(
                user_input, direction_count=3, knowledge_context=knowledge)

        # —— 场景专属补充（按意图叠加，不与场景分支冲突） ——
        if intent == "personnel_development" and user_id != "default_user":
            outputs["user_profile"] = self.zhiyu.build_user_profile(
                user_id, {}, user_input)
            outputs["growth_plan"] = self.zhiyu.plan_growth_path(
                user_id, user_input, "3个月")

        # —— 场景A：综合任务由元启·天枢总指挥调度 ——
        if scene == "A":
            print("[Step4.1] 元启·天枢 启动多Agent协同调度...")
            outputs["creative_optimize"] = self.chuangxiang.polish_report(
                outputs["yushu_analysis"], knowledge_context=knowledge)
            outputs["yuanqi_summary"] = self.yuanqi.synthesize(user_input, outputs)

        # ========== Step5：创想·灵韵 润色（B/F场景；A/C/F4已含或裁剪） ==========
        if scene in ("B", "F"):
            core_for_polish = outputs.get("yushu_analysis", "")
            if scene == "F":
                core_for_polish += f"\n\n预测补充：{outputs.get('yujian_forecast', '')}"
            outputs["polished_report"] = self.chuangxiang.polish_report(
                core_for_polish, style="商务正式", audience="管理层",
                knowledge_context=knowledge)

        # ========== Step6：元启·天枢 全局汇总（A 已含；B/C/F 裁剪） ==========
        # G2-002 修订（2026-09-27）：B 场景按总纲 §五「裁剪 6」不再产出
        # yuanqi_summary（此前代码与注释/规格矛盾，由 YYC3-60 G2 首跑发现）

        # ========== Step7：格物·宗师 质量校验与事实核查（F3 闭环复检） ==========
        print("\n[Step7] 格物·宗师 质量校验...")
        core_content = (outputs.get("yuanqi_summary")
                        or outputs.get("polished_report")
                        or outputs.get("yushu_analysis")
                        or outputs.get("creative_ideas", ""))
        if not isinstance(core_content, str):
            # G2-006 首跑发现：场景C 的 creative_ideas 为结构化列表（JSON 数组契约），
            # 质检/审计要求 str——统一次序化后再进入 Step7/8
            core_content = json.dumps(core_content, ensure_ascii=False)
        quality_result = self.gewu.validate(core_content, knowledge)
        qc_rounds = 1
        # F3：不达标→二次优化→复检，直至达标或达轮次上限
        while not quality_result["passed"] and qc_rounds < self.MAX_QC_ROUNDS:
            print(f"[Step7.{qc_rounds + 1}] 质量不达标，执行二次优化（第{qc_rounds + 1}轮）...")
            optimize_prompt = (f"请根据以下建议修正内容：\n"
                               f"{quality_result['suggestions']}\n\n原内容：\n{core_content}")
            core_content = self.chuangxiang.polish_report(
                optimize_prompt, knowledge_context=knowledge)
            quality_result = self.gewu.validate(core_content, knowledge)
            qc_rounds += 1
        outputs["optimized_content"] = core_content
        result["steps"].append({"step": "quality_check",
                                "result": quality_result,
                                "qc_rounds": qc_rounds})

        # ========== Step8：智云·守护 输出审计与脱敏 ==========
        print("\n[Step8] 输出安全审计...")
        audit_result = self.zhiyun.audit(core_content)
        result["steps"].append({"step": "output_audit", "result": audit_result})

        if not audit_result["safe"]:
            result["status"] = "blocked"
            result["final_output"] = "输出内容未通过安全合规审计"
            return result

        # ========== Step9：知遇·伯乐 个性化收尾（E匿名跳过） ==========
        if user_id != "default_user":
            print("\n[Step9] 知遇·伯乐 用户画像更新与个性化补充...")
            profile = self.zhiyu.build_user_profile(
                user_id, {"查询主题": [user_input[:50]]})
            recommendations = self.zhiyu.recommend_content(
                user_id, scene="学习提升", knowledge_pool=knowledge, top_n=2)
            result["agent_outputs"]["user_profile"] = profile
            result["agent_outputs"]["personalized_recs"] = recommendations

        # 最终输出（已脱敏）
        result["final_output"] = audit_result["desensitized_content"]

        print("\n" + "=" * 60)
        print(f"[系统] 全链路任务执行完成（trace_id={trace_id}）")
        print("=" * 60)
        return result


# -------------------------- 端到端场景演示 --------------------------
if __name__ == "__main__":
    orchestrator = AIFamilyOrchestrator()

    user_query = "生成本季度经营分析报告，包含数据解读、趋势预测、风险提示和可视化建议"
    result = orchestrator.execute(user_query, user_id="manager_001")

    print("\n" + "=" * 60)
    print(f"📌 最终经营报告（trace_id={result['trace_id']}）")
    print("=" * 60)
    print(result["final_output"])

    print("\n🔍 全链路执行节点：")
    for step in result["steps"]:
        print(f"  - {step['step']}")
