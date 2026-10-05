# ==============================================================
# run_g5_ops_ledger.py — G5 运营反哺账本（TC-G5-001/004 前置机制）
# 职责（YYC3-63 §四）：
#   init   — 初始化 docs/ops/g5-ops-ledger.json（空账本骨架）
#   judge  — 两用例真实判定：
#     TC-G5-001 完播率对比：P0/P1 两期各 ≥1 集 × ≥30 有效会话，
#              mean(P1) − mean(P0) ≥ 5pp → PASS（逐集+均值双报）
#     TC-G5-004 排期采纳率：≥4 周期且 采纳/建议 ≥60% → PASS
#   数据不足 → BLOCKED 如实留证（不虚构，G 门禁口径）
# 账本契约见 YYC3-63 §2.3/§3.2（completion / scheduling 字段）
# 运行：yyc3-ai-manju-studio/.venv/bin/python scripts/run_g5_ops_ledger.py init|judge
# ==============================================================
import argparse
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LEDGER = REPO / "docs" / "ops" / "g5-ops-ledger.json"

EMPTY = {"_schema": "YYC3-63 v1.0.0（completion/scheduling 契约见方案 §2.3/§3.2）",
         "completion": [], "scheduling": []}

# 手册阈值
COMPLETION_DELTA_PP = 5.0      # ≥5 个百分点
MIN_SESSIONS_PER_EP = 30       # 每集有效会话下限
ADOPT_RATE = 0.60              # 采纳率 ≥60%
MIN_CYCLES = 4                 # ≥4 周期


def load() -> dict:
    if not LEDGER.exists():
        print(f"[ledger] 账本不存在（先运行 init）：{LEDGER}")
        return dict(EMPTY)
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def save(data: dict) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                      encoding="utf-8")


def judge_001(entries: list) -> dict:
    """完播率两期对比（P0 基线 vs P1 反哺）。"""
    valid = [e for e in entries
             if e.get("sessions_valid", 0) >= MIN_SESSIONS_PER_EP]
    p0 = [e["completion_rate_mean"] for e in valid if e.get("phase") == "P0"]
    p1 = [e["completion_rate_mean"] for e in valid if e.get("phase") == "P1"]
    ready = bool(p0) and bool(p1)
    delta_pp = (sum(p1) / len(p1) - sum(p0) / len(p0)) * 100 if ready else None
    return {
        "case": "TC-G5-001 反哺前后完播率对比（>=5pp）",
        "valid_entries": len(valid), "p0_eps": len(p0), "p1_eps": len(p1),
        "p0_mean": round(sum(p0) / len(p0), 4) if p0 else None,
        "p1_mean": round(sum(p1) / len(p1), 4) if p1 else None,
        "delta_pp": round(delta_pp, 2) if delta_pp is not None else None,
        "gate": f"两期各 ≥1 有效集（≥{MIN_SESSIONS_PER_EP} 会话）且 Δ≥{COMPLETION_DELTA_PP}pp",
        "verdict": ("PASS" if delta_pp is not None
                    and round(delta_pp, 2) >= COMPLETION_DELTA_PP
                    else ("FAIL" if ready else "BLOCKED")),
        "honest_note": "" if ready else
                       "两期有效数据未齐（P0/P1 各需 ≥1 集 × ≥30 有效会话）——"
                       "窗口排期见 YYC3-63 §五，机制就绪待数据",
    }


def judge_004(cycles: list) -> dict:
    """伯乐排期采纳率（≥4 周期 × ≥60%）。"""
    n = len(cycles)
    adopted = sum(1 for c in cycles if c.get("adopted") is True)
    rate = round(adopted / n, 4) if n else None
    ready = n >= MIN_CYCLES
    return {
        "case": "TC-G5-004 伯乐排期建议采纳率（>=60%）",
        "cycles": n, "adopted": adopted,
        "adopt_rate": rate,
        "gate": f"周期 ≥{MIN_CYCLES} 且采纳率 ≥{int(ADOPT_RATE * 100)}%",
        "verdict": ("PASS" if ready and rate is not None
                    and rate >= ADOPT_RATE
                    else ("FAIL" if ready else "BLOCKED")),
        "honest_note": "" if ready else
                       f"周期数 {n}/{MIN_CYCLES} 未达——台账录入口径见 YYC3-63 §3.2",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["init", "judge"])
    args = ap.parse_args()
    if args.mode == "init":
        save(dict(EMPTY))
        print(f"[ledger] 空账本已初始化：{LEDGER}")
        return 0
    data = load()
    r1, r4 = judge_001(data.get("completion", [])), \
        judge_004(data.get("scheduling", []))
    out = {"testcase": "G5 运营反哺账本判定（TC-G5-001/004）",
           "ledger": str(LEDGER.relative_to(REPO)),
           "TC-G5-001": r1, "TC-G5-004": r4,
           "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
