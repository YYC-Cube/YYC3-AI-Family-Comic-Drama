# ==============================================================
# run_quality_review.py — G4 内容质检评审 + 交付物规范校验执行器
# 覆盖：TC-G4-005（五维自动评审，≥80 红线，对齐格物宗师 validate 契约）
#       TC-G4-008（交付物规范：命名/元数据/落位）
# 说明：格物宗师 LLM validate 依赖 vLLM 后端；本执行器为其规则化降级
#       实现（架构文档 4.1 降级策略合法路径），五维各 20 分确定性打分。
#       人工抽检（≥10%）由执行人对抽检集逐镜核对后回填 review 命令。
# 用法：
#   自动评审：.venv/bin/python scripts/run_quality_review.py \
#     --projects g4-ep01,g4-ep02,g4-ep03 --dynamic-conf '{"g4-ep01":6.413}'
#   人工抽检回填：--human-check g4-ep02 --human-agree 3 --human-total 3
# ==============================================================
import argparse
import json
import subprocess
import sys
from pathlib import Path

RED_LINE = 80.0


def ffprobe(path: str) -> dict:
    """取视频轨规格（codec,width,height,r_frame_rate）与格式时长。"""
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=codec_name,width,height,r_frame_rate",
             "-show_entries", "format=duration",
             "-of", "json", path],
            capture_output=True, text=True, timeout=30)
        j = json.loads(r.stdout)
        st = (j.get("streams") or [{}])[0]
        return {"codec": st.get("codec_name"), "width": st.get("width"),
                "height": st.get("height"), "fps": st.get("r_frame_rate"),
                "duration": float(j.get("format", {}).get("duration", 0) or 0)}
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)}


def audio_codec(path: str) -> str:
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "a:0",
             "-show_entries", "stream=codec_name", "-of", "csv=p=0", path],
            capture_output=True, text=True, timeout=30)
        return r.stdout.strip()
    except Exception:  # noqa: BLE001
        return ""


