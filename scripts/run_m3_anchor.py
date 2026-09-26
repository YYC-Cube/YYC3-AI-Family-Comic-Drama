# ==============================================================
# run_m3_anchor.py — M3 主体：anchor_guard 三段锚定联调（TC-G3-003 打回闭环）
# 前置：face_library 真实模式建库（本脚本进程内重建，同 FaceEncoder 代码路径）
# 运行：yyc3-ai-manju-studio/.venv/bin/python scripts/run_m3_anchor.py
# 素材：/tmp/g3_faces/char{A,B}_shot{1,2}.png（G3 预研同源）
# ==============================================================
import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MANJU = REPO / "yyc3-ai-manju-studio"
FACES = Path("/tmp/g3_faces")
LIBRARY = MANJU / "backend" / "face_library"

sys.path.insert(0, str(MANJU / "backend"))
from app.modules.consistency_engine.face_encoder import FaceEncoder, FEATURE_DIM  # noqa: E402
from app.modules.consistency_engine.anchor_guard import (  # noqa: E402
    AnchorGuard, MAX_ATTEMPTS)

RESULTS = {}


def rebuild_library():
    """生产兜底库重建（真实模式；G3-001 同一代码路径）"""
    enc = FaceEncoder(library_root=str(LIBRARY))
    if LIBRARY.exists():
        shutil.rmtree(LIBRARY)
    mapping = {"hero": FACES / "charA_shot1.png", "villain": FACES / "charB_shot1.png"}
    manifests = [enc.save_character(cid, cid, str(img)) for cid, img in mapping.items()]
    (LIBRARY / "index.json").write_text(
        json.dumps(manifests, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifests


def main():
    manifests = rebuild_library()
    modes = {m["char_id"]: m["mode"] for m in manifests}
    print(f"[建库] {modes}")
    guard = AnchorGuard(library_root=str(LIBRARY))
    assert guard.encoder.mode == "insightface", "锚定守卫必须运行于真实模型模式"

    # ── 生成前：锚定 ──
    pre = guard.pre_anchor("hero", "月光下的义庄门口，hero 回头凝视")
    pre_blocked = guard.pre_anchor("ghost", "未建库角色")
    r_pre = {
        "hero 锚定成功且 dim=512": pre["ok"] and pre["reference_dim"] == FEATURE_DIM,
        "锚定前缀生成": "一致性锚定" in pre["anchor_prompt_prefix"],
        "未建库角色 BLOCKED": pre_blocked["action"] == "blocked",
    }

    # ── 生成中：约束（桩态）──
    mid = guard.during_constraint("hero")
    r_mid = {"controlnet 约束描述（桩态）": mid["constraint"] == "controlnet_pose"
             and mid["mode"] == "stub"}

    # ── 生成后：打回闭环（TC-G3-003 核心）──
    # attempt1：模拟生成器产出「错人帧」（villain 的变体）
    chk1 = guard.post_check("hero", str(FACES / "charB_shot2.png"), attempts=1)
    # attempt2：重绘产出「同人帧」（hero 的跨镜头变体，G3-002 实证 0.9643）
    chk2 = guard.post_check("hero", str(FACES / "charA_shot2.png"), attempts=2)
    # 超限路径：连续错人达上限
    chk3 = guard.post_check("hero", str(FACES / "charB_shot2.png"), attempts=2)

    print(f"[闭环] attempt1（错人帧）: action={chk1['action']} sim={chk1['similarity']}")
    print(f"[闭环] attempt2（同人帧）: action={chk2['action']} sim={chk2['similarity']}")
    print(f"[闭环] 超限（错人帧×2）  : action={chk3['action']} attempts={chk3['attempts']}")

    r_post = {
        "错人帧 similarity<0.5": chk1["similarity"] is not None and chk1["similarity"] < 0.5,
        "错人帧被 REDRAW（触发重绘）": chk1["action"] == "redraw",
        "同人帧 similarity≥0.85": chk2["similarity"] is not None
                                   and chk2["similarity"] >= 0.85,
        "同人帧被 ACCEPT": chk2["action"] == "accept",
        "重绘上限 MAX_ATTEMPTS=2": MAX_ATTEMPTS == 2,
        "超限转人工 ESCALATE": chk3["action"] == "escalate",
        "全程真实模型特征（无哈希降级）": guard.encoder.last_mode == "insightface",
    }

    RESULTS["pre_anchor"] = r_pre
    RESULTS["during_constraint"] = r_mid
    RESULTS["post_check"] = r_post
    all_checks = {**r_pre, **r_mid, **r_post}
    for k, v in all_checks.items():
        print(f"  {'PASS' if v else 'FAIL'}  {k}")

    n_fail = sum(1 for v in all_checks.values() if not v)
    print(f"\n=== TC-G3-003 三段锚定联调："
          f"{'PASS' if n_fail == 0 else 'FAIL'}（{len(all_checks) - n_fail}/{len(all_checks)}）===")
    print(json.dumps({"tc": "TC-G3-003", "status": "PASS" if n_fail == 0 else "FAIL",
                      "checks": all_checks,
                      "evidence": {"attempt1": chk1, "attempt2": chk2, "escalate": chk3}},
                     ensure_ascii=False, indent=2))
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
