# file: main.py
# description: FastAPI 应用入口文件
# author: YanYuCloudCube Team
# version: v1.0.0
# created: 2026-03-21
# updated: 2026-04-04
# status: active
# tags: [api],[main],[entry]

# @file main.py
# @description FastAPI 主应用 - 模型管理 API 端点
# @author YanYuCloudCube Team <admin@0379.email>
# @version v1.0.0
# @created 2026-03-14
# @updated 2026-03-14
# @status stable
# @license MIT
# @copyright Copyright (c) 2026 YanYuCloudCube Team
# @tags python,fastapi,api

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import List, Optional

import psutil

from app.api import (
    a2a,
    agent,
    chat,
    documents,
    knowledge_base,
    mcp,
    proxy,
    rag,
    video_tasks,
    websocket,
)
from app.config import settings
from app.db import ModelRegistry, async_session

logger = logging.getLogger(__name__)
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.errors.handler import error_handler
from app.middleware import AuthMiddleware, RateLimitMiddleware, VersioningMiddleware
from app.models import ErrorRecord, ModelConfig, ModelStat, PingResponse, UsageSummary

app = FastAPI(
    title="YYC³ 统一模型网关",
    description="""
## 🎯 核心功能

### 支持的Provider
- **智谱GLM**: glm-4-flash, glm-4-plus（云端API）
- **Ollama**: llama3.2, codegeex4, qwen2.5等（本地部署）

### 主要接口
- `/v1/chat/completions` - 聊天完成（OpenAI兼容）
- `/v1/models` - 模型列表
- `/ws/chat` - WebSocket流式聊天
- `/ws/monitor` - 实时监控

### 知识库功能
- `/v1/knowledge-bases` - 知识库管理（创建、查询、更新、删除）
- `/v1/documents` - 文档管理（上传、解析、切片、向量化）
- `/v1/rag/search` - RAG语义检索
- `/v1/rag/ask` - 基于知识库的问答

### 认证方式
- **API Key**: 在请求头添加 `X-API-Key: YOUR_API_KEY`
- **JWT**: 在请求头添加 `Authorization: Bearer YOUR_JWT_TOKEN`

### 使用示例
```bash
# 获取模型列表
curl -H "X-API-Key: YOUR_API_KEY" https://api.0379.world/v1/models

# 聊天请求
curl -X POST https://api.0379.world/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: YOUR_API_KEY" \\
  -d '{
    "model": "llama3.2",
    "messages": [{"role": "user", "content": "你好"}]
  }'

# 创建知识库
curl -X POST https://api.0379.world/v1/knowledge-bases \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: YOUR_API_KEY" \\
  -d '{
    "name": "技术文档库",
    "description": "包含所有技术文档"
  }'

# 上传文档
curl -X POST https://api.0379.world/v1/documents/upload?knowledge_base_id=xxx \\
  -H "X-API-Key: YOUR_API_KEY" \\
  -F "file=@document.pdf"

# RAG检索
curl -X POST https://api.0379.world/v1/rag/search \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: YOUR_API_KEY" \\
  -d '{
    "query": "如何部署模型？",
    "knowledge_base_ids": ["xxx"],
    "top_k": 5
  }'
```
    """,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    servers=[
        {"url": "https://api.0379.world", "description": "Production"},
    ],
)

Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# P0: 补全 OpenAPI Security Scheme，让 Swagger UI 出现 Authorize 按钮
from fastapi.openapi.utils import get_openapi


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        servers=app.servers,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "APIKey": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "YYC³ API Key 认证",
        },
        "Bearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT Token 认证",
        },
    }
    openapi_schema["security"] = [{"APIKey": []}, {"Bearer": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.on_event("startup")
async def validate_critical_config():
    """启动时校验关键配置，防止生产环境使用默认值"""
    logger = logging.getLogger(__name__)

    critical_checks = [
        (
            "JWT_SECRET_KEY",
            settings.jwt_secret_key,
            lambda v: v and v != "change_me_in_production",
        ),
        ("API_KEYS", settings.api_keys, lambda v: bool(v)),
        (
            "POSTGRES_PASSWORD",
            settings.db_password,
            lambda v: v and v != "change_me_in_production",
        ),
        (
            "REDIS_PASSWORD",
            settings.redis_password,
            lambda v: v and v != "change_me_in_production",
        ),
    ]

    errors = []
    warnings = []

    for name, value, check in critical_checks:
        if not check(value):
            errors.append(name)

    if errors:
        msg = f"关键配置缺失或使用默认值: {', '.join(errors)}"
        if settings.auth_enabled:
            logger.critical(msg)
            raise RuntimeError(msg)
        else:
            logger.warning(f"[非生产模式] {msg}")

    # ── 非关键但建议配置的项 ──
    if not settings.zhipu_api_key:
        warnings.append("ZHIPU_API_KEY")
    if not settings.deepseek_api_key:
        warnings.append("DEEPSEEK_API_KEY")
    if not settings.openai_api_key:
        warnings.append("OPENAI_API_KEY")

    if not errors and warnings:
        logger.info(f"以下 API Key 未配置（按需忽略）: {', '.join(warnings)}")

    logger.info("配置校验通过，服务启动正常")


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AuthMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(VersioningMiddleware)

START_TIME = time.time()

app.include_router(chat.router, prefix="/v1", tags=["💬 聊天"])
app.include_router(agent.router, tags=["🤖 AI Family Agent编排"])
app.include_router(a2a.router, tags=["🔗 A2A协议"])
app.include_router(mcp.router, prefix="/v1", tags=["🔧 MCP工具"])
app.include_router(websocket.router, tags=["🔌 WebSocket"])
app.include_router(knowledge_base.router, tags=["📚 知识库管理"])
app.include_router(documents.router, tags=["📄 文档管理"])
app.include_router(rag.router, tags=["🔍 RAG检索"])
app.include_router(proxy.router, tags=["🧩 能力代理(embeddings/rerank/asr/ocr)"])
app.include_router(video_tasks.router, tags=["🎬 视频任务(MiniMax-H3异步)"])

# vk 管理看板（零依赖单页，受全局 Auth 中间件保护）
from app.services.admin_ui import router as admin_ui_router  # noqa: E402

app.include_router(admin_ui_router, tags=["📊 管理看板"])


@app.get("/health")
async def health_check():
    """
    健康检查端点

    返回系统状态、服务可用性、资源使用情况（并发检查）
    """
    from app.utils.metrics import metrics_manager

    async def _check_ollama():
        try:
            import httpx

            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get("http://localhost:11434/api/tags")
                return {
                    "status": "healthy" if resp.status_code == 200 else "unhealthy",
                    "latency_ms": int(resp.elapsed.total_seconds() * 1000),
                }
        except Exception:
            return {"status": "unreachable"}

    async def _check_redis():
        try:
            from app.cache import redis_client

            await redis_client.ping()
            return {"status": "healthy"}
        except Exception:
            return {"status": "unreachable"}

    async def _check_postgresql():
        try:
            from sqlalchemy import text as sa_text

            async with async_session() as session:
                await session.execute(sa_text("SELECT 1"))
                return {"status": "healthy"}
        except Exception:
            return {"status": "unreachable"}

    # 并发检查所有外部服务
    import asyncio

    ollama_result, redis_result, pg_result = await asyncio.gather(
        _check_ollama(),
        _check_redis(),
        _check_postgresql(),
        return_exceptions=True,
    )

    services = {
        "ollama": (
            ollama_result if not isinstance(ollama_result, BaseException) else {"status": "error"}
        ),
        "zhipu": {
            "status": "configured" if settings.zhipu_api_key else "not_configured",
        },
        "redis": (
            redis_result if not isinstance(redis_result, BaseException) else {"status": "error"}
        ),
        "postgresql": (
            pg_result if not isinstance(pg_result, BaseException) else {"status": "error"}
        ),
    }

    # 系统资源
    system = {
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage("/").percent,
    }

    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "2.0.0",
        "uptime_seconds": int(time.time() - START_TIME),
        "services": services,
        "system": system,
        "metrics": {
            "active_requests": metrics_manager.get_active_requests(),
            "total_requests": metrics_manager.get_total_requests(),
            "cache_hit_rate": metrics_manager.get_cache_hit_rate(),
        },
    }


@app.get("/healthz")
async def healthz():
    """轻量存活探针（供监控/负载均衡高频探活）

    与 /health 的区别：不做外部服务依赖检查，仅确认进程存活，
    开销极小，适合 Prometheus/Traefik/监控探活高频调用。
    """
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": int(time.time() - START_TIME),
    }


