# file: worker_entry.py
# description: 业务 Agent Worker 容器入口（python -m app.worker_entry；NAS/容器部署用）
# author: YanYuCloudCube Team <admin@0379.email>
# created: 2026-09-27
# status: active
# tags: [a2a],[worker],[entrypoint]

"""Agent Worker 容器入口。

仓库根脚本 core/scripts/agent_worker.py 负责路径引导（bare-metal 运行）；
容器镜像内 core/api 已映射为 app 包（PYTHONPATH=/app），无需引导——本模块
即为镜像内等价入口（compose command: python -m app.worker_entry）。

容器语义：docker stop 发 SIGTERM → 默认终止；在途消息留存 PEL，
重启后 XAUTOCLAIM 回收（五高-高可用，无消息丢失）。
"""

import asyncio
import logging
import os
import signal

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [worker] %(levelname)s %(name)s: %(message)s",
)


def main() -> None:
    from app.services import agent_workers

    ids = agent_workers.worker_agent_ids()
    print(f"[worker-entry] 启动：{','.join(ids)}（SIGTERM/SIGINT 优雅退出）")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    main_task = loop.create_task(agent_workers.run_workers(ids))

    def _shutdown(signum, _frame):
        print(f"\n[worker-entry] 收到信号 {signum}，收敛中…")
        main_task.cancel()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    try:
        loop.run_until_complete(main_task)
    except asyncio.CancelledError:
        pass
    finally:
        loop.close()
        print("[worker-entry] 已退出")


if __name__ == "__main__":
    main()
