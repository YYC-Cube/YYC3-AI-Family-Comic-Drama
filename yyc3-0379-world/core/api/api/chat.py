# file: chat.py
# description: 聊天 API 路由模块 - 支持同步和SSE流式响应
# author: YanYuCloudCube Team
# version: v2.0.0
# created: 2026-03-21
# updated: 2026-07-10
# status: active
# tags: [api],[chat],[route],[streaming],[sse]

"""
@file: app/api/chat.py
@description: Chat Completions API 路由，提供 OpenAI 兼容的统一接口（含SSE流式）
@author: YanYuCloudCube Team <admin@0379.email>
@version: v2.0.0
@created: 2026-03-13
@updated: 2026-07-10
@status: stable
@license: MIT
@copyright Copyright (c) 2026 YanYuCloudCube Team
@tags: api,python,chat,critical,public
"""

import hashlib
import json
import logging
import re
import time
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

from app.api.schemas import CompletionRequest
from app.config import settings
from app.errors.handler import error_handler, with_retry
from app.services import deepseek, ollama
from app.services import openai as openai_service
from app.services import openai_compatible, zhipu
from app.services.pricing import pricing
from app.services.upstream_registry import registry as upstream_registry
from app.services.usage_logger import log_usage
from app.utils import (
    cache_manager,
    concurrency_limiter,
    content_filter,
    metrics_manager,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _cache_key(req: CompletionRequest) -> str:
    payload = json.dumps(req.dict(), sort_keys=True).encode()
    return "llm_cache:" + hashlib.sha256(payload).hexdigest()


class _UpstreamAttemptError(Exception):
    """单个上游（含其备用地址）全部失败的内部信号"""


class SovereignUnavailableError(Exception):
    """主权路由无可用 sovereign 上游（拒绝降级到云，调用方应返回 503）"""

    def __init__(self, model: str):
        self.model = model
        super().__init__(f"sovereign 模式无可用本地上游（model={model}），拒绝降级到云")


class _UpstreamBackend:
    """
    上游池后端适配器：把 OpenAI 兼容上游包装成与 zhipu/ollama 同签名的后端。

    - 请求按降级链尝试：选中上游 → 同 capability 其他上游（按 priority）
    - 每个上游先打 base_url，失败自动切 fallback_url（QSFP 主 / Tailscale 备）
    - 每次尝试上报 registry（EWMA + 熔断状态机）
    - served_by / degraded_from 供响应头 X-YYC3-Upstream / X-YYC3-Degraded
    """

    def __init__(self, upstream, sovereign_only: bool = False):
        self.primary = upstream
        self.sovereign_only = sovereign_only  # 主权模式：降级链仅含 sovereign 上游
        self.served_by = None
        self.degraded_from: list = []  # 尝试失败的上游名（不含最终成功者）

    async def _attempt_upstream(
        self, u, model: str, messages: list, max_tokens, temperature, top_p
    ) -> dict:
        addresses = [u.base_url] + ([u.fallback_url] if u.fallback_url else [])
        upstream_registry.acquire(u)
        started = time.time()
        last_err = ""
        for addr in addresses:
            t0 = time.time()
            try:
                resp = await openai_compatible.chat_completion(
                    base_url=addr,
                    model=model,
                    messages=messages,
                    api_key=u.api_key(),
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    provider_name=getattr(u, "provider", "openai_compat"),
                )
                upstream_registry.release(u, (time.time() - started) * 1000, True)
                return resp
            except Exception as e:
                last_err = f"{addr}: {e}"
                # P1-1 多 Key 轮换：429 限流立即跳下一把 Key 重试本地址
                if "429" in str(e) and (u.api_key_envs or u.api_key_env):
                    new_key = u.rotate_key_on_429()
                    if new_key:
                        logger.warning(f"上游 {u.name} 429 → 轮换下一把 Key 重试")
                        continue
                logger.warning(f"上游 {u.name} 地址失败 {last_err}（{time.time() - t0:.1f}s）")
        upstream_registry.release(u, (time.time() - started) * 1000, False, last_err)
        raise _UpstreamAttemptError(last_err)

    async def chat_completion(
        self,
        model: str,
        messages: list,
        max_tokens=None,
        temperature: float = 0.7,
        top_p=None,
        stream: bool = False,
    ) -> dict:
        errors = []
        for u in upstream_registry.fallback_chain(self.primary):
            if u is not self.primary and not upstream_registry.available(u):
                continue  # 熔断摘除期，跳过
            try:
                resp = await self._attempt_upstream(
                    u, model, messages, max_tokens, temperature, top_p
                )
                self.served_by = u
                return resp
            except _UpstreamAttemptError as e:
                if u is self.primary or u.name not in self.degraded_from:
                    self.degraded_from.append(u.name)
                errors.append(f"{u.name}: {e}")
        raise RuntimeError(f"上游降级链全部失败: {'; '.join(errors)}")

    async def chat_completion_stream(
        self,
        model: str,
        messages: list,
        max_tokens=None,
        temperature: float = 0.7,
        top_p=None,
    ):
        """流式：先取到首个 chunk 证明链路可用，失败则走下一上游/地址"""
        errors = []
        for u in upstream_registry.fallback_chain(self.primary, sovereign_only=self.sovereign_only):
            if u is not self.primary and not upstream_registry.available(u):
                continue
            addresses = [u.base_url] + ([u.fallback_url] if u.fallback_url else [])
            upstream_registry.acquire(u)
            started = time.time()
            for addr in addresses:
                # P1-1 流式多 Key 轮换：429 限流同地址换 Key 重试（与同步路对齐）
                for attempt in range(1 + len(u.api_key_envs or [])):
                    agen = openai_compatible.chat_completion_stream(
                        base_url=addr,
                        model=model,
                        messages=messages,
                        api_key=u.api_key(),
                        max_tokens=max_tokens,
                        temperature=temperature,
                        top_p=top_p,
                    )
                    try:
                        first: dict = {}
                        async for chunk in agen:
                            first = chunk
                            break
                    except Exception as e:
                        if "429" in str(e) and (u.api_key_envs or u.api_key_env):
                            if u.rotate_key_on_429():
                                logger.warning(
                                    f"上游 {u.name}@{addr} 流式 429 → 轮换下一把 Key 重试"
                                )
                                continue  # 同地址换 Key 重试
                        errors.append(f"{u.name}@{addr}: {e}")
                        break  # 非 429 或无 Key 可换 → 下一地址
                    upstream_registry.release(u, (time.time() - started) * 1000, True)
                    self.served_by = u
                    yield {**first, "_yyc3_upstream": u.name}
                    async for chunk in agen:
                        yield chunk
                    return
            upstream_registry.release(u, (time.time() - started) * 1000, False, str(errors))
        raise RuntimeError(f"上游降级链全部失败（流式）: {'; '.join(errors)}")


def _select_backend(model_name: str, sovereign: bool = False):
    """选择模型后端，返回 (backend_module, backend_name, backend_type)

    三段式：
    1. 云前缀/云模型名（zhipu:/deepseek:/openai: 及默认名单）→ 云适配器
    2. 上游池模型匹配（fnmatch 通配，router_enabled 灰度开关）→ _UpstreamBackend
    3. 兜底 → 本地 Ollama（原默认行为保留）

    sovereign=True（请求头 X-YYC3-Sovereign: required）：
    跳过云适配器，仅路由 sovereign 上游；无可用抛 SovereignUnavailableError（→503 不降级到云）
    """
    if sovereign:
        if settings.router_enabled and upstream_registry.upstreams:
            u = upstream_registry.select_sovereign(model_name)
            if u is not None:
                return (
                    _UpstreamBackend(u, sovereign_only=True),
                    model_name,
                    f"upstream:{u.name}",
                )
        raise SovereignUnavailableError(model_name)
    if model_name.startswith("zhipu:") or model_name in [
        "glm-4-flash",
        "glm-4-plus",
        "glm-4",
    ]:
        backend = zhipu
        backend_name = model_name.split(":", 1)[1] if ":" in model_name else model_name
        backend_type = "zhipu"
    elif model_name.startswith("deepseek:") or model_name in [
        "deepseek-chat",
        "deepseek-coder",
    ]:
        backend = deepseek
        backend_name = model_name.split(":", 1)[1] if ":" in model_name else model_name
        backend_type = "deepseek"
    elif model_name.startswith("openai:") or model_name in [
        "gpt-4",
        "gpt-4o",
        "gpt-3.5-turbo",
    ]:
        backend = openai_service
        backend_name = model_name.split(":", 1)[1] if ":" in model_name else model_name
        backend_type = "openai"
    elif model_name.startswith("ollama:") or model_name.startswith("local:"):
        backend = ollama
        backend_type = "ollama"
        backend_name = model_name.split(":", 1)[1] if ":" in model_name else model_name
    elif settings.router_enabled and upstream_registry.upstreams:
        u = upstream_registry.select(model_name)
        if u is not None:
            return _UpstreamBackend(u), model_name, f"upstream:{u.name}"
        backend = ollama
        backend_type = "ollama"
        backend_name = model_name
    else:
        # 默认尝试Ollama本地模型
        backend = ollama
        backend_type = "ollama"
        backend_name = model_name
    return backend, backend_name, backend_type


def _has_stream_method(backend) -> bool:
    """检查后端是否支持流式输出"""
    return hasattr(backend, "chat_completion_stream")


@router.post("/chat/completions")
async def chat_completion(req: CompletionRequest, request: Request):
    """
    聊天完成接口

    - stream=false: 返回完整JSON响应
    - stream=true: 返回SSE流式响应（data: {...}\\n\\n 格式）
    """
    start_time = time.time()
    metrics_manager.increment_active_requests()

    # ── P2-1 Guardrail 输入检查：违规即 400，不进入推理 ──
    try:
        from app.services.guardrails import run_guardrails

        user_text = "\n".join(
            m.content for m in req.messages if getattr(m, "role", "") == "user" and m.content
        )
        violation = await run_guardrails(user_text, stage="input")
        if violation is not None:
            metrics_manager.decrement_active_requests()
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "message": f"输入违反内容安全策略: {violation}",
                        "type": "guardrail_blocked",
                    }
                },
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"guardrail 输入链异常（放行）: {e}")

    # ── 主权路由检测（P0-3）：X-YYC3-Sovereign: required → 仅本地推理 ──
    sovereign = request.headers.get("X-YYC3-Sovereign", "").strip().lower() == "required"

    # ── 选择后端 ──────────────────────────────────────────
    try:
        backend, backend_name, backend_type = _select_backend(req.model, sovereign=sovereign)
    except SovereignUnavailableError as e:
        metrics_manager.decrement_active_requests()
        raise HTTPException(
            status_code=503,
            detail={
                "error": {
                    "message": str(e),
                    "type": "sovereign_unavailable",
                    "X-YYC3-Sovereign": "unavailable",
                }
            },
        )
    except Exception as e:
        error_response = await error_handler.handle(
            e, context={"model": req.model, "operation": "backend_selection"}
        )
        metrics_manager.decrement_active_requests()
        raise HTTPException(status_code=error_response["status_code"], detail=error_response)

    # ── P0-1 虚拟密钥治理：白名单 + 预算闸门（402 语义）──
    user_ctx = getattr(request.state, "user", None)
    vk = user_ctx.get("vk") if isinstance(user_ctx, dict) else None
    if vk is not None:
        from app.services.virtual_key_manager import vk_manager

        if not vk_manager.check_model_allowed(vk, req.model):
            metrics_manager.decrement_active_requests()
            raise HTTPException(
                status_code=403,
                detail={
                    "error": {
                        "message": f"虚拟密钥无权访问模型 {req.model}",
                        "type": "model_not_allowed",
                    }
                },
            )
        if not vk_manager.check_budget(vk, est_cost=0.0):  # 预估 0：仅查已花超限
            metrics_manager.decrement_active_requests()
            raise HTTPException(
                status_code=402,
                detail={
                    "error": {
                        "message": "虚拟密钥预算已耗尽",
                        "type": "budget_exceeded",
                    }
                },
            )
        if not await vk_manager.check_tpm(vk):  # TPM 滑窗限流（Redis 分钟窗口）
            metrics_manager.decrement_active_requests()
            raise HTTPException(
                status_code=429,
                detail={
                    "error": {
                        "message": "虚拟密钥 TPM 限流触发",
                        "type": "rate_limit_exceeded",
                    }
                },
            )

    # ── 流式分支 ──────────────────────────────────────────
    if req.stream:
        return await _handle_stream(req, backend, backend_name, backend_type, start_time, vk)

    # ── 同步分支（带缓存） ────────────────────────────────
    return await _handle_sync(req, backend, backend_name, backend_type, start_time, vk)