@app.get("/v1/ping", response_model=PingResponse)
async def ping():
    """健康检查端点"""
    return PingResponse(status="ok")


@app.get("/v1/cache/stats")
async def get_cache_stats():
    """获取缓存统计（命中率、操作计数）"""
    from app.utils import cache_manager

    return cache_manager.get_stats()


@app.get("/v1/cache/info")
async def get_cache_info():
    """获取缓存详细信息（条目数、LRU淘汰状态、TTL配置）"""
    from app.cache import get_cache_info

    return await get_cache_info()


@app.post("/v1/cache/invalidate/{model_name}")
async def invalidate_cache(model_name: str):
    """按模型名主动失效缓存"""
    from app.cache import invalidate_model_cache

    count = await invalidate_model_cache(model_name)
    return {"model": model_name, "invalidated": count}


@app.delete("/v1/cache/all")
async def clear_cache():
    """清空所有LLM缓存"""
    from app.cache import clear_all_cache

    count = await clear_all_cache()
    return {"cleared": count}


@app.get("/v1/router/stats")
async def get_router_stats():
    """获取路由统计（上游池快照 + 节点 EWMA 动态权重）"""
    from app.services.model_router import model_router
    from app.services.upstream_registry import registry as upstream_registry

    return {
        "upstream_pool": upstream_registry.snapshot(),
        "nodes": model_router.get_node_stats(),
    }


