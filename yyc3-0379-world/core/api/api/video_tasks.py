# file: video_tasks.py
# description: 第五能力——MiniMax-H3 数字人视频异步任务 API（Phase 2.3，docs/11+审核论证定稿）
# author: YanYuCloudCube Team
# version: v1.0.0
# created: 2026-09-24
# status: active
# tags: [api],[video],[tasks],[async]
#
# 设计（2026-09-14 审核论证四修正落地）：
#   - 异步任务式（修正②）：POST 创建即返回 queued；生成由 Mac runner 夜间窗口执行（修正①）
#   - 公共端点（API Key + vk 门控）：POST/GET /v1/video/tasks、GET /v1/video/tasks/{id}[/result]
#   - runner 端点（/v1/admin/** 自动受 ADMIN_API_KEYS 保护）：claim/heartbeat/result/failure
#   - 租约机制：claim 取走 → running + lease_until；heartbeat 续租；过期回收（attempts<2 重排队，
#     否则 failed）——防 runner 掉线任务卡死
#   - 存储：Redis（任务 JSON 7 天 TTL；结果 mp4 ≤16MB 内联存储，NAS 归档为持久副本）
#   - 归档双速制（修正③）由 runner 侧完成；DGX 迁移（修正④）排 GLM 线后
"""
@file: app/api/video_tasks.py
@description: MiniMax-H3 数字人视频异步任务端点（第五能力）
@author: YanYuCloudCube Team <admin@0379.email>
@license: MIT
@copyright Copyright (c) 2026 YanYuCloudCube Team
"""

import base64
import json
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field

from app.api.proxy import _vk_gate
from app.cache import redis_client

logger = logging.getLogger(__name__)

router = APIRouter()

_TASK_TTL = 7 * 86400  # 任务记录 7 天
_RESULT_TTL = 7 * 86400  # 结果视频 7 天（NAS 归档为持久层）
_MAX_REF_IMAGE_B = 8 * 1024 * 1024  # 参考图 ≤8MB
_MAX_RESULT_B = 16 * 1024 * 1024  # 回传视频 ≤16MB
_MAX_ATTEMPTS = 2  # 租约过期重试上限

_KEY_QUEUE = "video:queue"  # FIFO：RPUSH 入队 / LPOP 领取
_KEY_INDEX = "video:tasks:ids"  # 全量 id 索引（SET）
_KEY_TASK = "video:task:{id}"
_KEY_RESULT = "video:result:{id}"

_VALID_QUALITY = ("preview", "full")


# ── Redis 薄存储层（测试桩替点）────────────────────────────


async def _store_task(task: Dict, ttl: int = _TASK_TTL) -> None:
    await redis_client.set(_KEY_TASK.format(id=task["id"]), json.dumps(task), ex=ttl)


async def _load_task(task_id: str) -> Optional[Dict]:
    raw = await redis_client.get(_KEY_TASK.format(id=task_id))
    return json.loads(raw) if raw else None


async def _queue_push(task_id: str) -> None:
    await redis_client.rpush(_KEY_QUEUE, task_id)


async def _queue_pop() -> Optional[str]:
    task_id = await redis_client.lpop(_KEY_QUEUE)
    return task_id if task_id else None


async def _queue_len() -> int:
    return int(await redis_client.llen(_KEY_QUEUE))


async def _index_add(task_id: str) -> None:
    await redis_client.sadd(_KEY_INDEX, task_id)


async def _index_all() -> List[str]:
    return [x for x in await redis_client.smembers(_KEY_INDEX)]


async def _store_result(task_id: str, data: bytes, ttl: int = _RESULT_TTL) -> None:
    """结果视频以 base64 存储（redis_client decode_responses=True，二进制直存 GET 会解码崩溃）"""
    await redis_client.set(
        _KEY_RESULT.format(id=task_id), base64.b64encode(data).decode("ascii"), ex=ttl
    )


async def _load_result(task_id: str) -> Optional[bytes]:
    raw = await redis_client.get(_KEY_RESULT.format(id=task_id))
    if not raw:
        return None
    try:
        return base64.b64decode(raw)
    except Exception:
        return None


# ── 模型 ────────────────────────────────────────────────────


class VideoTaskCreate(BaseModel):
    """创建视频任务请求"""

    prompt: Optional[str] = Field(
        None, max_length=4000, description="生成提示词（空=runner 默认数字人模板）"
    )
    quality: str = Field("preview", description="preview=快预览档 / full=全质量档")
    seed: Optional[int] = Field(None, ge=0, le=2**31 - 1)
    ref_image_b64: Optional[str] = Field(
        None, description="参考图 base64（≤8MB，空=runner 端默认人物）"
    )
    ref_image_name: Optional[str] = Field(
        None, max_length=64, description="参考图文件名（如 person_a.png）"
    )


