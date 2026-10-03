# ==============================================================
# run_faceid_adapter_smoke.py — FaceID 双档位接线生产冒烟 + G4-006 对照复跑
# 背景（HANDOFF 37 轮用户决策「双档位接线」）：drama_stage_adapter v1.3 默认
#   plus_face 档零变更，新增 faceid 档（FaceID PlusV2 评测冠军配置 w0.15/fv3.0）。
# 本脚本三层验证：
#   ①缺省行为零变更：无环境变量时 client.ipa_profile == "plus_face"
#   ②plus_face 档经 adapter 工作流复现历史基线（mean≈0.8672，验证接线无回归）
#   ③faceid 档经 adapter 工作流复现评测冠军（mean≈0.8248/min≈0.8036）
#   另含 1 张 1024 生产尺寸 faceid 冒烟（生产域参考，信息性）
# 口径：4 漂移种子 × 512 × PORTRAIT+DRIFT_SUFFIX，insightface 余弦 vs 历史设定图
#   本体（HERO 锚定，2026-10-02 参考系漂移治理后口径）。
# 运行：
#   yyc3-ai-manju-studio/.venv/bin/python scripts/run_faceid_adapter_smoke.py \
#     --out docs/attachments/G4-20261002/tc-g4-006-faceid-adapter-ctrl.json
# ==============================================================
import argparse
import json
import os
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MANJU = REPO / "yyc3-ai-manju-studio"
ARCHIVE = REPO / "yyc3-ai-agent-archive" / "components"

# 生产环境变量（adapter 缺省模型 sd_xl 会 400，须锚定 DreamShaper 8）
os.environ.setdefault("COMFYUI_URL", "http://localhost:41888")
os.environ.setdefault("COMFYUI_MODEL", "DreamShaper_8_pruned.safetensors")

sys.path.insert(0, str(MANJU / "backend"))
sys.path.insert(0, str(ARCHIVE))

# milvus_retriever 桩注入（冒烟仅取 ComfyUIClient/DramaToolGateway，不触知识库
# 检索；与仓库既有降级先例 smoke_test_degraded.py 同模式——pymilvus 未装时保
# adapter 可导入，五高-高可用）
import types as _types  # noqa: E402


class _StubMilvusRetriever:  # 冒烟桩：拦截实例化，阻断 pymilvus 依赖链
    def __init__(self, *a, **k):
        raise RuntimeError("冒烟桩：MilvusRetriever 不可用（本冒烟不依赖知识库）")


_stub = _types.ModuleType("milvus_retriever")
_stub.MilvusRetriever = _StubMilvusRetriever  # pyright: ignore[reportAttributeAccessIssue] 动态模块桩（同 smoke_test_degraded.py）
sys.modules.setdefault("milvus_retriever", _stub)

from drama_stage_adapter import ComfyUIClient, DramaToolGateway  # noqa: E402 # pyright: ignore[reportMissingImports]
from app.modules.consistency_engine.face_encoder import FaceEncoder  # noqa: E402 # pyright: ignore[reportMissingImports]

# 评测协议常量（与 run_lora_plusface_combo.py 单一事实源对齐）
PORTRAIT = ("portrait of a young chinese wuxia heroine, delicate face, "
            "ancient hanfu, ink wash background, upper body, highly detailed")
DRIFT_SUFFIX = ", smiling, night lantern lighting, different angle"
SEEDS = [777, 888, 999, 1111]
HERO = Path("/Users/yanyu/YYC-Cube/tools/ComfyUI/input/hero_base.png")
if not HERO.exists():
    HERO = Path("/tmp/comfy_out/hero_base.png")
    print(f"[warn] 历史设定图缺失，回落 /tmp 参考系（有漂移风险）：{HERO}")

# 历史参考系终裁基线（G4-20261002/final_eval_histref.json）
BASELINES = {"v2_combo_w015": {"mean": 0.8672, "min": 0.7846},
             "faceid_combo_w015_fv30": {"mean": 0.8248, "min": 0.8036}}


def run_profile(client: ComfyUIClient, enc: FaceEncoder, ref,
                profile: str, out_dir: Path, width: int = 512,
                reuse: bool = False) -> list:
    """经生产 adapter 客户端跑 4 漂移种子并逐张评分。

    :param reuse: 产物已存在时跳过生成仅重评分（断点续跑：1024 超时后复用 512 产物）
    """
    rows = []
    for s in SEEDS:
        out = out_dir / f"adapter_{profile}_{width}_{s}.png"
        if reuse and out.exists():
            f = enc.extract_feature(str(out))
            sim = None if f is None else round(float(ref @ f), 4)
            rows.append({"seed": s, "sim": sim, "mode": enc.last_mode,
                         "latency_s": None, "bytes": out.stat().st_size,
                         "reused": True})
            print(f"[adapter-{profile}] seed={s} sim={sim}（复用产物重评分）")
            continue
        t0 = time.perf_counter()
        r = client.generate_image(
            PORTRAIT + DRIFT_SUFFIX, str(out), width=width, height=width,
            seed=s, ref_image=HERO.name, lora="sd-hero-v2.safetensors",
            ipa_weight=0.15, ipa_profile=profile,
            **({"ipa_faceidv2": 3.0} if profile == "faceid" else {}))
        dt = round(time.perf_counter() - t0, 1)
        assert r["status"] == "ok", f"{profile} seed={s} 生成失败：{r}"
        f = enc.extract_feature(str(out))
        sim = None if f is None else round(float(ref @ f), 4)
        rows.append({"seed": s, "sim": sim, "mode": enc.last_mode,
                     "latency_s": dt, "bytes": r["bytes"]})
        print(f"[adapter-{profile}] seed={s} sim={sim} [{dt}s]")
    return rows