@app.get("/v1/router/health")
async def get_router_health():
    """触发一次路由器健康检查并返回结果"""
    from app.services.model_router import model_router

    await model_router.health_check()
    return model_router.get_node_stats()


@app.get("/v1/model/type")
async def get_model_type(model: str = Query(...)):
    """
    获取模型后端类型（用于 Traefik/HAProxy 的 GPU 感知路由）

    返回:
    - local_cpu: Ollama CPU 推理
    - local_gpu: Ollama GPU 推理（DGX Spark）
    - openai: OpenAI API
    - zhipu: 智谱 AI API
    - deepseek: DeepSeek API
    - unknown: 未注册模型
    """
    try:
        async with async_session() as session:
            from sqlalchemy import select

            from app.db import ModelRegistry

            result = await session.execute(
                select(ModelRegistry.backend_type, ModelRegistry.backend_name)
                .where(ModelRegistry.id == model)
                .where(ModelRegistry.enabled.is_(True))
            )
            row = result.first()
            if row:
                return {
                    "model": model,
                    "backend_type": row.backend_type,
                    "backend_name": row.backend_name,
                }
    except Exception:
        pass

    # 回退：根据模型名前缀推断
    if any(model.startswith(p) for p in ["glm-4", "zhipu:"]):
        return {"model": model, "backend_type": "zhipu", "backend_name": model}
    if any(model.startswith(p) for p in ["gpt-", "openai:"]):
        return {"model": model, "backend_type": "openai", "backend_name": model}
    if any(model.startswith(p) for p in ["deepseek-", "deepseek:"]):
        return {"model": model, "backend_type": "deepseek", "backend_name": model}
    if any(model.startswith(p) for p in ["llama", "codegeex", "qwen", "local:", "ollama:"]):
        return {"model": model, "backend_type": "local_cpu", "backend_name": model}

    return JSONResponse(status_code=404, content={"error": "Model not found", "model": model})


@app.get("/v1/versions")
async def get_api_versions():
    """获取所有API版本状态（current/deprecated/sunset）"""
    from app.middleware.versioning import VersioningMiddleware

    return VersioningMiddleware.get_version_info()


