# file: base_agent.py
# description: YYC3 AI Family 公共基座 BaseAgent v1.1 —— 统一身份/提示词/LLM调用（httpx OpenAI 兼容）
# author: YanYuCloudCube Team <admin@0379.email>
# created: 2026-09-25
# status: active
# tags: [agent],[base],[llm]

"""AI Family Agent 统一基类（Phase 0 工程化版，源：docs/YYC3-多端部署-Agent代码）。

相对 docs 原型的改造：
- LLM 调用改用 httpx（复用项目既有依赖，OpenAI 兼容 /chat/completions 协议）
- print → logging（模块级 logger，接入网关日志体系）
- 配置全部环境变量化：LLM_BASE_URL / LLM_API_KEY / LLM_MODEL / LLM_TEMPERATURE / LLM_TIMEOUT_SECONDS
- 未配置 LLM_BASE_URL 时进入显式 Mock 模式；调用失败自动降级 Mock（五高-高可用兜底）
"""

import json
import logging
import os

import httpx

logger = logging.getLogger(__name__)


class BaseAgent:
    """AI Family Agent 统一基类。

    三要素：name（人格化名称）/ role（角色定位）/ system_prompt（系统提示词）
    """

    def __init__(self, name: str, role: str, system_prompt: str):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt

    # ---------------- LLM 调用 ----------------
    @staticmethod
    def _llm_base_url() -> str:
        """LLM 服务地址；空串 = 显式 Mock 模式（离线调试/单元测试零网络依赖）。"""
        return os.getenv("LLM_BASE_URL", "").strip().rstrip("/")

    @staticmethod
    def _model_mapping() -> dict:
        """角色→模型映射表（AGENT_MODEL_MAPPING JSON，按人格化名称匹配）。

        指向网关自身时，映射的模型名经 upstream_registry 通配规则路由，
        未命中或未配置回退 LLM_MODEL（适配点 A1）。解析失败降级空表，绝不 crash。
        """
        raw = os.getenv("AGENT_MODEL_MAPPING", "").strip()
        if not raw:
            return {}
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except Exception as exc:
            logger.warning("AGENT_MODEL_MAPPING 解析失败，回退默认模型：%s", exc)
            return {}

    def _resolve_model(self) -> str:
        """本 Agent 实际使用的模型：映射表命中优先，否则 LLM_MODEL 兜底。"""
        return self._model_mapping().get(self.name) or os.getenv("LLM_MODEL", "deepseek-v4-pro")

    def run(self, prompt: str, context: str = "") -> str:
        """统一 LLM 调用入口（OpenAI 兼容协议）。

        :param prompt: 任务提示词
        :param context: RAG 知识库注入上下文，格式如 "[来源：xxx] 内容"
        :return: 模型输出文本；服务不可用时降级 Mock 输出
        """
        user_content = f"{context}\n\n{prompt}" if context else prompt
        base_url = self._llm_base_url()
        if not base_url:
            return self._mock_run(user_content)
        try:
            payload = {
                "model": self._resolve_model(),
                "messages": [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_content},
                ],
                "temperature": float(os.getenv("LLM_TEMPERATURE", "0.3")),
            }
            headers = {"Authorization": f"Bearer {os.getenv('LLM_API_KEY', 'nim-local-dummy')}"}
            timeout = float(os.getenv("LLM_TIMEOUT_SECONDS", "60"))
            resp = httpx.post(
                f"{base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=timeout,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except Exception as exc:  # 高可用降级：LLM 不可用时切 Mock，保障调试链路可用
            logger.warning("[%s] LLM 调用失败，降级 Mock 模式：%s", self.name, exc)
            return self._mock_run(prompt)

    def _mock_run(self, prompt: str) -> str:
        """本地兜底：离线调试与单元测试用；生产由 DGX NIM 服务承接。"""
        return f"[{self.name}|Mock] 已接收任务：{prompt[:100]}..."

    def heartbeat(self) -> dict:
        """心跳信息（供 A2A 注册中心使用，Phase 2 接入）。"""
        return {"agent_name": self.name, "role": self.role, "status": "online"}
