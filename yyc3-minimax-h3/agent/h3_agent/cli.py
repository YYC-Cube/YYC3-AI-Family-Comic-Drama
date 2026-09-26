# ==============================================================
# claim 签发 CLI v1.0（网关写操作 X-Claim-Token 生成器）
# @file agent/h3_agent/cli.py
# @author Intelligent Application Implementation Expert <admin@0379.email>
# @version v1.0.0
# @created 2026-09-26
#
# 用法（仓库根目录）：
#   python3 -m agent.h3_agent.cli --task-type generate_batch
# 输出为 issue_claim() 返回对象的 JSON 串，直接作 X-Claim-Token 头：
#   curl -X POST http://127.0.0.1:8300/api/tasks \
#     -H "X-Claim-Token: $(python3 -m agent.h3_agent.cli --task-type quality_check)" \
#     -H "Content-Type: application/json" \
#     -d '{"task_type":"quality_check","batch":"91"}'
# ==============================================================
import argparse
import json
import sys
import time

from .security import issue_claim


def main() -> int:
    ap = argparse.ArgumentParser(description="签发 H3 网关 claim 令牌（HMAC-SHA256）")
    ap.add_argument("--task-type", required=True,
                    help="任务类型（generate_batch / quality_check / security_audit ...）")
    ap.add_argument("--trace-id", default="",
                    help="追踪 ID（缺省自动生成 cli-<时间戳>）")
    ap.add_argument("--ttl", type=int, default=300, help="有效期秒数（默认 300）")
    args = ap.parse_args()
    trace_id = args.trace_id or f"cli-{int(time.time())}"
    try:
        claim = issue_claim(trace_id, args.task_type, ttl=args.ttl)
    except PermissionError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 2
    print(json.dumps(claim, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