# ── 默认模型配置 ──────────────────────────────────────────
# 可通过数据库 model_registry 表动态扩展（Ollama模型）
DEFAULT_MODELS = [
    # 智谱GLM
    ModelConfig(
        id="glm-4-flash",
        display_name="智谱GLM-4 Flash",
        backend="zhipu",
        enabled=True,
        max_tokens=128000,
        temperature=0.7,
        top_p=0.9,
        cost_per_1k_tokens=0.001,
    ),
    ModelConfig(
        id="glm-4-plus",
        display_name="智谱GLM-4 Plus",
        backend="zhipu",
        enabled=True,
        max_tokens=128000,
        temperature=0.7,
        top_p=0.9,
        cost_per_1k_tokens=0.05,
    ),
    # DeepSeek
    ModelConfig(
        id="deepseek-chat",
        display_name="DeepSeek Chat",
        backend="deepseek",
        enabled=True,
        max_tokens=64000,
        temperature=0.7,
        top_p=0.9,
        cost_per_1k_tokens=0.001,
    ),
    ModelConfig(
        id="deepseek-coder",
        display_name="DeepSeek Coder",
        backend="deepseek",
        enabled=True,
        max_tokens=16000,
        temperature=0.7,
        top_p=0.9,
        cost_per_1k_tokens=0.001,
    ),
    # Ollama本地（默认）
    ModelConfig(
        id="llama3.2",
        display_name="Llama 3.2 (本地)",
        backend="ollama",
        enabled=True,
        max_tokens=128000,
        temperature=0.7,
        top_p=0.9,
        cost_per_1k_tokens=0.0,
    ),
    ModelConfig(
        id="codegeex4",
        display_name="CodeGeeX4 (本地)",
        backend="ollama",
        enabled=True,
        max_tokens=128000,
        temperature=0.7,
        top_p=0.9,
        cost_per_1k_tokens=0.0,
    ),
    ModelConfig(
        id="qwen2.5",
        display_name="通义千问 2.5 (本地)",
        backend="ollama",
        enabled=True,
        max_tokens=128000,
        temperature=0.7,
        top_p=0.9,
        cost_per_1k_tokens=0.0,
    ),
]

# DB注册的默认Ollama模型ID（避免重复）
_DEFAULT_OLLAMA_IDS = {"llama3.2", "codegeex4", "qwen2.5"}


@app.get("/v1/models", response_model=List[ModelConfig])
async def list_models():
    """
    获取可用模型列表

    支持的Provider：
    - zhipu: 智谱GLM（glm-4-flash, glm-4-plus）
    - deepseek: DeepSeek（deepseek-chat, deepseek-coder）
    - ollama: 本地模型（llama3.2, codegeex4, qwen2.5等）
    数据库动态注册的模型自动附加
    """
    models = list(DEFAULT_MODELS)

    # 上游池模型（OPENAI_COMPATIBLE_UPSTREAMS 注入）
    from app.services.upstream_registry import registry as upstream_registry

    for u in upstream_registry.upstreams.values():
        if u.capability != "chat":
            continue
        for m in u.models:
            if "*" in m or "?" in m:
                m = m.replace("*", "").replace("?", "") or u.name
            models.append(
                ModelConfig(
                    id=m,
                    display_name=f"{m} @ {u.name}",
                    backend="upstream",
                    enabled=True,
                    max_tokens=128000,
                    temperature=0.7,
                    top_p=0.9,
                    cost_per_1k_tokens=0.0,
                )
            )

    # 从数据库加载动态注册的Ollama模型
    try:
        async with async_session() as session:
            result = await session.execute(
                select(ModelRegistry.id, ModelRegistry.display_name)
                .where(ModelRegistry.enabled.is_(True))
                .where(ModelRegistry.backend_type == "ollama")
            )
            for row in result:
                if row.id not in _DEFAULT_OLLAMA_IDS:
                    models.append(
                        ModelConfig(
                            id=row.id,
                            display_name=row.display_name,
                            backend="ollama",
                            enabled=True,
                            max_tokens=128000,
                            temperature=0.7,
                            top_p=0.9,
                            cost_per_1k_tokens=0.0,
                        )
                    )
    except Exception:
        pass

    return models


