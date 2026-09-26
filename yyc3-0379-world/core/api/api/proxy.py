# file: proxy.py
# description: 能力代理端点 - embeddings/rerank/asr/ocr，复用上游池 capability 路由
# author: YanYuCloudCube Team
# version: v1.0.0
# created: 2026-09-03
# status: active
# tags: [api],[proxy],[embeddings],[rerank],[asr],[ocr]

"""
@file: app/api/proxy.py
@description: 非 chat 能力的统一代理端点。上游池按 capability（embedding/rerank/asr/ocr）
             分层选择 + 熔断降级，与 chat 共用 OPENAI_COMPATIBLE_UPSTREAMS 配置与
             X-YYC3-Upstream / X-YYC3-Degraded 响应头契约。

             路径约定（上游为 vLLM/vLLM-兼容服务）：
             - embedding → {base}/v1/embeddings（OpenAI 格式透传）
             - reranker  → {base}/v1/score（vLLM --task score，Jina 格式；
                           本端点对外暴露 Cohere 风格 /v1/rerank 并做双向转换）
             - asr       → {base}/v1/audio/transcriptions（multipart 透传）
             - ocr       → {base}/v1/ocr（multipart 透传）
@author: YanYuCloudCube Team <admin@0379.email>
@license: MIT
@copyright Copyright (c) 2026 YanYuCloudCube Team
"""

import base64
import logging
import time
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.errors.handler import error_handler
from app.services.upstream_registry import Upstream, registry
from app.utils import metrics_manager

logger = logging.getLogger(__name__)

router = APIRouter()

_TIMEOUT = httpx.Timeout(120.0, connect=10.0, read=120.0)

# capability → 上游请求路径
# rerank 走生成式打分（Qwen3-Reranker 官方用法）：指令模板 + completions logprobs 取 yes 概率
_CAP_PATH = {
    "embedding": "/v1/embeddings",
    "rerank": "/v1/completions",
    "asr": "/v1/audio/transcriptions",
    "ocr": "/v1/chat/completions",  # OCR 走 VLM chat 适配（2026-09-24：vLLM 无 /v1/ocr 原生路由）
}

# Qwen3-Reranker 官方 judge 三段式模板（生成式打分：取 yes token 概率）
_RERANK_PREFIX = (
    "<|im_start|>system\nJudge whether the Document meets the requirements based on "
    'the Query and the Instruct provided. Note that the answer can only be "yes" or "no".'
    "<|im_end|>\n<|im_start|>user\n"
)
_RERANK_INSTRUCT = "Given a web search query, retrieve relevant passages that answer the query"
_RERANK_SUFFIX = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"


def _rerank_prompt(query: str, doc: str) -> str:
    middle = (
        f"<Instruct>{_RERANK_INSTRUCT}</Instruct>"
        f"\n<Query>{query}</Query>\n<Document>{doc}</Document>"
    )
    return _RERANK_PREFIX + middle + _RERANK_SUFFIX


class EmbeddingRequest(BaseModel):
    """OpenAI 兼容 embeddings 请求"""

    model: str
    input: Any  # str | List[str] | List[int tokens]
    dimensions: Optional[int] = None
    user: Optional[str] = None


class RerankRequest(BaseModel):
    """Cohere/Jina 风格 rerank 请求（对外契约）"""

    model: str
    query: str
    documents: List[str]
    top_n: Optional[int] = None
    user: Optional[str] = None


# ── 通用转发（降级链 + 熔断上报 + X 头） ────────────────────


def _chain(capability: str) -> List[Upstream]:
    """同 capability 上游按优先级排序（作为降级链）"""
    return sorted(
        [u for u in registry.upstreams.values() if u.capability == capability],
        key=lambda u: (u.priority, -u.weight),
    )


def _addresses(u: Upstream) -> List[str]:
    return [u.base_url] + ([u.fallback_url] if u.fallback_url else [])


async def _forward(
    capability: str,
    *,
    json_body: Optional[Dict] = None,
    data: Optional[Dict] = None,
    files: Optional[Dict] = None,
    headers_extra: Optional[Dict] = None,
):
    """
    按 capability 降级链转发；返回 (response_dict, served_upstream, degraded_from)。
    所有上游失败时抛 RuntimeError（由调用方转 502）。
    """
    errors: list = []
    degraded_from: list = []
    for u in _chain(capability):
        if not registry.available(u):
            continue
        registry.acquire(u)
        started = time.time()
        # 模型别名改写：请求 model 不在上游注册清单（如 OpenAI 客户端默认 whisper-1）
        # 时，改写为该上游首个注册模型，避免上游 404 model-not-found
        payload_json = dict(json_body) if json_body else None
        payload_data = dict(data) if data else None
        if u.models:
            req_model = (payload_json or payload_data or {}).get("model")
            if req_model and not u.serves(req_model):
                if payload_json is not None:
                    payload_json["model"] = u.models[0]
                if payload_data is not None:
                    payload_data["model"] = u.models[0]
        for addr in _addresses(u):
            url = f"{addr}{_CAP_PATH[capability]}"
            headers = {}
            if u.api_key():
                headers["Authorization"] = f"Bearer {u.api_key()}"
            if headers_extra:
                headers.update(headers_extra)
            try:
                async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                    resp = await client.post(
                        url,
                        json=payload_json,
                        data=payload_data,
                        files=files,
                        headers=headers,
                    )
                resp.raise_for_status()
                registry.release(u, (time.time() - started) * 1000, True)
                return resp.json(), u, degraded_from
            except Exception as e:
                errors.append(f"{u.name}@{addr}: {e}")
                logger.warning(f"[{capability}] 上游失败 {u.name}@{addr}: {e}")
        degraded_from.append(u.name)
        registry.release(u, (time.time() - started) * 1000, False, errors[-1] if errors else "")
    raise RuntimeError(f"[{capability}] 上游降级链全部失败: {'; '.join(errors)}")


