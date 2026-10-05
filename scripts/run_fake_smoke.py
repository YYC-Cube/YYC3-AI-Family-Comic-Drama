# ==============================================================
# run_fake_smoke.py — 全链 Fake 冒烟预检（63 号 A7 落位）
# 对标 MiraFrame Fake Provider（零外部依赖跑通完整流程验证逻辑）
# 原理：以强制 stub 环境子进程运行 run_batch_shots（ComfyUI/TTS/H3 全禁用
#   → adapter stub_fallback 路径），验证「切集→分镜→敏感词预检→AIGC 标识
#   →stub 产物→manifest 落盘」链路完整性，零 GPU 成本。
# 纪律：夜批前置闸门——预检不过不放行真实批次（失败即阻断）。
# 用法：python scripts/run_fake_smoke.py [--episode 1] [--out 留证.json]
# 退出码：0=链路完整 / 1=断流（附断点定位）
# ==============================================================
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PY = REPO / "yyc3-ai-manju-studio" / ".venv" / "bin" / "python"
BATCH = REPO / "scripts" / "run_batch_shots.py"

# 全 stub 强制环境：空 URL → 各 client enabled=False → adapter 降级路径
FAKE_ENV = {
    "COMFYUI_URL": "",
    "TTS_API_URL": "",
    "H3_AGENT_GATEWAY": "",
    "PROJECT_ROOT": "/tmp/yyc3_fake_smoke",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--episode", type=int, default=1)
    ap.add_argument("--project", default="fake-smoke")
    ap.add_argument("--limit", type=int, default=2,
                    help="冒烟镜头数（链路验证无需全量）")
    ap.add_argument("--out", default="", help="留证 JSON 路径")
    ap.add_argument("--market-file", default="",
                    help="市场情报 JSON（A1 闸：存在即校验并留证）")
    args = ap.parse_args()

    env = {**os.environ, **FAKE_ENV}
    cmd = [str(PY), str(BATCH), "--project", args.project,
           "--episode", str(args.episode), "--limit", str(args.limit)]
    if args.market_file:
        cmd += ["--market-file", args.market_file]
    t0 = time.time()
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300,
                          env=env)
    elapsed = round(time.time() - t0, 1)

    # 断点定位：解析 manifest 链路产物
    proj = Path(FAKE_ENV["PROJECT_ROOT"]) / args.project
    sb_p = proj / "storyboard" / "storyboard.v1.json"
    mf_p = proj / "state" / "manifest.json"
    sb = json.loads(sb_p.read_text(encoding="utf-8")) if sb_p.exists() else {}
    mf = json.loads(mf_p.read_text(encoding="utf-8")) if mf_p.exists() else {}

    checks = {
        "process_exit_0": proc.returncode == 0,
        "storyboard_written": bool(sb.get("shots")),
        "sensitive_scan_ran": "sensitive_scan" in mf,
        "aigc_declared": bool(mf.get("aigc", {}).get("declared")),
        "gate_rhythm_ran": "gate_rhythm" in mf,
        "gate_critique_ran": "gate_critique" in mf,
        "stub_shots_present": any(
            s.get("gen_status", "").startswith("stub")
            for s in mf.get("shots", [])),
        "manifest_elapsed": bool(mf.get("elapsed_s") is not None),
    }
    # A1 闸仅在实际传入情报时断言（可选闸位）
    if args.market_file:
        checks["market_intel_ran"] = "market_intel" in mf
    ok = all(checks.values())
    report = {"fake_smoke": ok, "checks": checks,
              "exit_code": proc.returncode, "elapsed_s": elapsed,
              "episode": args.episode, "project": args.project,
              "gate_critique": mf.get("gate_critique"),
              "gate_rhythm": (mf.get("gate_rhythm") or {}).get("coverage"),
              "market_intel": mf.get("market_intel"),
              "shots_in_storyboard": len(sb.get("shots", [])),
              "manifest_shots": len(mf.get("shots", [])),
              "stdout_tail": proc.stdout.strip().splitlines()[-6:],
              "stderr_tail": proc.stderr.strip().splitlines()[-3:]}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.out:
        Path(args.out).write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if not ok:
        failed = [k for k, v in checks.items() if not v]
        print(f"[fake-smoke] 断流断点：{failed}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