@app.get("/v1/models/stats", response_model=List[ModelStat])
async def get_stats():
    """获取所有模型统计信息（上游池为真实 EWMA 数据，云/Ollama 为 DB 用量）"""
    from app.services.upstream_registry import registry as upstream_registry

    stats: dict = {}
    # 上游池：真实延迟/错误率
    for u in upstream_registry.upstreams.values():
        stats[u.name] = ModelStat(
            model_id=u.name,
            usage_count=u.total_requests,
            avg_latency_ms=round(u.ewma_latency, 1),
            error_rate=round(u.ewma_error_rate, 4),
            total_tokens=0,
        )
    # DB 用量（DB 不可达时仅返回上游数据）
    try:
        async with async_session() as session:
            from sqlalchemy import func

            from app.db import UsageLog

            result = await session.execute(
                select(
                    UsageLog.model,
                    func.count(UsageLog.id).label("usage_count"),
                    func.sum(UsageLog.total_tokens).label("total_tokens"),
                ).group_by(UsageLog.model)
            )
            for row in result:
                if row.model in stats:
                    stats[row.model].usage_count += row.usage_count or 0
                    stats[row.model].total_tokens += row.total_tokens or 0
                else:
                    stats[row.model] = ModelStat(
                        model_id=row.model,
                        usage_count=row.usage_count or 0,
                        avg_latency_ms=0.0,
                        error_rate=0.0,
                        total_tokens=row.total_tokens or 0,
                    )
    except Exception as e:
        logger.warning(f"models/stats DB 查询失败（仅返回上游池数据）: {e}")
    return list(stats.values())


@app.get("/v1/models/errors", response_model=List[ErrorRecord])
async def get_errors():
    """获取上游池错误记录（真实数据）"""
    from datetime import datetime, timezone

    from app.services.upstream_registry import registry as upstream_registry

    out = []
    for i, e in enumerate(upstream_registry.errors()):
        out.append(
            ErrorRecord(
                id=f"upstream-{i}",
                timestamp=datetime.now(timezone.utc),
                model_id=e["upstream"],
                error_type="internal",
                message=e["error"] or "unknown",
                stack=None,
            )
        )
    return out


@app.get("/v1/models/summary", response_model=UsageSummary)
async def get_summary():
    """获取使用摘要"""
    async with async_session() as session:
        from sqlalchemy import func

        from app.db import UsageLog

        result = await session.execute(
            select(
                func.count(UsageLog.id).label("total_requests"),
                func.sum(UsageLog.total_tokens).label("total_tokens"),
            )
        )
        row = result.first()
        total_requests = row.total_requests if row and row.total_requests else 0
        total_tokens = row.total_tokens if row and row.total_tokens else 0
        return UsageSummary(
            total_requests=total_requests,
            total_tokens=total_tokens,
            cost_usd=0.0,
        )


# ── P0-2: 上游池主动验活（学 one-api 渠道自愈）────────────────

_probe_task: Optional[asyncio.Task] = None


async def _probe_loop():
    """周期探活：probe_interval_seconds 一轮；连续 2 败 degraded 权重减半，恢复复原"""
    from app.services.upstream_registry import registry as upstream_registry

    while True:
        await asyncio.sleep(settings.probe_interval_seconds)
        try:
            results = await upstream_registry.probe_all()
            degraded = [r["name"] for r in results if r["probe_degraded"]]
            if degraded:
                logger.warning(f"验活降级上游: {', '.join(degraded)}")
        except Exception as e:
            logger.warning(f"验活轮次异常（下轮继续）: {e}")


@app.post("/v1/admin/upstreams/probe")
async def probe_upstreams():
    """手动触发一轮上游验活（受全局 Auth 中间件保护），返回各上游健康明细"""
    from app.services.upstream_registry import registry as upstream_registry

    return {"probes": await upstream_registry.probe_all()}


# ── P0-1 收口：虚拟密钥管理端点（学 litellm /key 管理面）──────


class VKCreateRequest(BaseModel):
    name: str
    owner: str = "yanyu"
    model_whitelist: List[str] = []
    monthly_budget_usd: float = 0.0
    rate_limit_tpm: int = 0
    expires_at: Optional[str] = None
    metadata: Optional[dict] = None


@app.get("/v1/providers")
async def list_providers():
    """供应商运维面：已登记的 provider 实现（配置 OPENAI_COMPATIBLE_UPSTREAMS.provider 用）"""
    from app.services.providers.registry import known_providers

    return {"providers": known_providers()}