def review_episode(proj_dir: Path, dynamic_conf: "float | None" = None) -> dict:
    """单集五维评审（各维 20 分），返回明细与得分。"""
    name = proj_dir.name
    # 集号解析（2026-10-05 通用化）：取项目名末段数字（g4-ep01→1，
    # sdxl-prod-001→1）；无数字回退整名去非数字（保持旧口径行为）
    tail = "".join(ch for ch in name.split("-")[-1] if ch.isdigit())
    ep_no = tail or "".join(ch for ch in name if ch.isdigit())
    full = proj_dir / "output" / f"{name}_full.mp4"
    if not full.exists():  # 兼容旧命名产物 g4_epNN_full.mp4
        full = proj_dir / "output" / f"g4_ep{ep_no}_full.mp4"
    manifest_p = proj_dir / "state" / "manifest.json"
    sb_p = proj_dir / "storyboard" / "storyboard.v1.json"
    d = {"episode": name, "full": str(full), "dims": {}}

    # 维度1 规格维（20）：成片 1080p30 h264（12）+ aac 音轨（4）+ 时长>0（4）
    spec = ffprobe(str(full)) if full.exists() else {"error": "成片不存在"}
    s1 = 0
    ok_video = (spec.get("codec") == "h264" and spec.get("width") == 1920
                and spec.get("height") == 1080 and spec.get("fps") == "30/1")
    s1 += 12 if ok_video else 0
    s1 += 4 if audio_codec(str(full)) == "aac" else 0
    s1 += 4 if float(spec.get("duration") or 0) > 0 else 0
    d["dims"]["规格"] = {"score": s1, "spec": spec, "audio": audio_codec(str(full))}

    # 维度2 时长维（20）：集时长 ≤120s（10）+ ≥3s 下限（10，排除空片）
    dur = float(spec.get("duration") or 0)
    s2 = (10 if 0 < dur <= 120 else 0) + (10 if dur >= 3 else 0)
    d["dims"]["时长"] = {"score": s2, "duration": dur, "window": "3s-120s"}

    # 维度3 元数据维（20）：manifest（5）+ storyboard（5）+ trace_id 带 EP 号（5）
    #   + 各镜 seed 留痕（5）
    m = json.loads(manifest_p.read_text(encoding="utf-8")) if manifest_p.exists() else {}
    sb = json.loads(sb_p.read_text(encoding="utf-8")) if sb_p.exists() else {}
    trace = (sb.get("trace_id") or m.get("trace_id") or "")
    s3 = (5 if m else 0) + (5 if sb else 0) + (5 if f"EP{int(ep_no):02d}" in trace else 0)
    s3 += 5 if all("seed" in s for s in m.get("shots", [])) and m.get("shots") else 0
    d["dims"]["元数据"] = {"score": s3, "trace_id": trace, "shots": len(m.get("shots", []))}

    # 维度4 质量维（20）：动态镜口型 conf（10，有 conf 且 ≥0.75 满分，
    #   有记录未达标得 4）+ 静态镜一致性链留痕（10）
    s4 = 0
    if dynamic_conf is not None:
        s4 += 10 if dynamic_conf >= 0.75 else 4
    sim_records = [s.get("similarity") for s in m.get("shots", [])
                   if s.get("similarity") is not None]
    s4 += 10 if sim_records else 0
    d["dims"]["质量"] = {"score": s4, "dynamic_conf": dynamic_conf,
                        "static_sim": sim_records}

    # 维度5 交付维（20）：{project} 目录规范（10）+ 成片命名规范（10）
    layout_ok = all((proj_dir / sub).exists()
                    for sub in ("storyboard", "images", "audio", "state", "output"))
    s5 = (10 if layout_ok else 0) + (10 if full.exists() else 0)
    d["dims"]["交付"] = {"score": s5, "layout_ok": layout_ok, "full_exists": full.exists()}

    d["score"] = sum(v["score"] for v in d["dims"].values())
    d["passed"] = d["score"] >= RED_LINE
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--projects", default="g4-ep01,g4-ep02,g4-ep03",
                    help="逗号分隔的集目录名")
    ap.add_argument("--root", default="/tmp/yyc3_projects")
    ap.add_argument("--dynamic-conf", default="{}",
                    help='JSON：{集名: 动态镜 SyncNet conf}（如 {"g4-ep01":6.413}）')
    ap.add_argument("--human-check", default=None,
                    help="人工抽检集名（≥10%% 口径：抽检集镜头数即计入）")
    ap.add_argument("--human-agree", type=int, default=0, help="人工与自动结论一致镜头数")
    ap.add_argument("--human-total", type=int, default=0, help="人工抽检镜头总数")
    ap.add_argument("--out", default=None, help="评审结果 JSON 落盘路径")
    args = ap.parse_args()

    conf_map = json.loads(args.dynamic_conf)
    results = [review_episode(Path(args.root) / p.strip(), conf_map.get(p.strip()))
               for p in args.projects.split(",") if p.strip()]

    report = {"testcase": "TC-G4-005 内容质检评审 + TC-G4-008 交付物规范",
              "executor": "run_quality_review.py（格物宗师 validate 规则化降级实现）",
              "red_line": RED_LINE, "episodes": results,
              "avg_score": round(sum(r["score"] for r in results) / len(results), 1),
              "all_passed": all(r["passed"] for r in results)}

    if args.human_check:
        agree, total = args.human_agree, args.human_total
        rate = round(agree / total * 100, 1) if total else 0.0
        report["human_review"] = {"episode": args.human_check, "agree": agree,
                                  "total": total, "consistency_rate": rate,
                                  "threshold": "≥80%", "passed": rate >= 80.0}

    out = json.dumps(report, ensure_ascii=False, indent=2)
    print(out)
    if args.out:
        Path(args.out).write_text(out, encoding="utf-8")
    verdict = (report["all_passed"]
               and report.get("human_review", {}).get("passed", True))
    print(f"[结论] 均分 {report['avg_score']} / 红线 {RED_LINE} / "
          f"{'PASS' if verdict else 'FAIL'}")
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