def stats(rows: list) -> dict:
    sims = [r["sim"] for r in rows if r["sim"] is not None]
    return {"mean": round(sum(sims) / len(sims), 4),
            "min": min(sims), "max": max(sims)} if sims else {}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None, help="留证 JSON 落盘路径")
    ap.add_argument("--reuse-existing", action="store_true",
                    help="产物已存在时跳过生成仅重评分（断点续跑）")
    args = ap.parse_args()
    reuse = args.reuse_existing

    # ①缺省行为零变更断言（无 COMFYUI_IPA_PROFILE 时必须为 plus_face）
    assert "COMFYUI_IPA_PROFILE" not in os.environ, \
        "冒烟须在无档位环境变量下运行（验证缺省行为）"
    default_client = ComfyUIClient()
    assert default_client.ipa_profile == "plus_face", \
        f"缺省档位漂移：{default_client.ipa_profile}"
    print(f"[default] ipa_profile={default_client.ipa_profile}（零变更断言通过）")

    gw = DramaToolGateway()
    assert gw.comfy.enabled, "ComfyUI 未在线（COMFYUI_URL 未配置或不可达）"
    enc = FaceEncoder(library_root="/tmp/faceid_smoke_lib")
    ref = enc.extract_feature(str(HERO))
    assert enc.last_mode == "insightface", "参考特征必须真实模型提取"

    out_dir = Path("/tmp/kohya_out")
    out_dir.mkdir(parents=True, exist_ok=True)

    # ②plus_face 档回归对照（须复现 v2 基线 0.8672/0.7846 附近）
    rows_pf = run_profile(gw.comfy, enc, ref, "plus_face", out_dir, reuse=reuse)
    st_pf = stats(rows_pf)
    print(f"[adapter-plus_face] {st_pf}（基线 {BASELINES['v2_combo_w015']}）")

    # ③faceid 档冠军复现对照（须复现 0.8248/0.8036 附近）
    rows_fid = run_profile(gw.comfy, enc, ref, "faceid", out_dir, reuse=reuse)
    st_fid = stats(rows_fid)
    print(f"[adapter-faceid] {st_fid}（基线 {BASELINES['faceid_combo_w015_fv30']}）")

    # 生产尺寸 faceid 冒烟（1024，信息性，验证生产分辨率全链可用；
    # 1024 像素量 4 倍于 512，耗时预算放宽——首轮 300s 超时教训，
    # 复跑须 COMFYUI_TIMEOUT>=600；超时如实记录不炸整报告）
    out_prod = out_dir / "adapter_faceid_1024_prod.png"
    prod = {"status": "skipped", "sim": None, "latency_s": None}
    if reuse and out_prod.exists():
        f = enc.extract_feature(str(out_prod))
        prod = {"status": "ok(reused)", "sim": round(float(ref @ f), 4),
                "latency_s": None}
    else:
        try:
            t0 = time.perf_counter()
            r = gw.comfy.generate_image(
                PORTRAIT + DRIFT_SUFFIX, str(out_prod), width=1024, height=1024,
                seed=1044, ref_image=HERO.name, lora="sd-hero-v2.safetensors",
                ipa_weight=0.15, ipa_profile="faceid", ipa_faceidv2=3.0)
            dt_prod = round(time.perf_counter() - t0, 1)
            f = enc.extract_feature(str(out_prod))
            prod = {"status": r["status"],
                    "sim": None if f is None else round(float(ref @ f), 4),
                    "latency_s": dt_prod}
        except TimeoutError as e:
            prod = {"status": "timeout", "sim": None, "latency_s": None,
                    "error": str(e)[:120]}
    print(f"[adapter-faceid-1024] {prod}")

    drift_pf = round(abs(st_pf["mean"] - BASELINES["v2_combo_w015"]["mean"]), 4)
    drift_fid = round(abs(st_fid["mean"] - BASELINES["faceid_combo_w015_fv30"]["mean"]), 4)
    report = {
        "testcase": "TC-G4-006 FaceID 双档位接线生产冒烟 + 对照复跑（adapter v1.3）",
        "decision": "双档位接线（用户决策）：默认 plus_face 不变，faceid 为 min 稳定度备选",
        "default_behavior": {"ipa_profile": default_client.ipa_profile,
                             "assert": "无环境变量时缺省 plus_face，零变更通过"},
        "plus_face_regression": {"rows": rows_pf, **st_pf,
                                 "baseline": BASELINES["v2_combo_w015"],
                                 "mean_drift": drift_pf,
                                 "verdict": "PASS" if drift_pf <= 0.02 else "FAIL"},
        "faceid_champion_repro": {"rows": rows_fid, **st_fid,
                                  "baseline": BASELINES["faceid_combo_w015_fv30"],
                                  "mean_drift": drift_fid,
                                  "verdict": "PASS" if drift_fid <= 0.02 else "FAIL"},
        "production_1024_smoke": prod,
        "protocol": "4 漂移种子 x 512 x PORTRAIT+DRIFT_SUFFIX，insightface 余弦 vs "
                    "历史设定图本体（HERO 锚定）",
        "verdict": "PASS" if (drift_pf <= 0.02 and drift_fid <= 0.02
                              and prod["status"].startswith("ok")) else "FAIL",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.out:
        Path(args.out).write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
