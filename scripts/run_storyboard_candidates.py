# ==============================================================
# run_storyboard_candidates.py — 分镜候选选帧闸门（63 号 A3 落位）
# 对标 OnlyShot Phase 1.5（每 grid 1-4 候选，先锁构图再出视频，修改成本
#   降至视频层 1/18）。本项目静态镜先行已具架构位，本脚本把「候选-预分-
#   人工终选」做成显式工作流：
#   1) 每镜生成 N 个候选（镜内种子偏移 seed+i）
#   2) AnchorGuard.post_check 逐候选预打分（与生产同口径）
#   3) 相似度降序排名 → candidates_report.json
#   4) --pick sid:rank 人工终选回写 images/{sid}.png + manifest 留证
# 用法：
#   生成+打分：python scripts/run_storyboard_candidates.py \
#     --project g4-ep01 --episode 1 --limit 2 --candidates 3
#   人工终选：--project g4-ep01 --pick shot-EP01-001:1
# 成本纪律：候选仅静态图层（与生产同口径 1024px，可比性优先）；视频层
#   依旧只在终选后跑——前置迭代不触发视频重生成。
# ==============================================================
import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

# 集中配置（P2 专项 2026-10-05 迁移）：路径/端口/生产根单一出口 scripts/env.py
sys.path.insert(0, str(Path(__file__).resolve().parent))
from env import (COMPONENTS, MANJU, SCRIPT_ENGINE,  # noqa: E402
                 HERO, PROJECT_ROOT, comfy_env)

REPO = Path(__file__).resolve().parents[1]
LIBRARY = MANJU / "backend" / "face_library_sd"

comfy_env()  # COMFYUI_URL/MODEL/TIMEOUT 统一 setdefault（env.py）

import types  # noqa: E402
_m = types.ModuleType("milvus_retriever")


class _S:
    def __init__(self, *_args, **_kwargs):
        pass

    def search(self, *_args, **_kwargs):
        raise ConnectionError("stub")


setattr(_m, "MilvusRetriever", _S)
sys.modules["milvus_retriever"] = _m
for p in (COMPONENTS, MANJU / "backend", SCRIPT_ENGINE, REPO / "scripts"):
    sys.path.insert(0, str(p))

from drama_stage_adapter import DramaToolGateway  # type: ignore
from app.modules.consistency_engine.face_encoder import FaceEncoder  # type: ignore
from app.modules.consistency_engine.anchor_guard import AnchorGuard  # type: ignore
from splitter import split_chapters  # type: ignore
from episode_planner import plan_episodes  # type: ignore
from extractor import extract_elements  # type: ignore
from storyboard_schema import draft_storyboard  # type: ignore
from run_batch_shots import NOVEL, REF_STYLE  # type: ignore


def build_report(proj: Path, shots: list[dict], n_cand: int,
                 args) -> dict:
    """逐镜生成 N 候选 + anchor 预打分排名。"""
    gw = DramaToolGateway()
    guard = AnchorGuard(library_root=str(LIBRARY))
    report: dict = {"project": args.project, "episode": args.episode,
                    "candidates_per_shot": n_cand, "ref_image": args.ref_image,
                    "lora": args.lora or None, "ipa_weight": args.ipa_weight,
                    "shots": [], "generated_at":
                    time.strftime("%Y-%m-%dT%H:%M:%S")}
    for shot in shots[:args.limit]:
        sid = shot["shot_id"]
        base_seed = int(sid.split("-")[-1]) * 7 + 1000
        cdir = proj / "candidates" / sid
        cdir.mkdir(parents=True, exist_ok=True)
        rows = []
        for i in range(n_cand):
            seed = base_seed + i
            cpath = cdir / f"c{i}_seed{seed}.png"
            try:
                gen = gw.text_to_image(
                    f"{REF_STYLE}, {shot['description']}",
                    ref_assets=[args.char], out_path=str(cpath), seed=seed,
                    ref_image=args.ref_image, lora=args.lora or None,
                    ipa_weight=args.ipa_weight)
                if gen["status"] != "ok":
                    rows.append({"candidate": i, "seed": seed,
                                 "status": gen["status"]})
                    continue
                chk = guard.post_check(args.char, str(cpath), attempts=1)
                rows.append({"candidate": i, "seed": seed,
                             "status": "ok",
                             "similarity": chk.get("similarity"),
                             "action": chk["action"]})
            except Exception as exc:  # noqa: BLE001 单候选异常不断批
                rows.append({"candidate": i, "seed": seed,
                             "status": "error",
                             "error": f"{type(exc).__name__}: {exc}"})
        scored = sorted((r for r in rows if r.get("similarity") is not None),
                        key=lambda r: r["similarity"], reverse=True)
        for rank, r in enumerate(scored, 1):
            r["rank"] = rank
        best = scored[0] if scored else None
        report["shots"].append({"shot_id": sid, "base_seed": base_seed,
                                "candidates": rows,
                                "recommended": best and
                                {"rank": best["rank"], "seed": best["seed"],
                                 "similarity": best["similarity"]}})
        print(f"[cand] {sid}: 推荐 "
              f"{best and f"c{best['candidate']}（sim={best['similarity']}）" or "无有效候选"}")
    return report


