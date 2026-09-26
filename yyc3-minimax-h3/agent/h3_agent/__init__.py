# -*- coding: utf-8 -*-
"""YYC3 MiniMax-H3 多Agent 框架（H3 Agent Family）

对齐 YYC3-AI-Family-Comic-Drama-Agent 设计，承担漫剧六阶段之阶段4（视听生成）
执行层：生产官（织影）/ 质检官（格物）/ 安全哨（智云·守护 H3 侧）+ 阶段编排引擎。
"""
from . import config, protocol, security  # noqa: F401
from .base_agent import H3BaseAgent        # noqa: F401
from .orchestrator import H3StageOrchestrator, StageStatus  # noqa: F401

__version__ = "1.0.0"