@app.post("/v1/admin/virtual-keys")
async def admin_vk_create(req: VKCreateRequest):
    """创建虚拟密钥。明文只在本响应出现一次，请妥善保管"""
    from app.services.virtual_key_manager import vk_create

    try:
        return await vk_create(
            name=req.name,
            owner=req.owner,
            model_whitelist=req.model_whitelist,
            monthly_budget_usd=req.monthly_budget_usd,
            rate_limit_tpm=req.rate_limit_tpm,
            expires_at=req.expires_at,
            metadata=req.metadata,
        )
    except Exception as e:
        error_response = await error_handler.handle(e, context={"operation": "vk_create"})
        raise HTTPException(status_code=error_response["status_code"], detail=error_response)


@app.get("/v1/admin/virtual-keys")
async def admin_vk_list(owner: Optional[str] = None, active_only: bool = False):
    """列虚拟密钥（key 脱敏为前 8 位 hint）"""
    from app.services.virtual_key_manager import vk_list

    try:
        return {"keys": await vk_list(owner=owner, include_disabled=not active_only)}
    except Exception as e:
        error_response = await error_handler.handle(e, context={"operation": "vk_list"})
        raise HTTPException(status_code=error_response["status_code"], detail=error_response)


class VKUpdateRequest(BaseModel):
    status: Optional[str] = None
    monthly_budget_usd: Optional[float] = None
    rate_limit_tpm: Optional[int] = None
    model_whitelist: Optional[List[str]] = None


@app.patch("/v1/admin/virtual-keys/{key_id}")
async def admin_vk_update(key_id: str, req: VKUpdateRequest):
    """更新虚拟密钥：启停（status=active|disabled）/ 编辑预算、TPM、模型白名单"""
    from app.services.virtual_key_manager import vk_update_fields, vk_update_status

    if req.status is None and (
        req.monthly_budget_usd is None
        and req.rate_limit_tpm is None
        and req.model_whitelist is None
    ):
        raise HTTPException(
            status_code=422,
            detail="至少提供 status / monthly_budget_usd / rate_limit_tpm / model_whitelist 之一",
        )

    try:
        updated = {"status": False, "fields": False}
        if req.status is not None:
            updated["status"] = await vk_update_status(key_id, req.status)
        if (
            req.monthly_budget_usd is not None
            or req.rate_limit_tpm is not None
            or req.model_whitelist is not None
        ):
            updated["fields"] = await vk_update_fields(
                key_id,
                monthly_budget_usd=req.monthly_budget_usd,
                rate_limit_tpm=req.rate_limit_tpm,
                model_whitelist=req.model_whitelist,
            )
        return {"updated": updated, "key_id": key_id}
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        error_response = await error_handler.handle(e, context={"operation": "vk_update"})
        raise HTTPException(status_code=error_response["status_code"], detail=error_response)


@app.delete("/v1/admin/virtual-keys/{key_id}")
async def admin_vk_delete(key_id: str):
    """删除虚拟密钥（消费流水保留，key_id 置空以存审计）"""
    from app.services.virtual_key_manager import vk_delete

    try:
        deleted = await vk_delete(key_id)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"虚拟密钥不存在: {key_id}")
        return {"deleted": True, "key_id": key_id}
    except HTTPException:
        raise
    except Exception as e:
        error_response = await error_handler.handle(e, context={"operation": "vk_delete"})
        raise HTTPException(status_code=error_response["status_code"], detail=error_response)


@app.get("/v1/admin/virtual-keys/{key_id}/usage")
async def admin_vk_usage(key_id: str, days: int = 30):
    """用量查询：近 N 天按模型聚合成本（供看板/预算复盘）"""
    from app.services.virtual_key_manager import vk_usage

    try:
        return await vk_usage(key_id, days=days)
    except Exception as e:
        error_response = await error_handler.handle(e, context={"operation": "vk_usage"})
        raise HTTPException(status_code=error_response["status_code"], detail=error_response)


# ── 协同事务价格表管理（A2A 成本直报运行时覆盖；内存态，对齐 MODEL_PRICES_JSON 语义）──