class ClaimRequest(BaseModel):
    runner: str = Field(..., max_length=64, description="runner 标识（如 yyc3-22-mac）")
    lease_minutes: int = Field(180, ge=5, le=720)


class FailureRequest(BaseModel):
    error: str = Field(..., max_length=2000)


class HeartbeatRequest(BaseModel):
    runner: str = Field(..., max_length=64)
    lease_minutes: int = Field(30, ge=5, le=720)


def _public_view(t: Dict, include_result_url: bool = True) -> Dict:
    """对外视图（剥离参考图 base64 大字段）"""
    view = {
        "id": t["id"],
        "status": t["status"],
        "quality": t.get("quality"),
        "created_at": t.get("created_at"),
        "updated_at": t.get("updated_at"),
        "attempts": t.get("attempts", 0),
        "error": t.get("error"),
    }
    if include_result_url and t.get("status") == "succeeded":
        view["result_url"] = f"/v1/video/tasks/{t['id']}/result"
        view["archive_path"] = t.get("archive_path")
        view["duration_seconds"] = t.get("duration_seconds")
    return view


async def _sweep_expired() -> int:
    """回收租约过期的 running 任务：attempts<_MAX_ATTEMPTS 重排队，否则 failed"""
    swept = 0
    now = time.time()
    for task_id in await _index_all():
        t = await _load_task(task_id)
        if not t or t.get("status") != "running":
            continue
        if t.get("lease_until", 0) > now:
            continue
        t["attempts"] = t.get("attempts", 0) + 1
        if t["attempts"] >= _MAX_ATTEMPTS:
            t["status"] = "failed"
            t["error"] = f"runner 租约过期且达重试上限（lease_until={t.get('lease_until')}）"
        else:
            t["status"] = "queued"
            t["error"] = f"runner 租约过期，第 {t['attempts']} 次重排队"
            await _queue_push(task_id)
        t["updated_at"] = time.time()
        await _store_task(t)
        swept += 1
    return swept


# ── 公共端点 ────────────────────────────────────────────────


@router.post("/v1/video/tasks", status_code=201)
async def create_video_task(req: VideoTaskCreate, request: Request):
    """创建视频生成任务（异步；Mac runner 夜间窗口执行，见审核论证修正①②）"""
    import binascii

    if req.quality not in _VALID_QUALITY:
        raise HTTPException(status_code=422, detail=f"quality 必须为 {'/'.join(_VALID_QUALITY)}")
    try:
        await _vk_gate(request, "video", "minimax-h3")
    except HTTPException:
        raise
    ref_bytes_len = 0
    if req.ref_image_b64:
        try:
            ref_bytes_len = len(base64.b64decode(req.ref_image_b64, validate=True))
        except (binascii.Error, ValueError):
            raise HTTPException(status_code=422, detail="ref_image_b64 不是合法 base64")
        if ref_bytes_len > _MAX_REF_IMAGE_B:
            raise HTTPException(status_code=413, detail=f"参考图过大（{ref_bytes_len}B > 8MB）")

    task_id = uuid.uuid4().hex[:12]
    now = time.time()
    task = {
        "id": task_id,
        "status": "queued",
        "quality": req.quality,
        "prompt": req.prompt,
        "seed": req.seed,
        "ref_image_b64": req.ref_image_b64,
        "ref_image_name": req.ref_image_name or "ref.png",
        "created_at": now,
        "updated_at": now,
        "attempts": 0,
    }
    await _store_task(task)
    await _queue_push(task_id)
    await _index_add(task_id)
    position = max(await _queue_len() - 1, 0)
    logger.info(
        f"[video] 任务创建 {task_id} quality={req.quality} ref={ref_bytes_len}B queue_pos={position}"
    )
    return {
        "id": task_id,
        "status": "queued",
        "queue_position": position,
        "created_at": now,
    }


@router.get("/v1/video/tasks")
async def list_video_tasks(limit: int = 50):
    """任务列表（默认最近 50 条，按创建时间倒序）"""
    ids = await _index_all()
    tasks: List[Dict] = []
    for task_id in ids:
        t = await _load_task(task_id)
        if t:
            tasks.append(t)
        if len(tasks) >= limit * 2:
            break
    tasks.sort(key=lambda x: x.get("created_at", 0), reverse=True)
    return {"tasks": [_public_view(t) for t in tasks[:limit]]}


@router.get("/v1/video/tasks/{task_id}")
async def get_video_task(task_id: str):
    """任务详情（含 succeeded 后的 result_url / archive_path / 耗时）"""
    t = await _load_task(task_id)
    if not t:
        raise HTTPException(status_code=404, detail="任务不存在或已过期（记录保留 7 天）")
    return _public_view(t)


