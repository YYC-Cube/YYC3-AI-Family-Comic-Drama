# ==============================================================
# run_rhythm_check.py — 秒级节奏地图校验（63 号 A2 落位）
# 对标 OnlyShot 节奏地图（36 grid × 4-10s）+ 红果必爆 7 招。
# 折算红线（63 号文档明示）：红果 7 招节点秒数基于 180-195s 剧集实测，
#   本项目单集 90s 窗口——节点按 target_s = base_s × (集长/180) 等比折算，
#   禁止盲抄 180s 原始秒数。
# 规则化推断（诚实声明）：beat 覆盖判定为几何规则（镜头时间区间包含节点），
#   不做语义判定；建议标注位供人工/分镜 v2 回写，非强制语义正确。
# 用法：
#   python scripts/run_rhythm_check.py --storyboard <storyboard.v1.json>
#   追加回写：--write-back（生成 storyboard.v2.json，shot 增 beat 建议）
#   留证：--out 报告.json
# ==============================================================
import argparse
import json
import sys
from pathlib import Path

# 红果必爆 7 招（180s 基准节点秒）：
#   对抗式开场 0s / 30s 爆破 / 60s 爽点 / 90s 反转 / 120s 爽点 / 150s 钩子 / 180s 倒计时
RED_FRUIT_NODES: list[tuple[str, float]] = [
    ("cold_open", 0.0), ("blast", 30.0), ("satisfaction_1", 60.0),
    ("twist", 90.0), ("satisfaction_2", 120.0), ("hook", 150.0),
    ("countdown", 180.0),
]
BASE_EP_LEN = 180.0


def build_rhythm_map(shots: list[dict]) -> dict:
    """镜头时间轴 + 7 招折算节点覆盖判定。

    返回 {timeline, ep_len, beats, coverage, suggestions}。
    """
    timeline: list[dict] = []
    t = 0.0
    for s in shots:
        dur = float(s.get("duration_sec") or 0)
        timeline.append({"shot_id": s.get("shot_id"), "start": round(t, 2),
                         "end": round(t + dur, 2), "duration": dur,
                         "hook_flag": bool(s.get("hook_flag"))})
        t += dur
    ep_len = t
    ratio = ep_len / BASE_EP_LEN if ep_len else 0.0

    beats: list[dict] = []
    for name, base_s in RED_FRUIT_NODES:
        target = round(base_s * ratio, 2)
        # cold_open 特例：锚定首镜（始终覆盖），区间 0 至首镜时长
        hit = next((row for row in timeline
                    if row["start"] <= target < row["end"]
                    or (name == "cold_open" and row["start"] == 0)), None)
        beats.append({"beat": name, "base_s": base_s, "target_s": target,
                      "covered_by": hit["shot_id"] if hit else None,
                      "ok": hit is not None})
    covered = sum(1 for b in beats if b["ok"])
    # 节奏变化度：时长方差（全等时长=节奏单一，OnlyShot 4-10s 变奏思想）
    durs = [row["duration"] for row in timeline]
    mean_d = sum(durs) / len(durs) if durs else 0.0
    variance = round(sum((d - mean_d) ** 2 for d in durs) / len(durs), 3) \
        if durs else 0.0
    suggestions = [f"{b['beat']} 节点 {b['target_s']}s 未被镜头覆盖——"
                   f"建议在时间轴 {b['target_s']}s 附近镜头标注 beat（"
                   f"或调时长命中）" for b in beats if not b["ok"]]
    return {"timeline": timeline, "ep_len_s": round(ep_len, 2),
            "ratio_vs_180s": round(ratio, 3), "beats": beats,
            "coverage": f"{covered}/{len(beats)}",
            "duration_variance": variance, "suggestions": suggestions}


def write_back(shots: list[dict], beats: list[dict]) -> list[dict]:
    """把 beat 建议回写到 shot（v2 字段 beat：命中节点名列表）。"""
    by_shot: dict[str, list[str]] = {}
    for b in beats:
        if b["covered_by"]:
            by_shot.setdefault(b["covered_by"], []).append(b["beat"])
    for s in shots:
        sid = str(s.get("shot_id") or "")
        s["beat"] = by_shot.get(sid, [])
    return shots


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--storyboard", required=True)
    ap.add_argument("--write-back", action="store_true",
                    help="生成 storyboard.v2.json（shot 增 beat 字段）")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    p = Path(args.storyboard)
    sb = json.loads(p.read_text(encoding="utf-8"))
    report = build_rhythm_map(sb.get("shots", []))
    report["storyboard"] = str(p)
    print(json.dumps({k: report[k] for k in
                      ("ep_len_s", "ratio_vs_180s", "coverage",
                       "duration_variance", "beats", "suggestions")},
                     ensure_ascii=False, indent=2))
    if args.write_back:
        sb["shots"] = write_back(sb.get("shots", []), report["beats"])
        v2 = p.with_name("storyboard.v2.json")
        v2.write_text(json.dumps(sb, ensure_ascii=False, indent=2),
                      encoding="utf-8")
        print(f"[rhythm] beat 标注已回写：{v2}")
    if args.out:
        Path(args.out).write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
