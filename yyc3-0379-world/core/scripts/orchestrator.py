#!/usr/bin/env python3
# file: orchestrator.py
# description: A2A 编排器独立进程入口（结果流聚合 / 挂起回收 / 指标采集专职化）
# author: YanYuCloudCube Team <admin@0379.email>
# created: 2026-09-26
# status: active
# tags: [a2a],[orchestrator],[entrypoint],[redis-stream]

"""A2A 编排器独立进程（ResultHub 抽出网关：多网关实例共享 Redis 聚合）。

职责：专职消费 stream:agent:result:callback（消费者组 group-orchestrator）——
sender 覆盖式幂等聚合 + XAUTOCLAIM 挂起回收 + Prometheus 指标采集（refresh_gauges）。
同步闭环端点（/v1/agent/a2a/tasks/sync）经 Redis 结果流与网关共享聚合状态，
本进程与网关进程可跨机部署（只需同源 Redis）。

部署形态（三选一）:
    ① 网关内嵌（缺省）：网关 A2A_RESULT_CONSUMER_ENABLED=true 自带泵，无需本进程
    ② 独立编排器（本入口）：网关侧置 false + 本进程专职（消除网关实例间的聚合竞争，
       多网关横向扩容时推荐）
    ③ 混合灰度：两端都开（消费者组多成员分摊，Redis 语义安全；同型任务不重复消费）

用法（NAS/Mac 任一能连通 Redis 的执行位）:
    export REDIS_HOST=... REDIS_PASSWORD=...                # 与网关 .env 同源
    python core/scripts/orchestrator.py                     # 聚合 + 回收 + 指标
    python core/scripts/orchestrator.py --no-metrics        # 关指标采集（单实例采集即可）
    python core/scripts/orchestrator.py --consumer nas-orch # 消费者名指定（多实例各自唯一）

环境变量:
    A2A_RESULT_CONSUMER    消费者名后缀（缺省 hostname-pid，多实例部署各自唯一）
    A2A_AUDIT_LOKI_ENABLED 同进程顺带启动审计 Loki shipper（可选，缺省读 env）
    LOKI_URL               Loki 地址（shipper 启用时生效）

注意：网关侧同步端点依赖 wait_one——独立部署时网关 A2A_RESULT_CONSUMER_ENABLED
必须为 false 吗？否：混合形态下网关内嵌泵与独立编排进程同为消费者组成员，
Redis XREADGROUP 分摊投递，任一成员 ACK 后消息不再重复投递，端点 wait_one 经
聚合器事件驱动唤醒（跨进程经 Redis 结果流幂等扇入，进程内聚合器即时唤醒）。
"""

import argparse
import asyncio
import importlib.util
import os
import signal
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_API_DIR = _REPO_ROOT / "core" / "api"


def _bootstrap() -> None:
    """路径引导：core/api 注册为 app 包（对齐 tests/conftest.py 机制）+ 仓库根入 path。"""
    for p in (str(_REPO_ROOT), str(_API_DIR)):
        if p not in sys.path:
            sys.path.insert(0, p)
    if "app" not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            "app", _API_DIR / "__init__.py", submodule_search_locations=[str(_API_DIR)]
        )
        pkg = importlib.util.module_from_spec(spec)
        sys.modules["app"] = pkg
        spec.loader.exec_module(pkg)


def _load_env_file() -> None:
    """可选加载项目根 .env（python-dotenv 存在时；已有环境变量不覆盖）。"""
    try:
        from dotenv import load_dotenv

        load_dotenv(_REPO_ROOT / ".env", override=False)
    except ImportError:
        pass


async def _run(with_metrics: bool, with_audit: bool) -> None:
    """编排器主协程：结果流聚合（+可选指标采集 / 审计 shipper），SIG 信号取消收敛。"""
    from app.services import a2a_audit, a2a_result

    tasks = [asyncio.create_task(a2a_result.result_hub().run_forever(), name="orch-hub")]
    if with_metrics:
        from app.services import a2a_metrics

        tasks.append(asyncio.create_task(a2a_metrics.observe_loop(), name="orch-metrics"))
    if with_audit and a2a_audit._enabled():
        tasks.append(asyncio.create_task(a2a_audit.ship_loop(), name="orch-audit"))
        print("[orchestrator] 审计 Loki shipper 已随编排器启动")
    await asyncio.gather(*tasks)


def main() -> None:
    parser = argparse.ArgumentParser(description="YYC³ A2A 编排器（结果流聚合独立进程）")
    parser.add_argument(
        "--consumer",
        default="",
        help="结果流消费者名后缀（缺省读 A2A_RESULT_CONSUMER，再缺省 hostname-pid）",
    )
    parser.add_argument(
        "--no-metrics", action="store_true", help="关闭指标采集循环（多实例部署仅留一个采集位）"
    )
    parser.add_argument(
        "--with-audit",
        action="store_true",
        help="同进程附带审计 Loki shipper（替代网关内嵌，需 A2A_AUDIT_LOKI_ENABLED=true）",
    )
    args = parser.parse_args()

    _bootstrap()
    _load_env_file()
    if args.consumer:
        os.environ["A2A_RESULT_CONSUMER"] = args.consumer

    print(
        "[orchestrator] 启动：结果流聚合 + 挂起回收"
        f"（metrics={'off' if args.no_metrics else 'on'},"
        f" audit={'on' if args.with_audit else 'off'}；Ctrl/Cmd+C 优雅退出）"
    )

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    main_task = loop.create_task(_run(with_metrics=not args.no_metrics, with_audit=args.with_audit))

    def _shutdown(signum, _frame):
        print(f"\n[orchestrator] 收到信号 {signum}，收敛中…")
        main_task.cancel()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    try:
        loop.run_until_complete(main_task)
    except asyncio.CancelledError:
        pass
    finally:
        loop.close()
        print("[orchestrator] 已退出")


if __name__ == "__main__":
    main()