def _record_spend(vk, response: dict, model: str, upstream_name: str, latency_ms: float) -> float:
    """P0-1 响应后记账：算成本 → 入队（微秒级）→ 返回成本供响应头披露"""
    if vk is None:
        return 0.0
    try:
        usage = response.get("usage", {}) or {}
        pt = int(usage.get("prompt_tokens") or 0)
        ct = int(usage.get("completion_tokens") or 0)
        cost = pricing.completion_cost(model, pt, ct)
        if cost == 0.0 and pt == 0 and ct == 0:
            return 0.0
        import asyncio

        from app.services.virtual_key_manager import vk_manager

        asyncio.get_running_loop().create_task(
            vk_manager.enqueue_spend(
                {
                    "key_id": vk.get("id"),
                    "model": model,
                    "upstream": upstream_name,
                    "capability": "chat",
                    "prompt_tokens": pt,
                    "completion_tokens": ct,
                    "cost_usd": cost,
                    "latency_ms": int(latency_ms),
                }
            )
        )
        return cost
    except Exception as e:
        logger.warning(f"记账失败（不影响响应）: {e}")
        return 0.0


async def _handle_sync(req, backend, backend_name, backend_type, start_time, vk=None):
    """处理同步请求（带缓存）"""
    try:
        cache_key = _cache_key(req)
        cached = await cache_manager.get(cache_key)
        if cached:
            metrics_manager.record_cache_hit(req.model)
            metrics_manager.record_request("POST", "/chat/completions", 200, "cache")
            metrics_manager.record_response_time(
                "POST", "/chat/completions", time.time() - start_time, "cache"
            )
            metrics_manager.decrement_active_requests()
            return cached

        metrics_manager.record_cache_miss(req.model)
    except Exception as e:
        error_response = await error_handler.handle(e, context={"operation": "cache_check"})
        metrics_manager.decrement_active_requests()
        raise HTTPException(status_code=error_response["status_code"], detail=error_response)

    async with concurrency_limiter.limit():
        backend_start_time = time.time()
        try:
            if backend_type.startswith("upstream:"):
                # 上游池自带降级链+地址切换重试，不再包 with_retry
                response = await backend.chat_completion(
                    model=backend_name,
                    messages=[m.dict() for m in req.messages],
                    max_tokens=req.max_tokens,
                    temperature=req.temperature,
                    top_p=req.top_p,
                    stream=False,
                )
            else:
                response = await with_retry(max_retries=2, delay=1.0)(backend.chat_completion)(
                    model=backend_name,
                    messages=[m.dict() for m in req.messages],
                    max_tokens=req.max_tokens,
                    temperature=req.temperature,
                    top_p=req.top_p,
                    stream=False,
                )
            metrics_manager.record_backend_latency(
                backend_type, req.model, time.time() - backend_start_time
            )
        except Exception as e:
            # Ollama失败时回退到智谱
            if backend is ollama:
                try:
                    response = await with_retry(max_retries=2, delay=1.0)(zhipu.chat_completion)(
                        model="glm-4-flash",
                        messages=[m.dict() for m in req.messages],
                        max_tokens=req.max_tokens,
                        temperature=req.temperature,
                        top_p=req.top_p,
                        stream=False,
                    )
                    backend_type = "zhipu"
                except Exception as ee:
                    error_response = await error_handler.handle(
                        ee,
                        context={
                            "model": req.model,
                            "backend": backend_type,
                            "fallback": "zhipu",
                            "operation": "fallback_request",
                        },
                    )
                    raise HTTPException(
                        status_code=error_response["status_code"], detail=error_response
                    )
            else:
                error_response = await error_handler.handle(
                    e,
                    context={
                        "model": req.model,
                        "backend": backend_type,
                        "operation": "backend_request",
                    },
                )
                raise HTTPException(
                    status_code=error_response["status_code"], detail=error_response
                )

        # 缓存 + 用量记录
        await cache_manager.set(
            cache_key,
            response,
            ttl=300,
            tags=[f"model:{req.model}"],
        )

        # 用量落库/指标为旁路：失败不得杀死已成功的推理响应
        try:
            usage = response.get("usage", {})
            await log_usage(
                model=req.model,
                backend_type=backend_type,
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
                user_id=req.user_id,
            )
        except Exception as e:
            logger.warning(f"log_usage 失败（不影响响应）: {e}")

        try:
            metrics_manager.record_model_usage(req.model, backend_type)
            metrics_manager.record_token_usage(
                req.model,
                backend_type,
                "prompt",
                response.get("usage", {}).get("prompt_tokens", 0),
            )
            metrics_manager.record_token_usage(
                req.model,
                backend_type,
                "completion",
                response.get("usage", {}).get("completion_tokens", 0),
            )
        except Exception as e:
            logger.warning(f"metrics 记录失败（不影响响应）: {e}")

        filtered_response, is_blocked = content_filter.filter_response(response)
        if is_blocked:
            logger.warning(f"Response blocked for model: {req.model}, user: {req.user_id}")

        # ── P2-1 Guardrail 输出检查：PII 泄漏防护（检查器异常按放行）──
        try:
            from app.services.guardrails import run_guardrails

            out_text = "\n".join(
                c.get("message", {}).get("content", "")
                for c in filtered_response.get("choices", [])
                if isinstance(c, dict)
            )
            out_violation = await run_guardrails(out_text, stage="output")
            if out_violation is not None:
                metrics_manager.decrement_active_requests()
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": {
                            "message": f"输出违反内容安全策略: {out_violation}",
                            "type": "guardrail_blocked",
                        }
                    },
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"guardrail 输出链异常（放行）: {e}")

        metrics_manager.record_request("POST", "/chat/completions", 200, backend_type)
        metrics_manager.record_response_time(
            "POST", "/chat/completions", time.time() - start_time, backend_type
        )
        metrics_manager.decrement_active_requests()

        if backend_type.startswith("upstream:"):
            headers = {
                "X-YYC3-Upstream": (
                    backend.served_by.name if backend.served_by else backend.primary.name
                )
            }
            if backend.degraded_from:
                headers["X-YYC3-Degraded"] = ",".join(backend.degraded_from)
            if backend.sovereign_only:
                headers["X-YYC3-Sovereign"] = "satisfied"
            upstream_name = backend.served_by.name if backend.served_by else backend.primary.name
            cost = _record_spend(
                vk,
                filtered_response,
                req.model,
                upstream_name,
                (time.time() - start_time) * 1000,
            )
            if cost > 0.0 or vk is not None:
                headers["X-YYC3-Cost"] = f"{cost:.6f}"
            return JSONResponse(content=filtered_response, headers=headers)
        else:
            _record_spend(
                vk,
                filtered_response,
                req.model,
                backend_type,
                (time.time() - start_time) * 1000,
            )
        return filtered_response


