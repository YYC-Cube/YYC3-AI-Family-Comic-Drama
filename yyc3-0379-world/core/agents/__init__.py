# file: __init__.py
# description: YYC3 AI Family Agent 包（Phase 0 工程化版）——统一导出入口
# author: YanYuCloudCube Team <admin@0379.email>
# created: 2026-09-25
# status: active
# tags: [agent],[package]

"""YYC³ AI Family 多 Agent 协同包（ReAct-C 九步闭环）。

源：docs/YYC3-多端部署-Agent代码/YYC3-AI-Family-Agent/（Phase 0 工程化迁移，
单一事实源以本包为准，docs 目录转为只读归档）。

用法（Mock 模式零配置离线运行）::

    from core.agents import AIFamilyOrchestrator
    result = AIFamilyOrchestrator().execute("分析本季度营收")
    print(result["final_output"])

生产模式：设置 LLM_BASE_URL/LLM_API_KEY 指向网关或 DGX NIM 服务（见 .env.example）。
"""

from .base_agent import BaseAgent
from .chuangxiang_lingyun_agent import ChuangXiangLingYunAgent
from .gewu_zongshi_agent import GeWuZongShiAgent
from .orchestrator import AIFamilyOrchestrator
from .retriever import NullRetriever, Retriever
from .yanqi_qianhang_agent import YanQiQianHangAgent
from .yuanqi_tianshu_agent import YuanQiTianShuAgent
from .yujian_xianzhi_agent import YuJianXianZhiAgent
from .yushu_wanwu_agent import YuShuWanWuAgent
from .zhiyu_bole_agent import ZhiYuBoLeAgent
from .zhiyun_shouhu_agent import ZhiYunShouHuAgent, set_audit_sink

__all__ = [
    "AIFamilyOrchestrator",
    "BaseAgent",
    "ChuangXiangLingYunAgent",
    "GeWuZongShiAgent",
    "NullRetriever",
    "Retriever",
    "YanQiQianHangAgent",
    "YuanQiTianShuAgent",
    "YuJianXianZhiAgent",
    "YuShuWanWuAgent",
    "ZhiYuBoLeAgent",
    "ZhiYunShouHuAgent",
    "set_audit_sink",
]
