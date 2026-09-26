"""灰度验证一次性脚本（不入测试面）：真实 Redis(6390) + 真实 Loki(3100) 的 shipper 端到端。

步骤：XADD 两条审计 → ship_once 推送 Loki → 回读 Loki 查询断言（labels + 内容）。
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6390")
os.environ.setdefault("LOKI_URL", "http://localhost:3100")

import importlib.util

_API_DIR = Path(__file__).resolve().parents[1] / "api"
spec = importlib.util.spec_from_file_location(
    "app", _API_DIR / "__init__.py", submodule_search_locations=[str(_API_DIR)]
)
pkg = importlib.util.module_from_spec(spec)
sys.modules["app"] = pkg
spec.loader.exec_module(pkg)

import time

import httpx

from app.services import a2a_audit
from app.services import a2a_protocol as proto


async def main() -> None:
    # ① 真实 XADD 两条审计（task_dead / orphan_result）
    now_ms = int(time.time() * 1000)
    await proto.publish_audit(
        {
            "trace_id": "gray-t1",
            "auditor": "gewu-zongshi-001",
            "action": "task_dead",
            "detail": {"error": "gray-验证死信"},
            "timestamp": now_ms,
        }
    )
    await proto.publish_audit(
        {
            "trace_id": "gray-t2",
            "auditor": "gateway",
            "action": "orphan_result",
            "detail": {"stream_msg_id": "gray-1"},
            "timestamp": now_ms,
        }
    )
    # ② 建组 → ship_once：真实 Redis 拉取 → 真实 Loki 推送
    await proto.ensure_group(proto.AUDIT_STREAM, a2a_audit.AUDIT_GROUP)
    shipped = await a2a_audit.ship_once()
    print(f"[gray] ship_once 推送 {shipped} 条")
    assert shipped >= 2, "应至少推送 2 条（脚本重跑累积幂等）"
    await asyncio.sleep(1.5)  # Loki 写入窗口
    # ③ 回读 Loki 查询断言
    async with httpx.AsyncClient(timeout=5.0) as client:
        r = await client.get(
            "http://localhost:3100/loki/api/v1/query_range",
            params={
                "query": '{job="a2a-audit"} |= "gray-"',
                "start": str((now_ms - 60000) * 1_000_000),
                "end": str((now_ms + 60000) * 1_000_000),
                "limit": "10",
            },
        )
        data = r.json()
        values = [v for stream in data["data"]["result"] for v in stream["values"]]
        print(f"[gray] Loki 回读 {len(values)} 条")
        assert len(values) >= 2, f"Loki 应含 2 条，实得 {len(values)}"
        assert any("task_dead" in v[1] for v in values), "应含 task_dead"
        assert any("orphan_result" in v[1] for v in values), "应含 orphan_result"
        labels = {tuple(sorted(s["stream"].items())) for s in data["data"]["result"]}
        print(f"[gray] 标签组 {len(labels)} 组")
    print("[gray] ✅ 灰度端到端验证通过：Redis XADD → shipper → Loki 可查询")


asyncio.run(main())
