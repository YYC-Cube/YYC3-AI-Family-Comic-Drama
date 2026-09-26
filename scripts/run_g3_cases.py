# ==============================================================
# run_g3_cases.py — G3 一致性专项预研执行器（YYC3-60 §五 TC-G3-001/002）
# 前置：insightface buffalo_l 真实模型（manju-studio/.venv）+ 人脸测试图
# 运行：yyc3-ai-manju-studio/.venv/bin/python scripts/run_g3_cases.py
# 说明：建库逻辑与 scripts/build_face_library.py 同一 FaceEncoder 代码路径，
#       进程内执行（无子进程拼装）；脚本本体另行直跑留证于验收记录
# 素材：/tmp/g3_faces/char{A,B}_shot{1,2}.png（shot2=同源裁剪/亮度/JPEG 变体，
#       模拟同角色跨镜头；AI 合成人脸/接口人像，无第三方肖像权进入仓库）
# ==============================================================
import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MANJU = REPO / "yyc3-ai-manju-studio"
FACES = Path("/tmp/g3_faces")
LIBRARY = MANJU / "backend" / "face_library_g3"

sys.path.insert(0, str(MANJU / "backend"))
from app.modules.consistency_engine.face_encoder import FaceEncoder, FEATURE_DIM  # noqa: E402

RESULTS = []


def record(cid, name, status, checks, deviations=()):
    RESULTS.append({"id": cid, "name": name, "status": status,
                    "checks": checks, "deviations": list(deviations)})


def build_library_inprocess():
    """与 build_face_library.py 同一代码路径：建库 + 维度/确定性校验 + index 落盘"""
    enc = FaceEncoder(library_root=str(LIBRARY))
    source = FACES / "_build_source"
    source.mkdir(exist_ok=True)
    shutil.copy2(FACES / "charA_shot1.png", source / "hero.png")
    shutil.copy2(FACES / "charB_shot1.png", source / "villain.png")
    if LIBRARY.exists():
        shutil.rmtree(LIBRARY)

    manifests = []
    for img in sorted(source.glob("*.png")):
        manifests.append(enc.save_character(
            char_id=img.stem, name=img.stem, image_path=str(img)))

    lines, all_ok = [], True
    for m in manifests:
        vec = enc.load_feature(m["char_id"])
        vec2 = enc.extract_feature(m["source_image"])
        cos = float(vec @ vec2)
        ok = vec.shape == (FEATURE_DIM,) and abs(cos - 1.0) < 1e-5
        all_ok = all_ok and ok
        lines.append(f"{'PASS' if ok else 'FAIL'} {m['char_id']}: "
                     f"dim={vec.shape[0]} cos_sim_same={cos:.6f} mode={m['mode']}")
    (LIBRARY / "index.json").write_text(
        json.dumps(manifests, ensure_ascii=False, indent=2), encoding="utf-8")
    return enc, manifests, lines, all_ok


