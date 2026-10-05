# ==============================================================
# run_storyboard_critique.py — 分镜自批判环（63 号 A6 落位）
# 对标 MiraFrame CRITIQUE_*（SCORE_THRESHOLD / MAX_ROUNDS 阈值化重roll）
#   + OnlyShot 阶段5 六维度批判。
# 实现口径：遵循 run_quality_review 既有先例——LLM 批判依赖 vLLM 后端，
#   本执行器为其规则化降级实现（架构文档降级策略合法路径），六维各 100
#   分确定性打分；LLM 增强口预留（vLLM 后端就绪后接入，接口不变）。
# 六维：节奏（beat 覆盖+变奏）/冲突/画面性/对白/钩子/一致性
# 用法：python scripts/run_storyboard_critique.py --storyboard <sb.json> \
#         [--threshold 70] [--out 报告.json]
# 退出码：0=pass / 2=revise（阈值未达，附改进建议；夜批前置闸门语义）
# ==============================================================
import argparse
import json
import math
import sys
from pathlib import Path

CONFLICT_WORDS = ("杀", "追", "毒", "疑", "符", "封", "尸", "剑", "黑衣",
                  "失踪", "暴", "破", "追出", "翻检", "攥紧")
SUSPENSE_WORDS = ("为何", "是谁", "要么", "远比", "竟", "忽", "第一", "深")


def critique_storyboard(sb: dict, threshold: float) -> dict:
    """六维规则化评分（各 0-100），返回明细+综合+建议。"""
    shots = sb.get("shots", [])
    n = len(shots)
    dims: dict[str, dict] = {}
    if n == 0:
        return {"verdict": "revise", "total": 0,
                "suggestions": ["分镜为空"], "dims": {}}

    # 1) 节奏维：时长变奏（方差）+ 镜数密度（90s 窗口 >=8 镜）
    durs = [float(s.get("duration_sec") or 0) for s in shots]
    mean_d = sum(durs) / n
    variance = sum((d - mean_d) ** 2 for d in durs) / n
    s_rhythm = min(60.0, variance * 60.0) + (40.0 if n >= 8 else n / 8 * 40)
    dims["节奏"] = {"score": round(s_rhythm, 1),
                    "duration_variance": round(variance, 3),
                    "shots": n}

    # 2) 冲突维：冲突词覆盖镜头占比（>=60% 满分线性折算）
    conflict_n = sum(1 for s in shots
                     if any(w in (s.get("description") or "")
                            for w in CONFLICT_WORDS))
    dims["冲突"] = {"score": round(min(100.0, conflict_n / n / 0.6 * 100), 1),
                    "conflict_shots": conflict_n}

    # 3) 画面性维：景别多样性（分布熵归一）+ image_prompt 非空率
    types = [s.get("shot_type") or "无" for s in shots]
    probs = [types.count(t) / n for t in set(types)]
    entropy = -sum(p * math.log2(p) for p in probs if p > 0)
    max_entropy = math.log2(len(set(types))) if len(set(types)) > 1 else 1.0
    prompt_ok = sum(1 for s in shots if (s.get("image_prompt") or "").strip())
    s_visual = (entropy / max_entropy * 60 if max_entropy else 0) \
        + prompt_ok / n * 40
    dims["画面性"] = {"score": round(s_visual, 1),
                      "shot_type_entropy": round(entropy, 2),
                      "prompt_coverage": f"{prompt_ok}/{n}"}

    # 4) 对白维：对白镜占比（20%-60% 区间满分钟形）+ 短句率（<=30 字）
    dlg = [s for s in shots if s.get("dialogue")]
    ratio = len(dlg) / n
    bell = max(0.0, 1 - abs(ratio - 0.4) / 0.4)
    short = sum(1 for s in dlg if len(s.get("dialogue") or "") <= 30)
    s_dialog = bell * 60 + (short / len(dlg) * 40 if dlg else 0)
    dims["对白"] = {"score": round(s_dialog, 1), "dialogue_ratio":
                    round(ratio, 2), "short_line_rate":
                    round(short / len(dlg), 2) if dlg else 0.0}

    # 5) 钩子维：hook_flag 首尾镜 + 尾镜悬念词
    hooks = [s for s in shots if s.get("hook_flag")]
    tail = shots[-1]
    s_hook = (20 if any(s is shots[0] for s in hooks) else 0) \
        + (40 if hooks else 0) \
        + (40 if any(w in (tail.get("dialogue") or "")
                     or w in (tail.get("description") or "")
                     for w in SUSPENSE_WORDS) else 0)
    dims["钩子"] = {"score": round(s_hook, 1), "hook_shots": len(hooks)}

    # 6) 一致性维：consistency_anchor 全覆盖 + image_prompt 含锚标记
    anchored = sum(1 for s in shots
                   if s.get("consistency_anchor")
                   or "锚" in (s.get("image_prompt") or ""))
    dims["一致性"] = {"score": round(anchored / n * 100, 1),
                      "anchored": f"{anchored}/{n}"}

    total = round(sum(d["score"] for d in dims.values()) / len(dims), 1)
    verdict = "pass" if total >= threshold else "revise"
    weakest = sorted(dims.items(), key=lambda kv: kv[1]["score"])[:2]
    suggestions = [f"「{name}」维度最低（{d['score']}）——"
                   f"{_advice(name)}" for name, d in weakest]
    return {"verdict": verdict, "total": total, "threshold": threshold,
            "dims": dims, "suggestions": suggestions,
            "llm_enhance": "预留口：vLLM 后端就绪后接入语义批判（接口不变）"}


def _advice(name: str) -> str:
    return {
        "节奏": "调 duration_sec 形成 1-3s 变奏，并保证镜数密度",
        "冲突": "为低冲突镜补对抗性描写（对峙/追击/悬念动作）",
        "画面性": "丰富景别分布（远/中/近/特轮换），补全 image_prompt",
        "对白": "对白占比向 40% 靠拢，长句拆短句（<=30 字）",
        "钩子": "首镜强化对抗式开场，尾镜补悬念词/倒计时",
        "一致性": "补 consistency_anchor 或 image_prompt 角色锚标记",
    }.get(name, "人工复核该维度")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--storyboard", required=True)
    ap.add_argument("--threshold", type=float, default=70.0)
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    sb = json.loads(Path(args.storyboard).read_text(encoding="utf-8"))
    report = critique_storyboard(sb, args.threshold)
    report["storyboard"] = args.storyboard
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.out:
        Path(args.out).write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8")
    return 0 if report["verdict"] == "pass" else 2


if __name__ == "__main__":
    sys.exit(main())