def _json_or_502(payload: Dict, upstream: Upstream, degraded: List[str], status_hint: int = 200):
    headers = {"X-YYC3-Upstream": upstream.name}
    if degraded:
        headers["X-YYC3-Degraded"] = ",".join(degraded)
    return JSONResponse(content=payload, status_code=status_hint, headers=headers)


def _vk_from_request(request) -> Optional[Dict]:
    """从 request.state 提取虚拟密钥上下文（Auth 中间件写入），非 vk 返回 None"""
    user_ctx = getattr(request.state, "user", None)
    return user_ctx.get("vk") if isinstance(user_ctx, dict) else None


async def _vk_gate(request, capability: str, model: str) -> Optional[Dict]:
    """P1-3 能力收口治理：vk 模型白名单 + 预算闸门（对齐 chat 语义）。拒绝时抛 HTTPException"""
    from fastapi import HTTPException

    from app.services.virtual_key_manager import vk_manager

    vk = _vk_from_request(request)
    if vk is None:
        return None
    if not vk_manager.check_model_allowed(vk, model):
        raise HTTPException(
            status_code=403,
            detail={
                "error": {
                    "message": f"虚拟密钥无权访问模型 {model}",
                    "type": "model_not_allowed",
                }
            },
        )
    if not vk_manager.check_budget(vk, est_cost=0.0):
        raise HTTPException(
            status_code=402,
            detail={"error": {"message": "虚拟密钥预算已耗尽", "type": "budget_exceeded"}},
        )
    if not await vk_manager.check_tpm(vk):
        raise HTTPException(
            status_code=429,
            detail={
                "error": {
                    "message": "虚拟密钥 TPM 限流触发",
                    "type": "rate_limit_exceeded",
                }
            },
        )
    return vk


def _vk_spend(
    vk: Optional[Dict],
    capability: str,
    model: str,
    upstream_name: str,
    started: float,
    payload: Optional[Dict] = None,
):
    """proxy 能力（asr/ocr/embedding/rerank）响应后异步记账。无 vk 跳过"""
    if vk is None:
        return
    try:
        from app.services.pricing import pricing
        from app.services.virtual_key_manager import vk_manager

        usage = (payload or {}).get("usage", {}) or {}
        pt = int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0)
        ct = int(usage.get("completion_tokens") or usage.get("output_tokens") or 0)
        cost = pricing.completion_cost(model, pt, ct)

        import asyncio

        asyncio.get_running_loop().create_task(
            vk_manager.enqueue_spend(
                {
                    "key_id": vk.get("id"),
                    "model": model,
                    "upstream": upstream_name,
                    "capability": capability,
                    "prompt_tokens": pt,
                    "completion_tokens": ct,
                    "cost_usd": cost,
                    "latency_ms": int((time.time() - started) * 1000),
                }
            )
        )
    except Exception as e:
        logger.warning(f"[{capability}] vk 记账失败（不影响响应）: {e}")


def _yes_probability(choice: Dict) -> float:
    """从 completions choice 的 top_logprobs 里提取 yes 概率（Qwen3-Reranker 语义）"""
    import math

    top = (choice.get("logprobs") or {}).get("top_logprobs") or []
    if not top:
        return 0.0
    for tok, lp in (top[0] or {}).items():
        if tok.strip().lower() == "yes":
            return math.exp(lp)
    return 0.0


# ── 1) POST /v1/embeddings ─────────────────────────────────


@router.post("/v1/embeddings")
async def embeddings(req: EmbeddingRequest, request: Request):
    """向量嵌入（OpenAI 兼容；上游池 capability=embedding；vk 白名单+预算+记账）"""
    started = time.time()
    try:
        vk = await _vk_gate(request, "embedding", req.model)
        body = {"model": req.model, "input": req.input}
        if req.dimensions:
            body["dimensions"] = req.dimensions
        result, u, degraded = await _forward("embedding", json_body=body)
        metrics_manager.record_model_usage(req.model, f"embedding:{u.name}")
        _vk_spend(vk, "embedding", req.model, u.name, started, result)
        return _json_or_502(result, u, degraded)
    except Exception as e:
        error_response = await error_handler.handle(
            e,
            context={
                "model": req.model,
                "capability": "embedding",
                "operation": "proxy",
            },
        )
        raise HTTPException(status_code=error_response["status_code"], detail=error_response)