class TaskPriceRequest(BaseModel):
    price_usd: float = Field(..., ge=0, description="每任务固定成本（USD）")


@app.get("/v1/admin/pricing/task-types")
async def admin_pricing_task_types():
    """列协同事务任务类型价格表（TASK_TYPE_PRICES 运行时态，X-A2A-Cost 取值源）"""
    from app.services.pricing import TASK_TYPE_PRICES

    return {"task_types": dict(TASK_TYPE_PRICES)}


@app.put("/v1/admin/pricing/task-types/{task_type}")
async def admin_pricing_task_type_upsert(task_type: str, req: TaskPriceRequest):
    """登记/更新任务类型单价（内存即时生效 + PG task_prices 持久；未知类型也可预置）

    persisted=false 表示 PG 未落库（表未迁移/DB 不可达）——内存价已生效但重启丢失，
    提示运维执行 004_task_prices.sql 迁移。
    """
    from app.services import pricing as pricing_svc

    try:
        persisted = await pricing_svc.upsert_task_price_persisted(task_type, req.price_usd)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return {
        "updated": True,
        "task_type": task_type,
        "price_usd": req.price_usd,
        "persisted": persisted,
    }


@app.on_event("startup")
async def load_task_prices_from_db():
    """协同事务价格表启动加载：PG task_prices 覆盖内存默认（best-effort 不阻断）"""
    from app.services import pricing as pricing_svc

    await pricing_svc.load_task_prices_from_db()


@app.on_event("startup")
async def start_probe_loop():
    global _probe_task
    if settings.probe_enabled and settings.router_enabled:
        _probe_task = asyncio.create_task(_probe_loop())
        logger.info(
            f"上游验活已启动（间隔 {settings.probe_interval_seconds}s，PROBE_ENABLED=false 可关闭）"
        )
    # ── P0-1: 虚拟密钥记账管道（批量落库 spend_logs）──
    from app.services.virtual_key_manager import vk_manager

    await vk_manager.ensure_tables()  # sqlite 本地模式自建表（PG 跳过，由 003 SQL 迁移管）
    await vk_manager.start_ledger()


@app.on_event("shutdown")
async def stop_probe_loop():
    global _probe_task
    if _probe_task is not None:
        _probe_task.cancel()
        _probe_task = None
    from app.services.virtual_key_manager import vk_manager

    await vk_manager.stop_ledger()


@app.on_event("startup")
async def start_agent_worker():
    """AI Family 内置编排 Worker（AGENT_WORKER_ENABLED=false 或外置 Worker 部署时可关闭）"""
    from app.api import agent as agent_module

    agent_module.start_worker()


@app.on_event("shutdown")
async def stop_agent_worker():
    from app.api import agent as agent_module

    await agent_module.stop_worker()


@app.on_event("startup")
async def start_a2a_registry():
    """A2A 启动：审计 sink 注入智云守护 + 内置编队 Agent Card 注册/心跳（A2A_ENABLED 控制）"""
    from app.services import a2a_protocol

    a2a_protocol.start_registry()


@app.on_event("shutdown")
async def stop_a2a_registry():
    from app.services import a2a_protocol

    await a2a_protocol.stop_registry()


@app.on_event("startup")
async def start_a2a_result_consumer():
    """A2A 结果流消费端：编排器聚合回执 + XAUTOCLAIM 挂起回收
    （A2A_ENABLED × A2A_RESULT_CONSUMER_ENABLED 双控；独立编排器部署时可在网关侧关闭）"""
    from app.services import a2a_result

    a2a_result.start_result_consumer()


@app.on_event("shutdown")
async def stop_a2a_result_consumer():
    from app.services import a2a_result

    await a2a_result.stop_result_consumer()


@app.on_event("startup")
async def start_a2a_audit_shipper():
    """A2A 审计流 Loki 消费端：孤儿/死信审计可检索可告警
    （A2A_ENABLED × A2A_AUDIT_LOKI_ENABLED 双控，缺省关闭）"""
    from app.services import a2a_audit

    a2a_audit.start_audit_shipper()


@app.on_event("shutdown")
async def stop_a2a_audit_shipper():
    from app.services import a2a_audit

    await a2a_audit.stop_audit_shipper()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