def main():
    # ── 素材就绪检查 ──
    shots = {f"char{p}_shot{n}": FACES / f"char{p}_shot{n}.png"
             for p in ("A", "B") for n in (1, 2)}
    missing = [k for k, v in shots.items() if not v.exists()]
    if missing:
        print(f"[素材缺失] {missing}；请先执行素材准备步骤")
        return 2

    # ── TC-G3-001 角色特征库建库（512 维，真实模型）──
    enc, manifests, build_lines, all_ok = build_library_inprocess()
    print("[TC-G3-001 建库输出]")
    for line in build_lines:
        print("   ", line)
    modes = {m["char_id"]: m["mode"] for m in manifests}
    dims = {m["char_id"]: m["dim"] for m in manifests}
    c1 = {
        "2 角色入库": len(manifests) == 2,
        "mode=insightface（真实模型）": set(modes.values()) == {"insightface"},
        "dim=512": set(dims.values()) == {FEATURE_DIM},
        "同图二次编码 cos=1.0": all_ok,
        "feature.npy+manifest.json+index.json 三件齐": all(
            (LIBRARY / m["char_id"] / "feature.npy").exists()
            and (LIBRARY / m["char_id"] / "manifest.json").exists()
            for m in manifests),
    }
    record("TC-G3-001", "角色特征库建库（512 维）",
           "PASS" if all(c1.values()) else "FAIL", c1,
           ["建库逻辑与 build_face_library.py 同一 FaceEncoder 代码路径（脚本本体直跑留证见验收记录）",
            "素材为 AI 合成人脸/接口人像的本地变换变体（预研用），生产库落 NAS 待硬件"])
    print("TC-G3-001", json.dumps(c1, ensure_ascii=False), f"modes={modes}")

    # ── TC-G3-002 跨镜头一致性比对（≥0.85 / 区分度 <0.85）──
    feats, per_shot_modes = {}, []
    for k, v in shots.items():
        f = enc.extract_feature(str(v))
        per_shot_modes.append(enc.last_mode)
        feats[k] = f
    lib_hero = enc.load_feature("hero")
    lib_villain = enc.load_feature("villain")

    def cos(a, b):
        return float(a @ b)  # 均已 L2 归一化

    same_pairs = {
        "hero: 库特征 vs 跨镜头shot2": cos(lib_hero, feats["charA_shot2"]),
        "hero: shot1 vs shot2": cos(feats["charA_shot1"], feats["charA_shot2"]),
        "villain: 库特征 vs 跨镜头shot2": cos(lib_villain, feats["charB_shot2"]),
        "villain: shot1 vs shot2": cos(feats["charB_shot1"], feats["charB_shot2"]),
    }
    cross_pairs = {
        "A1×B1": cos(feats["charA_shot1"], feats["charB_shot1"]),
        "A1×B2": cos(feats["charA_shot1"], feats["charB_shot2"]),
        "A2×B1": cos(feats["charA_shot2"], feats["charB_shot1"]),
        "A2×B2": cos(feats["charA_shot2"], feats["charB_shot2"]),
    }
    matrix = {**same_pairs, **cross_pairs}
    print("[TC-G3-002 相似度矩阵]")
    for k, v in matrix.items():
        tag = "同角色" if k in same_pairs else "跨角色"
        print(f"    {tag} {k}: {v:.4f}")

    c2 = {
        "dim=512×4": all(f.shape == (FEATURE_DIM,) for f in feats.values()),
        "4 帧全部真实模型提取（无哈希降级）": per_shot_modes == ["insightface"] * 4,
        "同角色跨镜头全部 ≥0.85": all(v >= 0.85 for v in same_pairs.values()),
        "跨角色全部 <0.85（区分度）": all(v < 0.85 for v in cross_pairs.values()),
    }
    record("TC-G3-002", "跨镜头一致性比对",
           "PASS" if all(c2.values()) else "FAIL", c2,
           [f"逐帧提取模式留证：{per_shot_modes}",
            "shot2 为同源人脸感知裁剪变体（检测框外扩1.8×/亮度1.12/JPEG88），"
            "模拟同角色跨机位；真实多机位素材待 M3 主体阶段补充"])
    print("TC-G3-002", json.dumps(c2, ensure_ascii=False),
          f"same_min={min(same_pairs.values()):.4f} cross_max={max(cross_pairs.values()):.4f}")

    # ── 汇总 ──
    n_pass = sum(1 for r in RESULTS if r["status"] == "PASS")
    n_fail = sum(1 for r in RESULTS if r["status"] == "FAIL")
    print(f"\n=== G3 一致性预研汇总：PASS {n_pass} / FAIL {n_fail}（共 {len(RESULTS)}）===")
    print(json.dumps({"summary": {"pass": n_pass, "fail": n_fail},
                      "library": str(LIBRARY),
                      "matrix": {k: round(v, 4) for k, v in matrix.items()},
                      "results": RESULTS}, ensure_ascii=False, indent=2))
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
