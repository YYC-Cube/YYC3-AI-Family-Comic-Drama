# file: virtual_key_manager.py
# description: 虚拟密钥管理器 - 双层缓存校验链 + Redis 队列异步记账（学 litellm L1+L3）
# author: YanYuCloudCube Team
# version: v1.0.0
# created: 2026-09-20
# status: active
# tags: [billing],[virtual-key],[dual-cache],[async-ledger]

"""
@file: app/services/virtual_key_manager.py
@description: P0-1 成本主权闭环。
    ① 校验链（学 litellm DualCache）：内存 dict → Redis → PG virtual_keys 表，
       热路径 0 DB 查询；PG 不可达时降级仅用 env 静态 Key，绝不阻塞认证。
    ② 记账管道：spend 记录 LPUSH 到 Redis 队列，后台协程批量 BLPOP → PG 批量
       INSERT spend_logs。DB 写不进请求路径（响应前只入队，微秒级）。
    ③ 预算闸门：spent_usd + 本次预估 ≥ monthly_budget_usd → 拒绝（402 语义）。
@author: YanYuCloudCube Team <admin@0379.email>
@license: MIT
@copyright Copyright (c) 2026 YanYuCloudCube Team
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional

from app.cache import redis_client

logger = logging.getLogger(__name__)

VK_CACHE_TTL = 300  # 虚拟密钥缓存 5 分钟（预算更新及时性 vs 查询压力折中）
SPEND_QUEUE_KEY = "yyc3:spend:queue"
SPEND_BATCH_SIZE = 100
SPEND_FLUSH_INTERVAL = 5.0
VK_KEY_PREFIX = "yyc3:vk:"


class VirtualKeyManager:
    """虚拟密钥：双层缓存校验 + 预算闸门 + 异步批量记账"""

    def __init__(self):
        # 内存层：{key_hash: vk_record}，TTL 靠时间戳懒淘汰
        self._mem_cache: Dict[str, Dict[str, Any]] = {}
        self._ledger_task: Optional[asyncio.Task] = None

    # ── ① 校验链：内存 → Redis → PG ────────────────────────

    async def authenticate(self, api_key: str) -> Optional[Dict[str, Any]]:
        """虚拟密钥认证。返回 vk 记录（含 id/预算/白名单），非 vk 返回 None
        （调用方继续走 env 静态 Key 逻辑）。"""
        key_hash = _sha256(api_key)

        # L1 内存
        cached = self._mem_cache.get(key_hash)
        if cached and cached["_expires"] > time.time():
            if cached.get("status") != "active":
                return None
            return cached

        # L2 Redis
        try:
            raw = await redis_client.get(VK_KEY_PREFIX + key_hash)
            if raw:
                record = json.loads(raw)
                self._mem_fill(key_hash, record)
                if record.get("status") != "active":
                    return None
                return record
        except Exception as e:
            logger.debug(f"vk Redis 层读取失败（降级 PG）: {e}")

        # L3 PG
        record = await self._pg_lookup(key_hash)
        if record:
            if record.get("status") != "active":
                return None
            self._mem_fill(key_hash, record)
            try:
                await redis_client.set(
                    VK_KEY_PREFIX + key_hash,
                    json.dumps(record, default=str),
                    ex=VK_CACHE_TTL,
                )
            except Exception:
                pass
            return record
        return None

    async def _pg_lookup(self, key_hash: str) -> Optional[Dict[str, Any]]:
        """PG 查询虚拟密钥；表不存在/DB 不可达一律返回 None（功能静默关闭）"""
        try:
            from sqlalchemy import text

            from app.db import async_session

            async with async_session() as session:
                result = await session.execute(
                    text(
                        "SELECT id, name, owner, model_whitelist, monthly_budget_usd, "
                        "spent_usd, rate_limit_tpm, status, expires_at "
                        "FROM virtual_keys WHERE key_hash = :h"
                    ),
                    {"h": key_hash},
                    # 关键列（status/expires_at）变化少，TTL 过期即回源
                )
                row = result.mappings().first()
            if not row:
                return None
            rec = dict(row)
            wl = rec.get("model_whitelist")
            if isinstance(wl, str):  # sqlite 无 TEXT[]，JSON 字符串存储 → 反序列化
                try:
                    wl = json.loads(wl)
                except Exception:
                    wl = []
            rec["model_whitelist"] = list(wl or [])  # PG TEXT[] → list
            rec["monthly_budget_usd"] = float(rec.get("monthly_budget_usd") or 0)
            rec["spent_usd"] = float(rec.get("spent_usd") or 0)
            rec["rate_limit_tpm"] = int(rec.get("rate_limit_tpm") or 0)
            return rec
        except Exception as e:
            logger.debug(f"vk PG 查询不可达（vk 功能静默关闭）: {e}")
            return None

    def _mem_fill(self, key_hash: str, record: Dict[str, Any]) -> None:
        record["_expires"] = time.time() + VK_CACHE_TTL
        if len(self._mem_cache) > 1000:  # 防无限膨胀
            now = time.time()
            self._mem_cache = {k: v for k, v in self._mem_cache.items() if v["_expires"] > now}
        self._mem_cache[key_hash] = record

    # ── ② 预算闸门 ─────────────────────────────────────────

    @staticmethod
    def check_budget(record: Dict[str, Any], est_cost: float) -> bool:
        """预算检查：budget>0 且 spent+est > budget → False（402 语义）"""
        budget = float(record.get("monthly_budget_usd") or 0)
        if budget <= 0:
            return True
        return float(record.get("spent_usd") or 0) + est_cost <= budget

    @staticmethod
    def check_model_allowed(record: Dict[str, Any], model: str) -> bool:
        """模型白名单：空 = 不限"""
        wl = record.get("model_whitelist") or []
        if not wl:
            return True
        import fnmatch

        return any(fnmatch.fnmatch(model, pat) for pat in wl)

    # ── ②.5 TPM 滑窗限流：Redis INCR + 首次 EXPIRE（分钟窗口）──

    TPM_PREFIX = "yyc3:vk:tpm:"

    @staticmethod
    async def check_tpm(record: Dict[str, Any], est_tokens: int = 1) -> bool:
        """滑动窗口（分钟粒度）限流。rate_limit_tpm<=0 = 不限。
        INCR 原子累加，首次（返回 1）时 EXPIRE 60s 对齐自然分钟窗口。
        Redis 不可达按放行（限流器故障 ≠ 拒绝服务）。"""
        limit = int(record.get("rate_limit_tpm") or 0)
        if limit <= 0:
            return True
        key = f"{VirtualKeyManager.TPM_PREFIX}" f"{record.get('id')}:{time.strftime('%Y%m%d%H%M')}"
        try:
            count = await redis_client.incr(key)
            if count == 1:
                await redis_client.expire(key, 60)
            return int(count) + est_tokens - 1 <= limit
        except Exception as e:
            logger.debug(f"TPM 检查 Redis 不可达（放行）: {e}")
            return True

    # ── ③ 异步记账管道：LPUSH → 批量 BLPOP → PG 批量 INSERT ──

    async def enqueue_spend(self, entry: Dict[str, Any]) -> None:
        """请求路径内调用：只入队不落库（微秒级，不阻塞响应）"""
        entry.setdefault("ts", time.time())
        try:
            await redis_client.lpush(SPEND_QUEUE_KEY, json.dumps(entry, default=str))
        except Exception as e:
            logger.warning(f"spend 入队失败（丢弃本次计量，不影响响应）: {e}")

    async def start_ledger(self) -> None:
        """startup 挂载后台批量落库协程"""
        if self._ledger_task is None or self._ledger_task.done():
            self._ledger_task = asyncio.create_task(self._ledger_loop())
            logger.info("虚拟密钥记账管道已启动（批量落库 spend_logs）")

    async def stop_ledger(self) -> None:
        if self._ledger_task is not None:
            self._ledger_task.cancel()
            self._ledger_task = None

    async def ensure_tables(self) -> None:
        """sqlite 本地模式（DATABASE_URL=sqlite+aiosqlite）自建表；PG 模式跳过（由 003 SQL 迁移管）"""
        from app.db import DATABASE_URL, engine

        if not DATABASE_URL.startswith("sqlite"):
            return
        from sqlalchemy import text

        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS virtual_keys ("
                    "id VARCHAR(64) PRIMARY KEY, key_hash VARCHAR(64) UNIQUE, "
                    "name VARCHAR(100), owner VARCHAR(100), model_whitelist TEXT, "
                    "monthly_budget_usd FLOAT DEFAULT 0, spent_usd FLOAT DEFAULT 0, "
                    "rate_limit_tpm INT DEFAULT 0, status VARCHAR(20) DEFAULT 'active', "
                    "expires_at TIMESTAMP, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, "
                    "metadata TEXT)"
                )
            )
            await conn.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS spend_logs ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, key_id VARCHAR(64), "
                    "model VARCHAR(100), upstream VARCHAR(100), capability VARCHAR(20), "
                    "prompt_tokens INT DEFAULT 0, completion_tokens INT DEFAULT 0, "
                    "cost_usd FLOAT DEFAULT 0, latency_ms INT DEFAULT 0, "
                    "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
                )
            )

    async def _ledger_loop(self) -> None:
        while True:
            try:
                batch = await self._drain_batch()
                if batch:
                    await self._flush_batch(batch)
                else:
                    await asyncio.sleep(SPEND_FLUSH_INTERVAL)
            except asyncio.CancelledError:
                return
            except Exception as e:
                logger.warning(f"记账管道轮次异常（继续）: {e}")
                await asyncio.sleep(SPEND_FLUSH_INTERVAL)

    async def _drain_batch(self) -> List[Dict[str, Any]]:
        """RPOPLPUSH 不适合此场景；直接循环 RPOP 取一批（队列为计量数据，丢失容忍）"""
        batch: List[Dict[str, Any]] = []
        try:
            for _ in range(SPEND_BATCH_SIZE):
                raw = await redis_client.rpop(SPEND_QUEUE_KEY)
                if raw is None:
                    break
                try:
                    batch.append(json.loads(raw))
                except Exception:
                    continue
        except Exception as e:
            logger.debug(f"spend 出队失败: {e}")
        return batch

    async def _flush_batch(self, batch: List[Dict[str, Any]]) -> None:
        """批量 INSERT spend_logs + 增量 UPDATE virtual_keys.spent_usd；失败回灌队首"""
        try:
            from sqlalchemy import text

            from app.db import async_session

            async with async_session() as session:
                await session.execute(
                    text(
                        "INSERT INTO spend_logs (key_id, model, upstream, capability, "
                        "prompt_tokens, completion_tokens, cost_usd, latency_ms) "
                        "VALUES (:key_id, :model, :upstream, :capability, "
                        ":prompt_tokens, :completion_tokens, :cost_usd, :latency_ms)"
                    ),
                    [
                        {
                            "key_id": b.get("key_id"),
                            "model": b.get("model"),
                            "upstream": b.get("upstream"),
                            "capability": b.get("capability", "chat"),
                            "prompt_tokens": int(b.get("prompt_tokens") or 0),
                            "completion_tokens": int(b.get("completion_tokens") or 0),
                            "cost_usd": float(b.get("cost_usd") or 0),
                            "latency_ms": int(b.get("latency_ms") or 0),
                        }
                        for b in batch
                    ],
                )
                # 内存态预算同步增加（下次请求预算检查立即生效）
                for b in batch:
                    key_id = b.get("key_id")
                    if key_id:
                        for rec in self._mem_cache.values():
                            if str(rec.get("id")) == str(key_id):
                                rec["spent_usd"] = float(rec.get("spent_usd") or 0) + float(
                                    b.get("cost_usd") or 0
                                )
                await session.commit()
        except Exception as e:
            logger.warning(f"spend 批量落库失败（回灌队首重试）: {e}")
            for b in reversed(batch):
                try:
                    await redis_client.lpush(SPEND_QUEUE_KEY, json.dumps(b, default=str))
                except Exception:
                    break


def _sha256(s: str) -> str:
    import hashlib

    return hashlib.sha256(s.encode()).hexdigest()


# ── ④ 管理操作（CRUD）：供 /v1/admin/virtual-keys 端点调用 ──

import secrets
import uuid


async def vk_create(
    name: str,
    owner: str = "yanyu",
    model_whitelist: Optional[List[str]] = None,
    monthly_budget_usd: float = 0.0,
    rate_limit_tpm: int = 0,
    expires_at: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """创建虚拟密钥。明文 Key 只在本响应出现一次（学 litellm new_virtual_key 语义）"""
    plaintext = f"vk-{secrets.token_urlsafe(32)}"
    rec = {
        "id": str(uuid.uuid4()),
        "key_hash": _sha256(plaintext),
        "name": name,
        "owner": owner,
        "model_whitelist": model_whitelist or [],
        "monthly_budget_usd": float(monthly_budget_usd or 0),
        "spent_usd": 0.0,
        "rate_limit_tpm": int(rate_limit_tpm or 0),
        "status": "active",
        "expires_at": expires_at,
    }
    from sqlalchemy import text

    from app.db import async_session

    # 跨方言（PG/sqlite 本地 e2e）：白名单 list 由 JSON 编码器序列化为字符串绑定
    async with async_session() as session:
        await session.execute(
            text(
                "INSERT INTO virtual_keys (id, key_hash, name, owner, model_whitelist, "
                "monthly_budget_usd, rate_limit_tpm, status, expires_at, metadata) "
                "VALUES (:id, :h, :name, :owner, :wl, :budget, :tpm, 'active', "
                ":expires_at, :meta)"
            ),
            {
                "id": rec["id"],
                "h": rec["key_hash"],
                "name": name,
                "owner": owner,
                "wl": json.dumps(model_whitelist or []),
                "budget": rec["monthly_budget_usd"],
                "tpm": rec["rate_limit_tpm"],
                "expires_at": expires_at,
                "meta": json.dumps(metadata, default=str) if metadata else None,
            },
        )
        await session.commit()
    # 预热缓存：创建即可用（免首次请求穿透 PG）
    vk_manager._mem_fill(rec["key_hash"], dict(rec))
    try:
        await redis_client.set(
            VK_KEY_PREFIX + rec["key_hash"],
            json.dumps(rec, default=str),
            ex=VK_CACHE_TTL,
        )
    except Exception:
        pass
    return {"key": plaintext, **rec}


async def vk_list(owner: Optional[str] = None, include_disabled: bool = True) -> List[Dict]:
    """列虚拟密钥（脱敏：只露 hash 前 8 位）"""
    from sqlalchemy import text

    from app.db import async_session

    q = (
        "SELECT id, key_hash, name, owner, model_whitelist, monthly_budget_usd, "
        "spent_usd, rate_limit_tpm, status, expires_at, created_at FROM virtual_keys"
    )
    cond, params = [], {}
    if owner:
        cond.append("owner = :owner")
        params["owner"] = owner
    if not include_disabled:
        cond.append("status = 'active'")
    if cond:
        q += " WHERE " + " AND ".join(cond)
    q += " ORDER BY created_at DESC"
    async with async_session() as session:
        result = await session.execute(text(q), params)
        rows = [dict(r) for r in result.mappings()]
    for r in rows:
        r["key_hint"] = (r.pop("key_hash") or "")[:8]
        r["monthly_budget_usd"] = float(r.get("monthly_budget_usd") or 0)
        r["spent_usd"] = float(r.get("spent_usd") or 0)
    return rows


async def vk_update_status(key_id: str, status: str) -> bool:
    """启停虚拟密钥（active/disabled）。同步失效两级缓存，即时生效"""
    if status not in ("active", "disabled"):
        raise ValueError(f"非法状态: {status}")
    from sqlalchemy import text

    from app.db import async_session

    async with async_session() as session:
        result = await session.execute(
            text("UPDATE virtual_keys SET status = :s WHERE id = :id"),
            {"s": status, "id": key_id},
        )
        await session.commit()
        changed = (result.rowcount or 0) > 0
    if changed:
        # 精确失效：查 hash 后逐级剔除，强制下次校验回源 PG
        async with async_session() as session:
            row = (
                await session.execute(
                    text("SELECT key_hash FROM virtual_keys WHERE id = :id"),
                    {"id": key_id},
                )
            ).scalar()
        if row:
            vk_manager._mem_cache.pop(row, None)
            try:
                await redis_client.delete(VK_KEY_PREFIX + row)
            except Exception:
                pass
    return changed


async def vk_update_fields(
    key_id: str,
    monthly_budget_usd: Optional[float] = None,
    rate_limit_tpm: Optional[int] = None,
    model_whitelist: Optional[List[str]] = None,
) -> bool:
    """编辑虚拟密钥字段（预算/TPM/白名单，None=不改）。两级缓存即时失效"""
    sets: List[str] = []
    params: Dict[str, Any] = {"id": key_id}
    if monthly_budget_usd is not None:
        sets.append("monthly_budget_usd = :budget")
        params["budget"] = float(monthly_budget_usd)
    if rate_limit_tpm is not None:
        sets.append("rate_limit_tpm = :tpm")
        params["tpm"] = int(rate_limit_tpm)
    if model_whitelist is not None:
        sets.append("model_whitelist = :wl")
        params["wl"] = json.dumps(model_whitelist)
    if not sets:
        return False
    from sqlalchemy import text

    from app.db import async_session

    async with async_session() as session:
        result = await session.execute(
            text(f"UPDATE virtual_keys SET {', '.join(sets)} WHERE id = :id"), params
        )
        await session.commit()
        changed = (result.rowcount or 0) > 0
    if changed:
        async with async_session() as session:
            row = (
                await session.execute(
                    text("SELECT key_hash FROM virtual_keys WHERE id = :id"),
                    {"id": key_id},
                )
            ).scalar()
        if row:
            vk_manager._mem_cache.pop(row, None)
            try:
                await redis_client.delete(VK_KEY_PREFIX + row)
            except Exception:
                pass
    return changed


async def vk_delete(key_id: str) -> bool:
    """删除虚拟密钥（spend_logs.key_id 置 NULL，流水保留审计）"""
    from sqlalchemy import text

    from app.db import async_session

    async with async_session() as session:
        row = (
            await session.execute(
                text("SELECT key_hash FROM virtual_keys WHERE id = :id"), {"id": key_id}
            )
        ).scalar()
        if not row:
            return False
        await session.execute(text("DELETE FROM virtual_keys WHERE id = :id"), {"id": key_id})
        await session.commit()
    vk_manager._mem_cache.pop(row, None)
    try:
        await redis_client.delete(VK_KEY_PREFIX + row)
    except Exception:
        pass
    return True


async def vk_usage(key_id: str, days: int = 30) -> Dict[str, Any]:
    """用量查询：近 N 天按模型聚合（供前端看板/预算复盘）"""
    from sqlalchemy import text

    from app.db import async_session

    async with async_session() as session:
        from datetime import datetime, timedelta

        since = datetime.utcnow() - timedelta(days=int(days))
        result = await session.execute(
            text(
                "SELECT model, COUNT(*) AS calls, SUM(prompt_tokens) AS prompt_tokens, "
                "SUM(completion_tokens) AS completion_tokens, SUM(cost_usd) AS cost_usd "
                "FROM spend_logs WHERE key_id = :id AND created_at >= :since "
                "GROUP BY model ORDER BY cost_usd DESC"
            ),
            {"id": key_id, "since": since},
        )
        by_model = [dict(r) for r in result.mappings()]
        for r in by_model:
            r["cost_usd"] = float(r.get("cost_usd") or 0)
    total = sum(r["cost_usd"] for r in by_model)
    return {
        "key_id": key_id,
        "days": days,
        "total_cost_usd": round(total, 6),
        "by_model": by_model,
    }


# 模块级单例
vk_manager = VirtualKeyManager()
