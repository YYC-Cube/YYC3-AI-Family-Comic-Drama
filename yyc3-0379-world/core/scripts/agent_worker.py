#!/usr/bin/env python3
# file: agent_worker.py
# description: 业务 Agent 外置 Worker 独立进程入口（Phase 2 A2A Worker 化）
# author: YanYuCloudCube Team <admin@0379.email>
# created: 2026-09-26
# status: active
# tags: [a2a],[worker],[entrypoint],[redis-stream]

"""业务 Agent 外置 Worker 进程（可行性报告 Phase 2：语枢/预见/创想先期独立消费）。

职责：消费 stream:agent:task:{agent_id}（消费者组），执行单 Agent 业务任务，
成功 ACK + 结果回执；失败 nack 重试（3 次）后迁移死信流。与网关进程解耦部署
（可同机不同容器，也可分发至 yyc3-22-mac 等执行位）。

用法（NAS/Mac 任一能连通 Redis 的执行位）:
    export REDIS_HOST=... REDIS_PASSWORD=...            # 与网关 .env 同源
    python core/scripts/agent_worker.py                 # 默认首批 3 Agent
    python core/scripts/agent_worker.py --agents yushu-wanwu-001
    A2A_WORKER_AGENTS=yushu-wanwu-001,yujian-xianzhi-001 python core/scripts/agent_worker.py

环境变量:
    A2A_WORKER_AGENTS     逗号分隔 agent_id（缺省 yushu,yujian,chuangxiang 3 Agent）
    A2A_WORKER_CONSUMER   消费者名后缀（缺省 hostname-pid，多进程不串投递记录）
    LLM_BASE_URL/LLM_API_KEY 等  业务 Agent 推理通道（未配置自动 Mock 降级）
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


def main() -> None:
    parser = argparse.ArgumentParser(description="YYC³ 业务 Agent 外置 Worker（A2A 消费者组）")
    parser.add_argument(
        "--agents",
        default="",
        help="逗号分隔 agent_id；缺省读 A2A_WORKER_AGENTS，再缺省首批 3 Agent",
    )
    args = parser.parse_args()

    _bootstrap()
    _load_env_file()
    if args.agents:
        os.environ["A2A_WORKER_AGENTS"] = args.agents

    from app.services import agent_workers

    ids = agent_workers.worker_agent_ids()
    print(f"[agent-worker] 启动：{','.join(ids)}（Ctrl/Cmd+C 优雅退出）")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    main_task = loop.create_task(agent_workers.run_workers(ids))

    def _shutdown(signum, _frame):
        print(f"\n[agent-worker] 收到信号 {signum}，收敛中…")
        main_task.cancel()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    try:
        loop.run_until_complete(main_task)
    except asyncio.CancelledError:
        pass
    finally:
        loop.close()
        print("[agent-worker] 已退出")


if __name__ == "__main__":
    main()
