# file: guardrails.py
# description: Guardrail 链 - 输入/输出检查器可插拔管道（学 OpenAI Moderation，零外部依赖）
# author: YanYuCloudCube Team
# created: 2026-09-20
# status: active
# tags: [guardrail],[safety],[pipeline]

"""
@file: app/services/guardrails.py
@description: 内容安全管道。设计原则（学 Guardrails.ai 精简）：
    ① 检查器即函数：async def checker(text) -> Optional[str]（返回违规说明，None=通过）
    ② 链式执行：任一检查器拒绝即短路；默认链零外部依赖（不阻塞推理主路径）
    ③ 开关可控：GUARDRAILS_ENABLED=false 一键关闭；检查器异常按放行处理（安全链不可用 ≠ 拒绝服务）
扩展：新增检查器在 _INPUT_CHAIN/_OUTPUT_CHAIN 登记；可接外部审核 API（Provider 化）
@author: YanYuCloudCube Team <admin@0379.email>
@license: MIT
"""

import logging
import os
import re
from typing import Awaitable, Callable, List, Optional

logger = logging.getLogger(__name__)

Checker = Callable[[str], Awaitable[Optional[str]]]

GUARDRAILS_ENABLED = os.getenv("GUARDRAILS_ENABLED", "true").lower() != "false"
# 环境变量注入自定义敏感词（逗号分隔），运行时可运营化更新
EXTRA_BLOCKED_TERMS = [
    t.strip() for t in os.getenv("GUARDRAILS_BLOCKED_TERMS", "").split(",") if t.strip()
]

# ── 云审核 Provider（P2-1 深化）：外部内容安全 API，环境变量启用 ──
# GUARDRAILS_CLOUD_URL: 审核端点（POST JSON {"text": ...} → {"flagged": bool, "reason": str}）
# GUARDRAILS_CLOUD_KEY: 鉴权 Bearer Token；两者齐备才挂载，缺省纯本地链
CLOUD_URL = os.getenv("GUARDRAILS_CLOUD_URL", "").strip()
CLOUD_KEY = os.getenv("GUARDRAILS_CLOUD_KEY", "").strip()


async def _check_cloud_moderation(text: str) -> Optional[str]:
    """外部审核 API。超时/异常按放行（可用性优先，安全链不可用 ≠ 拒绝服务）"""
    if not (CLOUD_URL and CLOUD_KEY):
        return None
    try:
        import httpx

        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.post(
                CLOUD_URL,
                json={"text": text[:8000]},  # 截断防爆
                headers={"Authorization": f"Bearer {CLOUD_KEY}"},
            )
            resp.raise_for_status()
            data = resp.json()
        if data.get("flagged"):
            return f"云审核拦截: {str(data.get('reason', 'unspecified'))[:80]}"
        return None
    except Exception as e:
        logger.warning(f"[guardrail:cloud] 审核服务不可达（放行）: {e}")
        return None


async def _check_prompt_injection(text: str) -> Optional[str]:
    """基础提示注入模式检测（显式越权指令启发式，误报率优先压低：只拦高置信模式）"""
    patterns = [
        r"忽略(?:之前|上面|以上)(?:的)?(?:所有)?(?:指令|设定|规则)",
        r"ignore (?:all )?(?:previous|above|prior) instructions",
        r"reveal (?:your )?(?:system )?prompt",
        r"(?:你|你 now)现在是?(?:无限制|没有限制|不受限制)的",
        r"DAN mode|developer mode",
    ]
    for p in patterns:
        if re.search(p, text, re.IGNORECASE):
            return f"疑似提示注入（匹配 {p[:24]}…）"
    return None


async def _check_blocked_terms(text: str) -> Optional[str]:
    """敏感词检测：默认空表（由 GUARDRAILS_BLOCKED_TERMS 运营配置），空表直接放行"""
    if not EXTRA_BLOCKED_TERMS:
        return None
    low = text.lower()
    for term in EXTRA_BLOCKED_TERMS:
        if term.lower() in low:
            return f"命中敏感词: {term[:4]}***"
    return None


async def _check_length_bomb(text: str) -> Optional[str]:
    """超长输入防护（防 token 轰炸；单字段上限 128K 字符，约 3 倍上下文窗口余量）"""
    if len(text) > 128_000:
        return f"输入超长: {len(text)} 字符"
    return None


# ── 输出链：PII 泄漏防护（学 Guardrails.ai PII guard 精简）──
# 高置信模式才拦（中国手机号/身份证/银行卡/邮箱）；GUARDRAILS_PII_ENABLED=false 可关
_PII_ENABLED = os.getenv("GUARDRAILS_PII_ENABLED", "true").lower() != "false"
_PII_PATTERNS = [
    (r"(?<!\d)1[3-9]\d{9}(?!\d)", "手机号"),
    (r"(?<!\d)\d{17}[\dXx](?!\d)", "身份证号"),
    (r"(?<!\d)\d{16,19}(?!\d)", "银行卡号"),
    (r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "邮箱"),
]


async def _check_pii_leak(text: str) -> Optional[str]:
    """输出 PII 检测：命中高置信个人信息模式即拦（防模型幻觉/训练数据泄漏 PII）"""
    if not _PII_ENABLED:
        return None
    for pattern, label in _PII_PATTERNS:
        m = re.search(pattern, text)
        if m:
            return f"疑似泄漏{label}: {m.group(0)[:4]}***"
    return None


_INPUT_CHAIN: List[Checker] = [
    _check_length_bomb,
    _check_prompt_injection,
    _check_blocked_terms,
    _check_cloud_moderation,  # 环境变量未配置时自跳过（零成本）
]
_OUTPUT_CHAIN: List[Checker] = [
    _check_pii_leak,  # GUARDRAILS_PII_ENABLED=false 可关（本地推理可信场景）
]


async def run_guardrails(text: str, stage: str = "input") -> Optional[str]:
    """执行 guardrail 链。返回违规说明（拒绝）或 None（放行）。
    stage: input | output。检查器异常按放行处理（可用性优先，降级不阻塞）。"""
    if not GUARDRAILS_ENABLED:
        return None
    chain = _INPUT_CHAIN if stage == "input" else _OUTPUT_CHAIN
    for checker in chain:
        try:
            verdict = await checker(text)
            if verdict is not None:
                logger.info(f"[guardrail:{stage}] 拦截: {verdict}")
                return verdict
        except Exception as e:
            logger.warning(f"[guardrail:{stage}] 检查器异常（放行）: {e}")
    return None