def pick(proj: Path, sid: str, rank: int, report: dict) -> int:
    """人工终选：rank 候选拷贝为正式产物 + manifest 留证。"""
    shot_row = next((s for s in report["shots"] if s["shot_id"] == sid), None)
    if not shot_row:
        print(f"[pick] 错误：{sid} 不在候选报告内")
        return 1
    cand = next((c for c in shot_row["candidates"] if c.get("rank") == rank),
                None)
    if not cand or not cand.get("seed"):
        print(f"[pick] 错误：{sid} 无 rank={rank} 有效候选")
        return 1
    src = proj / "candidates" / sid / f"c{cand['candidate']}_seed{cand['seed']}.png"
    dst = proj / "images" / f"{sid}.png"
    if not src.exists():
        print(f"[pick] 错误：候选文件缺失 {src}")
        return 1
    shutil.copyfile(src, dst)
    mf_p = proj / "state" / "manifest.json"
    if mf_p.exists():
        mf = json.loads(mf_p.read_text(encoding="utf-8"))
        row: dict = next((r for r in mf.get("shots", [])
                          if r.get("shot_id") == sid), None) or \
            {"shot_id": sid}
        if row not in mf.get("shots", []):
            mf.setdefault("shots", []).append(row)
        row.update(action="accept", similarity=cand.get("similarity"),
                   candidate_picked={"rank": rank, "seed": cand["seed"],
                                     "source": str(src.relative_to(proj))})
        mf_p.write_text(json.dumps(mf, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    print(f"[pick] 终选落位：{sid} ← c{cand['candidate']}"
          f"（sim={cand.get('similarity')}）→ {dst}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--char", default="sd-hero")
    ap.add_argument("--episode", type=int, default=1)
    ap.add_argument("--limit", type=int, default=2)
    ap.add_argument("--candidates", type=int, default=3)
    ap.add_argument("--ref-image", default="hero_base.png")
    ap.add_argument("--lora", default=os.getenv("CHAR_LORA", ""))
    ap.add_argument("--ipa-weight", type=float,
                    default=float(os.getenv("IPA_WEIGHT", "0.15")))
    ap.add_argument("--root", default=str(PROJECT_ROOT))
    ap.add_argument("--pick", default="",
                    help="人工终选：shot_id:rank（如 shot-EP01-001:1）")
    args = ap.parse_args()

    proj = Path(args.root) / args.project
    for sub in ("candidates", "images", "state"):
        (proj / sub).mkdir(parents=True, exist_ok=True)

    if args.pick:
        rp = proj / "state" / "candidates_report.json"
        if not rp.exists():
            print(f"[pick] 错误：候选报告缺失 {rp}（先跑生成打分模式）")
            return 1
        report = json.loads(rp.read_text(encoding="utf-8"))
        sid, rank = args.pick.rsplit(":", 1)
        return pick(proj, sid, int(rank), report)

    # 特征库保障（与 run_batch_shots 同口径）
    if not (LIBRARY / args.char / "feature.npy").exists():
        shutil.rmtree(LIBRARY / args.char, ignore_errors=True)
        src = os.environ.get("CHAR_BASE_IMAGE", str(HERO))
        FaceEncoder(library_root=str(LIBRARY)).save_character(
            args.char, args.char, src)

    els = extract_elements(NOVEL)
    eps = plan_episodes(split_chapters(NOVEL))
    ep = eps[args.episode - 1]
    sb = draft_storyboard(args.project, ep, els,
                          trace_id=f"trace-CAND-EP{args.episode:02d}")
    report = build_report(proj, sb["shots"], args.candidates, args)
    out = proj / "state" / "candidates_report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"[cand] 报告落位：{out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
