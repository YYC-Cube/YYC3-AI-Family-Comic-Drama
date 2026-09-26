# file: orchestrator_entry.py
# description: A2A 编排器容器入口（python -m app.orchestrator_entry；NAS/容器部署用）
# author: YanYuCloudCube Team <admin@0379.email>
# created: 2026-09-27
# status: active
# tags: [a2a],[orchestrator],[entrypoint]

"""编排器容器入口（仓库根脚本 core/scripts/orchestrator.py 的镜像内等价物）。

职责：结果流聚合（ResultHub）+ 指标采集（可选）+ 审计 Loki shipper（可选）。
用法：
    python -m app.orchestrator_entry                    # 聚合 + 指标
    python -m app.orchestrator_entry --no-metrics       # 多实例仅留一个采集位
    python -m app.orchestrator_entry --with-audit       # 附带审计 shipper
"""

import argparse
import asyncio
import logging
import os
import signal

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [orchestrator] %(levelname)s %(name)s: %(message)s",
)


async def _run(with_metrics: bool, with_audit: bool) -> None:
    from app.services import a2a_audit, a2a_result

    tasks = [asyncio.create_task(a2a_result.result_hub().run_forever(), name="orch-hub")]
    if with_metrics:
        from app.services import a2a_metrics

        tasks.append(asyncio.create_task(a2a_metrics.observe_loop(), name="orch-metrics"))
    if with_audit and a2a_audit._enabled():
        tasks.append(asyncio.create_task(a2a_audit.ship_loop(), name="orch-audit"))
        print("[orchestrator-entry] 审计 Loki shipper 已随编排器启动")
    await asyncio.gather(*tasks)


def main() -> None:
    parser = argparse.ArgumentParser(description="YYC³ A2A 编排器（容器入口）")
    parser.add_argument(
        "--consumer",
        default="",
        help="结果流消费者名后缀（缺省读 A2A_RESULT_CONSUMER，再缺省 hostname-pid）",
    )
    parser.add_argument("--no-metrics", action="store_true", help="关闭指标采集循环")
    parser.add_argument(
        "--with-audit",
        action="store_true",
        help="附带审计 Loki shipper（需 A2A_AUDIT_LOKI_ENABLED=true）",
    )
    args = parser.parse_args()

    if args.consumer:
        os.environ["A2A_RESULT_CONSUMER"] = args.consumer

    print(
        "[orchestrator-entry] 启动：结果流聚合 + 挂起回收"
        f"（metrics={'off' if args.no_metrics else 'on'},"
        f" audit={'on' if args.with_audit else 'off'}；SIGTERM/SIGINT 优雅退出）"
    )

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    main_task = loop.create_task(_run(not args.no_metrics, args.with_audit))

    def _shutdown(signum, _frame):
        print(f"\n[orchestrator-entry] 收到信号 {signum}，收敛中…")
        main_task.cancel()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    try:
        loop.run_until_complete(main_task)
    except asyncio.CancelledError:
        pass
    finally:
        loop.close()
        print("[orchestrator-entry] 已退出")


if __name__ == "__main__":
    main()
