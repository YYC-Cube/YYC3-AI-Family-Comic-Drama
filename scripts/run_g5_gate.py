# ==============================================================
# run_g5_gate.py — G5 门禁执行器（骨架生产化 · HANDOFF 34.4 P2 → 35.4 续作）
# 职责：TC-G5-001~006 六用例统一收割口径——有数据即真实计算判定，
#   无数据按手册允许 BLOCKED 留证（对齐 G4 002/009 先例），不虚构 PASS。
# 可执行件：TC-G5-003 LoRA 增量训练触发判定（均值口径 mean < 0.85 触发，
#   与 M3 二轮生产上线决策一致：v2 组合峰值 mean 0.8669 达标上线）——
#   以留证评测 JSON 为输入真实跑判定，输出准确率与误触发率。
# 35.4 升级：①新增 v2m777 档（历史参考系重评分 mean 0.8586，不触发，
#   预期 False）；②增量重训已真实执行（v2 起步 + 8x777 样本 + 540 步，
#   n1 远端留证）；③复测结论如实 FAIL（777 种子 min 0.7269 < 0.85
#   手册预期未达，泛化目标未达成，生产维持 v2）。
# 运行：yyc3-ai-manju-studio/.venv/bin/python scripts/run_g5_gate.py \
#   --out docs/attachments/G4-20261002/tc-g5-gate-run-20261002.json
# ==============================================================
import argparse
import json
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EVID = REPO / "docs" / "attachments" / "G4-20260929"
EVID2 = REPO / "docs" / "attachments" / "G4-20261002"

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


def _histref_group(tag: str) -> dict:
    """从 20261002 历史参考系终裁报告中按 tag 取组（含 mean/min/逐种子）。"""
    for g in load_json(EVID2 / "final_eval_histref.json")["groups"]:
        if g["tag"] == tag:
            return g
    raise KeyError(tag)


def case_g5_003() -> dict:
    """触发判定真实执行：四档留证模型逐个过判定器（35.4 追加 v2m777）。"""
    v2m777 = _histref_group("v2m777_combo_w015")
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
        ("sd-hero-v2m777（v2+8x777 增量续训 540 步）", v2m777["mean"],
         "G4-20261002/final_eval_histref.json#v2m777_combo_w015"),
    ]
    expected = [False, True, True, False]  # v2/v2m777 达标不触发；v3/v3r32 滑落必触发
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

    # 35.4：增量重训已真实执行（HANDOFF 35.4 P2，n1 远端 kohya 540 步）
    step2 = {
        "verdict": "DONE",
        "note": "35.4 P2 真实执行：v2 checkpoint 起步（network_weights 口径）+ 8 张 777 "
                "挖掘样本（27 图混合集，无 caption 走 class token）+ dim32/alpha16 + "
                "lr 1e-4 constant + 2 epochs（540/540 步，1.14it/s，bf16/fp16 保存）",
        "artifacts": ["sd-hero-v2m777.safetensors（最终 2ep，fp16，37.8MB）",
                      "sd-hero-v2m777-000001.safetensors（1ep 中间档）"],
        "evidence": "G4-20261002/train_v2m777.log",
    }
    # 35.4：复测结论如实——均值守住 0.85 线但 min 未达手册预期
    v2_rebase = _histref_group("v2_rebase_combo_w015")
    step3_pass = v2m777["min"] >= TRIGGER_THRESHOLD
    step3 = {
        "verdict": "PASS" if step3_pass else "FAIL",
        "mean": v2m777["mean"], "min": v2m777["min"], "max": v2m777["max"],
        "per_seed": {str(r["seed"]): r["sim"] for r in v2m777["rows"]},
        "baseline_v2": {"mean": v2_rebase["mean"], "min": v2_rebase["min"]},
        "evidence": "G4-20261002/final_eval_histref.json（历史参考系 input/hero_base.png，"
                    "库向量校准 1.0）",
        "note": "均值口径守住 0.85 线（0.8586≥0.85，触发判定不触发）但手册预期 min≥0.85 "
                "未达：777 种子 0.7846→0.7269 反降——777 样本系 v2 自生成同分布，续训巩固"
                "而非泛化；1ep 中间档 min 0.7256 同样未达；生产维持 v2，不替换",
    }
    case_pass = step1_pass and step3_pass
    return {
        "case": "TC-G5-003 LoRA 增量训练触发验证",
        "step1_trigger_judgement": {
            "rule": f"组合峰值 mean < {TRIGGER_THRESHOLD} 触发（均值口径上线门槛）",
            "rows": rows, "accuracy": acc, "false_trigger_count": false_fires,
            "verdict": "PASS" if step1_pass else "FAIL"},
        "step2_incremental_retrain": step2,
        "step3_re_eval": step3,
        "verdict": "PASS" if case_pass else "FAIL",
        "honest_note": "①触发判定 100% 准确/零误触发（四档真实执行，含 35.4 追加 v2m777）；"
                       "②增量重训已真实执行（非模拟）；③复测均值守线但 min 0.7269<0.85 "
                       "手册预期未达，如实 FAIL——泛化目标未达成，生产维持 v2",
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
    # 总裁决语义：TC-G5-003 全链 PASS → 其余用例仍属运营依赖 BLOCKED（BLOCKED-partial）；
    # 003 任一步未达 → FAIL（如实，不虚构）
    report = {"testcase": "TC-G5 门禁执行器（骨架生产化 · 35.4 复跑）",
              "gate_summary": summary,
              "gate_verdict": "BLOCKED-partial" if summary["TC-G5-003"] == "PASS"
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