@router.get("/v1/video/tasks/{task_id}/result")
async def get_video_result(task_id: str):
    """下载生成结果视频（mp4；持久副本见 NAS 归档路径 archive_path）"""
    t = await _load_task(task_id)
    if not t or t.get("status") != "succeeded":
        raise HTTPException(status_code=404, detail="任务不存在或未成功")
    data = await _load_result(task_id)
    if data is None:
        raise HTTPException(status_code=410, detail="结果已过期（7 天 TTL），请取 NAS 归档副本")
    from fastapi.responses import Response

    return Response(
        content=data,
        media_type="video/mp4",
        headers={
            "X-YYC3-Upstream": "video-runner-mac",
            "Content-Disposition": f'attachment; filename="yyc3_video_{task_id}.mp4"',
        },
    )


# ── runner 管理端点（/v1/admin/** 由 auth 中间件以 ADMIN_API_KEYS 保护）────


@router.post("/v1/admin/video/tasks/claim")
async def claim_video_task(req: ClaimRequest):
    """runner 领取最早已排队任务（FIFO）；无任务返回 204。附带租约过期回收。"""
    await _sweep_expired()
    while True:
        task_id = await _queue_pop()
        if not task_id:
            return {"claimed": None}
        t = await _load_task(task_id)
        if not t or t.get("status") != "queued":
            continue  # 已被回收/失效的队列残项，跳过
        t["status"] = "running"
        t["runner"] = req.runner
        t["lease_until"] = time.time() + req.lease_minutes * 60
        t["updated_at"] = time.time()
        await _store_task(t)
        logger.info(f"[video] 任务 {task_id} 被 {req.runner} 领取（lease {req.lease_minutes}min）")
        return {"claimed": t}


@router.post("/v1/admin/video/tasks/{task_id}/heartbeat")
async def heartbeat_video_task(task_id: str, req: HeartbeatRequest):
    t = await _load_task(task_id)
    if not t or t.get("status") != "running":
        raise HTTPException(status_code=409, detail="任务不存在或不处于 running")
    t["runner"] = req.runner
    t["lease_until"] = time.time() + req.lease_minutes * 60
    t["updated_at"] = time.time()
    await _store_task(t)
    return {"id": task_id, "lease_until": t["lease_until"]}


@router.post("/v1/admin/video/tasks/{task_id}/result")
async def report_video_result(
    task_id: str,
    file: Optional[UploadFile] = File(None),
    archive_path: Optional[str] = Form(None),
    duration_seconds: Optional[float] = Form(None),
):
    """runner 回报成功：回传 mp4（≤16MB 内联存储）+ NAS 归档落盘（VIDEO_ARCHIVE_DIR）+ 生成耗时。
    归档文件名取自任务记录内的服务端生成 id（uuid hex），与 URL 参数解耦，无路径穿越面。"""
    t = await _load_task(task_id)
    if not t or t.get("status") != "running":
        raise HTTPException(status_code=409, detail="任务不存在或不处于 running")
    stored = False
    if file is not None:
        data = await file.read()
        if len(data) > _MAX_RESULT_B:
            raise HTTPException(
                status_code=413,
                detail=f"结果视频过大（{len(data)}B > 16MB，仅归档路径交付）",
            )
        await _store_result(task_id, data)
        stored = True
        # NAS 持久归档（compose 卷挂载 VIDEO_ARCHIVE_DIR → /Volume1/yyc3_hd/video_tasks）
        archive_dir = os.environ.get("VIDEO_ARCHIVE_DIR", "")
        if archive_dir:
            try:
                safe_name = f"{t['id']}.mp4"  # 记录内 id = 服务端 uuid hex
                (Path(archive_dir) / safe_name).write_bytes(data)
                archive_path = archive_path or f"/Volume1/yyc3_hd/video_tasks/{safe_name}"
            except Exception as e:
                logger.warning(f"[video] 任务 {task_id} NAS 归档写盘失败（不阻断）: {e}")
    t["status"] = "succeeded"
    t["archive_path"] = archive_path
    t["duration_seconds"] = duration_seconds
    t["updated_at"] = time.time()
    await _store_task(t)
    logger.info(f"[video] 任务 {task_id} 成功（result_stored={stored} archive={archive_path}）")
    return {
        "id": task_id,
        "status": "succeeded",
        "result_stored": stored,
        "archive_path": archive_path,
    }


@router.post("/v1/admin/video/tasks/{task_id}/failure")
async def report_video_failure(task_id: str, req: FailureRequest):
    t = await _load_task(task_id)
    if not t or t.get("status") != "running":
        raise HTTPException(status_code=409, detail="任务不存在或不处于 running")
    t["status"] = "failed"
    t["error"] = req.error
    t["updated_at"] = time.time()
    await _store_task(t)
    logger.warning(f"[video] 任务 {task_id} 失败：{req.error[:200]}")
    return {"id": task_id, "status": "failed"}