def _sanitize_chunk(chunk: dict, carry: dict) -> dict:
    """流式输出链 PII 纵深防御（chunk 级）。

    流式首字节一旦发出便无法回退改判 400（对齐同步路 run_guardrails 拦截语义不可行），
    故采用脱敏策略：命中 _PII_PATTERNS 即替换为 ****（与 content_filter 第一层同构）。
    carry 缓冲拼接上一 chunk 尾部 20 字符，解决 PII 跨 chunk 截断漏检
    （如 "1381234" | "5678" 分片）；检查器异常按放行（安全链不可用 ≠ 拒绝服务）。
    """
    try:
        choices = chunk.get("choices")
        if not isinstance(choices, list) or not choices:
            return chunk
        delta = choices[0].get("delta") if isinstance(choices[0], dict) else None
        content = delta.get("content") if isinstance(delta, dict) else None
        if not (content and isinstance(content, str)):
            return chunk
        prev = carry.pop("text", "")
        text = prev + content
        from app.services.guardrails import _PII_PATTERNS

        for pattern, _label in _PII_PATTERNS:
            text = re.sub(pattern, "****", text)
        hold = min(len(text), 20)
        carry["text"] = text[len(text) - hold :] if hold else ""
        # 只下发除 carry 尾部以外的部分（尾部留待下 chunk 拼接，避免重复输出）
        delta["content"] = text[: len(text) - hold]
        return chunk
    except Exception:
        return chunk


