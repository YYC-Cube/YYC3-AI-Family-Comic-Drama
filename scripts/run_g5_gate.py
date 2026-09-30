# ==============================================================
# run_g5_gate.py — G5 门禁执行器（骨架生产化 · HANDOFF 34.4 P2）
# 职责：TC-G5-001~006 六用例统一收割口径——有数据即真实计算判定，
#   无数据按手册允许 BLOCKED 留证（对齐 G4 002/009 先例），不虚构 PASS。
# 可执行件：TC-G5-003 LoRA 增量训练触发判定（均值口径 mean < 0.85 触发，
#   与 M3 二轮生产上线决策一致：v2 组合峰值 mean 0.8669 达标上线）——
#   以三轮留证评测 JSON 为输入真实跑判定，输出准确率与误触发率。
# 运行：yyc3-ai-manju-studio/.venv/bin/python scripts/run_g5_gate.py \
#   --out docs/attachments/G4-20260929/tc-g5-gate-run-20260930.json
# ==============================================================
import argparse
import json
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EVID = REPO / "docs" / "attachments" / "G4-20260929"

# 触发阈值：anchor_guard 生产判定口径 0.85（均值口径为上线门槛）
TRIGGER_THRESHOLD = 0.85


def lora_increment_trigger(combo_peak_mean: float) -> bool:
    """LoRA 增量训练触发判定（TC-G5-003 ①）。

    组合峰值 mean < 0.85 → 触发增量训练（一致性滑落）；
    >= 0.85 → 不触发（达标模型，误触发即失败）。
    """
    return combo_peak_mean < TRIGGER_THRESHOLD


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def case_g5_003() -> dict:
    """触发判定真实执行：三轮留证模型逐个过判定器。"""
    models = [
        ("sd-hero-v2（生产上线配置）",
         load_json(EVID / "tc-m3-lora-v2-sweep.json")["combo_weight_sweep"]["w015_peak"]["mean"],
         "tc-m3-lora-v2-sweep.json"),
        ("sd-hero-v3（rank64+4.76ep）",
         load_json(EVID / "tc-m3-lora-v3-sweep.json")["combo_weight_sweep"]["w015_peak"]["mean"],
         "tc-m3-lora-v3-sweep.json"),
        ("sd-hero-v3r32（rank32+10ep）",
         json.load(open(EVID / "tc-m3-lora-v3r32-sweep.json"))["results"]["combo_w020"]["mean"],
         "tc-m3-lora-v3r32-sweep.json"),
    ]
    expected = [False, True, True]  # v2 达标不触发；v3/v3r32 滑落必触发
    rows = []
    for (name, mean, evid), exp in zip(models, expected):
        fired = lora_increment_trigger(mean)
        rows.append({"model": name, "combo_peak_mean": mean,
                     "trigger_fired": fired, "expected": exp,
                     "correct": fired == exp, "evidence": evid})
        print(f"[g5-003] {name}: mean={mean} -> 触发={fired}（预期 {exp}，"
              f"{'正确' if fired == exp else '误判'})")
    acc = sum(1 for r in rows if r["correct"]) / len(rows)
    false_fires = sum(1 for r in rows if r["trigger_fired"] and r["expected"] is False)
    step1_pass = acc == 1.0 and false_fires == 0
    return {
        "case": "TC-G5-003 LoRA 增量训练触发验证",
        "step1_trigger_judgement": {
            "rule": f"组合峰值 mean < {TRIGGER_THRESHOLD} 触发（均值口径上线门槛）",
            "rows": rows, "accuracy": acc, "false_trigger_count": false_fires,
            "verdict": "PASS" if step1_pass else "FAIL"},
        "step2_incremental_retrain": {"verdict": "BLOCKED",
            "note": "增量重训窗口待排（33.5 备选路径：v2 checkpoint 起步 + 777 样本低步数续训）"},
        "step3_re_eval": {"verdict": "BLOCKED", "note": "依赖 step2"},
        "verdict": "partial" if step1_pass else "FAIL",
        "honest_note": "①触发判定 100% 准确/零误触发（真实执行三模型）；②③待训练窗口，"
                       "手册预期 min≥0.85 复测口径不变",
    }


def case_g5_002() -> dict:
    """产能：基线在位（3 集/晚），反哺项未全量启用，夜间窗口未复跑。"""
    base = load_json(EVID / "tc-g4-009-nightly-batch-stats.json")
    n_base = len(base["episodes"])
    return {"case": "TC-G5-002 反哺后产能提升（>=30%）",
            "baseline": f"TC-G4-009：{n_base} 集/晚（tc-g4-009-nightly-batch-stats.json）",
            "verdict": "BLOCKED",
            "honest_note": "反哺项（锚定域再校准/combo 复评）未全量启用，整夜批量窗口未复跑；"
                           "计算链就绪（manifest 聚合 + 产能对照），启用后一键复算"}


def case_g5_005() -> dict:
    """成本：核算链就绪（含计量接入），反哺后单集未复算。"""
    cost = load_json(EVID / "tc-g4-007-cost-report.json")["episodes"]
    base_range = [min(e["total_cost_cny"] for e in cost),
                  max(e["total_cost_cny"] for e in cost)]
    return {"case": "TC-G5-005 运营成本反哺核算（较基线降 >=20%）",
            "baseline_cny_per_ep": base_range,
            "verdict": "BLOCKED",
            "honest_note": f"G4 基线 {base_range[0]:.4f}-{base_range[1]:.4f} 元/集在位；"
                           "反哺项未全量启用故无'反哺后'核算对象；核算链 v1.1.1 就绪"
                           "（电费折算 + Token-Console 计量接入，timeout 8s 修复）"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(EVID / "tc-g5-gate-run.json"))
    args = ap.parse_args()

    cases = {
        "TC-G5-001": {"case": "反哺前后完播率对比（>=5pp）", "verdict": "BLOCKED",
                      "honest_note": "依赖真实运营曝光窗口（每集 >=30 会话 x2 期），手册允许 BLOCKED"},
        "TC-G5-002": case_g5_002(),
        "TC-G5-003": case_g5_003(),
        "TC-G5-004": {"case": "伯乐排期建议采纳率（>=60%）", "verdict": "BLOCKED",
                      "honest_note": "依赖智语伯乐接入排期流程 >=4 周期台账，手册允许 BLOCKED"},
        "TC-G5-005": case_g5_005(),
        "TC-G5-006": {"case": "G5 回归门禁（启动前置）", "verdict": "BLOCKED",
                      "honest_note": "启动前置：G5 其余用例执行完毕；回归集（G1 三项+G2 十用例"
                                     "+G3 五项+G4 抽样）清单与历史留证已对齐"},
    }
    summary = {cid: c["verdict"] for cid, c in cases.items()}
    report = {"testcase": "TC-G5 门禁执行器首轮运行（骨架生产化）",
              "gate_summary": summary,
              "gate_verdict": "BLOCKED-partial" if summary["TC-G5-003"] == "partial"
              else "FAIL",
              "cases": cases,
              "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    print(json.dumps({"gate_summary": summary,
                      "gate_verdict": report["gate_verdict"]},
                     ensure_ascii=False, indent=2))
    Path(args.out).write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[g5] 报告已落盘 {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