# ── 2) POST /v1/rerank ─────────────────────────────────────


@router.post("/v1/rerank")
async def rerank(req: RerankRequest, request: Request):
    """重排序（Cohere 风格对外；上游 Qwen3-Reranker 生成式打分；vk 白名单+预算+记账）"""
    started = time.time()
    try:
        vk = await _vk_gate(request, "rerank", req.model)
        # Qwen3-Reranker 生成式打分：批量 prompt → completions(max_tokens=1, logprobs)
        prompts = [_rerank_prompt(req.query, doc) for doc in req.documents]
        score_body = {
            "model": req.model,
            "prompt": prompts,
            "max_tokens": 1,
            "temperature": 0,
            "logprobs": 20,
        }
        result, u, degraded = await _forward("rerank", json_body=score_body)
        choices = result.get("choices", [])
        items = []
        for i, ch in enumerate(choices):
            score = _yes_probability(ch)
            items.append({"index": i, "relevance_score": score})
        items.sort(key=lambda x: x["relevance_score"], reverse=True)
        top_n = req.top_n or len(items)
        payload = {
            "model": req.model,
            "results": items[:top_n],
            "usage": result.get("usage", {}),
        }
        metrics_manager.record_model_usage(req.model, f"rerank:{u.name}")
        _vk_spend(vk, "rerank", req.model, u.name, started, payload)
        return _json_or_502(payload, u, degraded)
    except Exception as e:
        error_response = await error_handler.handle(
            e,
            context={"model": req.model, "capability": "rerank", "operation": "proxy"},
        )
        raise HTTPException(status_code=error_response["status_code"], detail=error_response)


# ── 3) POST /v1/audio/transcriptions ───────────────────────


@router.post("/v1/audio/transcriptions")
async def transcriptions(request: Request, file: UploadFile = File(...), model: str = Form(...)):
    """语音转写（Whisper 风格 multipart；上游池 capability=asr；vk 白名单+预算+记账）"""
    started = time.time()
    try:
        vk = await _vk_gate(request, "asr", model)
        content = await file.read()
        files = {
            "file": (
                file.filename,
                content,
                file.content_type or "application/octet-stream",
            )
        }
        data = {"model": model}
        result, u, degraded = await _forward("asr", data=data, files=files)
        metrics_manager.record_model_usage(model, f"asr:{u.name}")
        _vk_spend(vk, "asr", model, u.name, started, result)
        return _json_or_502(result, u, degraded)
    except Exception as e:
        error_response = await error_handler.handle(
            e, context={"model": model, "capability": "asr", "operation": "proxy"}
        )
        raise HTTPException(status_code=error_response["status_code"], detail=error_response)


# ── 4) POST /v1/ocr ────────────────────────────────────────


@router.post("/v1/ocr")
async def ocr(
    request: Request,
    file: UploadFile = File(...),
    model: Optional[str] = Form(None),
    prompt: Optional[str] = Form(None),
):
    """图文识别（multipart 图片 → VLM chat 适配；上游池 capability=ocr；vk 白名单+预算+记账）

    2026-09-24 改造：vLLM 无原生 /v1/ocr 路由，OCR 上游=多模态 VLM（如 MiniCPM-V），
    图片转 base64 data URL 走 /v1/chat/completions，取回复文本为 OCR 结果。
    """
    started = time.time()
    try:
        vk = await _vk_gate(request, "ocr", model or "ocr")
        content = await file.read()
        mime = file.content_type or "image/png"
        if not mime.startswith("image/"):
            mime = "image/png"
        b64 = base64.b64encode(content).decode("ascii")
        ocr_prompt = prompt or (
            "Extract all text from this image. Output the recognized text as plain text, "
            "preserving natural reading order. Output no explanations."
        )
        body = {
            "model": model or "ocr",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime};base64,{b64}"},
                        },
                        {"type": "text", "text": ocr_prompt},
                    ],
                }
            ],
            "max_tokens": 2048,
        }
        result, u, degraded = await _forward("ocr", json_body=body)
        text = ""
        choices = result.get("choices") or []
        if choices:
            msg = choices[0].get("message") or {}
            content_out = msg.get("content")
            if isinstance(content_out, list):  # 某些 VLM 返回分段 content
                text = "".join(p.get("text", "") for p in content_out if isinstance(p, dict))
            else:
                text = content_out or ""
        payload = {"text": text.strip(), "model": u.models[0] if u.models else "ocr"}
        metrics_manager.record_model_usage(model or "ocr", f"ocr:{u.name}")
        _vk_spend(vk, "ocr", model or "ocr", u.name, started, result)
        return _json_or_502(payload, u, degraded)
    except Exception as e:
        error_response = await error_handler.handle(
            e,
            context={
                "model": model or "ocr",
                "capability": "ocr",
                "operation": "proxy",
            },
        )
        raise HTTPException(status_code=error_response["status_code"], detail=error_response)