async def _handle_stream(req, backend, backend_name, backend_type, start_time, vk=None):
    """
    处理流式请求，返回SSE StreamingResponse

    所有Provider的 chat_completion_stream() 都产出统一的chunk格式，
    这里统一包装为 SSE "data: {json}\\n\\n" 格式。
    """
    # 流式请求不查缓存
    metrics_manager.record_cache_miss(req.model)

    if not _has_stream_method(backend):
        # 后端不支持流式，降级为同步后包装
        logger.warning(f"Backend {backend_type} has no stream method, falling back to sync")

        async def _fallback_stream():
            response = await backend.chat_completion(
                model=backend_name,
                messages=[m.dict() for m in req.messages],
                max_tokens=req.max_tokens,
                temperature=req.temperature,
                top_p=req.top_p,
                stream=False,
            )
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            yield {
                "id": response.get("id", ""),
                "object": "chat.completion.chunk",
                "created": response.get("created", int(time.time())),
                "model": req.model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {"role": "assistant", "content": content},
                        "finish_reason": None,
                    }
                ],
            }
            yield {
                "id": response.get("id", ""),
                "object": "chat.completion.chunk",
                "created": response.get("created", int(time.time())),
                "model": req.model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {},
                        "finish_reason": "stop",
                    }
                ],
            }

        stream_gen = _fallback_stream()
    else:
        stream_gen = backend.chat_completion_stream(
            model=backend_name,
            messages=[m.dict() for m in req.messages],
            max_tokens=req.max_tokens,
            temperature=req.temperature,
            top_p=req.top_p,
        )

    async def sse_wrapper(gen) -> AsyncGenerator[str, None]:
        """将统一的chunk dict包装为SSE格式（P0-1：流式末尾 usage → 记账 + cost 回填）"""
        total_tokens = 0
        usage_info: dict = {}
        pii_carry: dict = {}  # PII 跨 chunk 截断缓冲（_sanitize_chunk 尾部 20 字符滞留）
        try:
            async for chunk in gen:
                # 估算token（粗略：按字符数/4）
                delta = chunk.get("choices", [{}])[0].get("delta", {})
                if delta.get("content"):
                    total_tokens += len(delta["content"]) // 4
                # 上游显式 usage chunk（OpenAI stream_options / zhipu 末块）优先采信
                if chunk.get("usage"):
                    usage_info = chunk["usage"]

                # ── P2 输出链 PII 纵深防御（chunk 级脱敏，首字节已发不可回退 400）──
                chunk = _sanitize_chunk(chunk, pii_carry)

                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            # 正常流末：flush 滞留缓冲（carry 尾部不再等下 chunk 拼接）
            tail = pii_carry.pop("text", "")
            if tail:
                flush_chunk = {
                    "id": "yyc3-flush",
                    "object": "chat.completion.chunk",
                    "model": req.model,
                    "choices": [{"index": 0, "delta": {"content": tail}, "finish_reason": None}],
                }
                yield f"data: {json.dumps(flush_chunk, ensure_ascii=False)}\n\n"
        except Exception as e:
            logger.error(f"Stream error: {e}")
            error_chunk = {
                "error": {
                    "message": str(e),
                    "type": "stream_error",
                }
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
        finally:
            # 发送结束标记
            yield "data: [DONE]\n\n"

            # ── P0-1 流式成本回填：真实 usage → 记账 + cost chunk 披露 ──
            try:
                if vk is not None:
                    from app.services.virtual_key_manager import vk_manager

                    pt = int(usage_info.get("prompt_tokens") or 0)
                    ct = int(usage_info.get("completion_tokens") or total_tokens)
                    cost = pricing.completion_cost(req.model, pt, ct)
                    await vk_manager.enqueue_spend(
                        {
                            "key_id": vk.get("id"),
                            "model": req.model,
                            "upstream": backend_name,
                            "capability": "chat_stream",
                            "prompt_tokens": pt,
                            "completion_tokens": ct,
                            "cost_usd": cost,
                            "latency_ms": int((time.time() - start_time) * 1000),
                        }
                    )
                    cost_chunk = {
                        "id": "yyc3-cost",
                        "object": "chat.completion.chunk",
                        "model": req.model,
                        "choices": [],
                        "yyc3_cost_usd": round(cost, 6),
                        "yyc3_usage": {
                            "prompt_tokens": pt,
                            "completion_tokens": ct,
                            "total_tokens": pt + ct,
                        },
                    }
                    # DONE 之后追加的扩展块（非 OpenAI 标准字段，解析器按未知块忽略）
                    yield f"data: {json.dumps(cost_chunk, ensure_ascii=False)}\n\n"
            except Exception as e:
                logger.warning(f"流式成本回填失败（不影响响应）: {e}")

            # 记录用量
            try:
                await log_usage(
                    model=req.model,
                    backend_type=backend_type,
                    prompt_tokens=int(usage_info.get("prompt_tokens") or 0),
                    completion_tokens=int(usage_info.get("completion_tokens") or total_tokens),
                    total_tokens=int(
                        usage_info.get("total_tokens")
                        or (usage_info.get("prompt_tokens") or 0) + total_tokens
                    ),
                    user_id=req.user_id,
                )
                metrics_manager.record_model_usage(req.model, backend_type)
                metrics_manager.record_token_usage(
                    req.model, backend_type, "completion", total_tokens
                )
            except Exception:
                pass

            metrics_manager.record_request("POST", "/chat/completions", 200, backend_type)
            metrics_manager.record_response_time(
                "POST", "/chat/completions", time.time() - start_time, backend_type
            )
            metrics_manager.decrement_active_requests()

    stream_headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    if backend_type.startswith("upstream:"):
        # 流式降级发生在响应开始后，无法改 header；
        # 实际服务者通过首个 chunk 的 _yyc3_upstream 字段披露
        stream_headers["X-YYC3-Upstream"] = backend.primary.name
    if vk is not None:
        stream_headers["X-YYC3-Cost"] = "0.000000"  # 流式实际成本见末尾 usage chunk
    return StreamingResponse(
        sse_wrapper(stream_gen),
        media_type="text/event-stream",
        headers=stream_headers,
    )
