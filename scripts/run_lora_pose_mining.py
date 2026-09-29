# ==============================================================
# run_lora_pose_mining.py — 777 类姿态样本挖掘（M3 三轮 · P1 min 口径冲刺）
# 策略：seed777 全权重域相似度最低（生成姿态偏离训练分布，HANDOFF 32.4）。
#   用现行最优路线（sd-hero-v2 + PLUS FACE w=0.15）以 seed777 × 姿态提示词
#   变体生成候选池，insightface 身份门（sim ≥ 0.75 vs hero_base）筛选后
#   入三轮训练集——教模型「该姿态族下仍保持身份」，防分布外漂移。
# 防漂移放大：仅收高身份相似度样本；caption 沿用基准描述（身份-描述绑定不变）。
# 运行（manju venv，insightface 在位；ComfyUI 走 HTTP 无需本机 torch）：
#   yyc3-ai-manju-studio/.venv/bin/python scripts/run_lora_pose_mining.py \
#     --lora sd-hero-v2.safetensors --weight 0.15
# ==============================================================
import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from run_lora_plusface_combo import (  # noqa: E402  同目录复用工作流与生成协议
    PORTRAIT, build_workflow, comfy_generate)

MANJU = REPO / "yyc3-ai-manju-studio"
sys.path.insert(0, str(MANJU / "backend"))
from app.modules.consistency_engine.face_encoder import FaceEncoder  # noqa: E402 # pyright: ignore[reportMissingImports]

HERO = Path("/tmp/comfy_out/hero_base.png")
OUT_DIR = Path("/tmp/pose_mining")
ACCEPT_DIR = OUT_DIR / "accepted"

# 姿态提示词变体：覆盖 777 漂移姿态族（侧脸/回眸/四分之三/动态/俯仰角/特写）
POSE_VARIANTS = [
    "side profile view, night lantern lighting",
    "looking back over shoulder, different angle",
    "three quarter view, walking forward",
    "drawing sword, dynamic pose",
    "looking up, low angle view",
    "head turned left, profile lighting",
    "smiling, looking away, night scene",
    "closeup face, tilted head, night lantern",
]
SIM_GATE = 0.75  # 身份门：低于此值疑似漂移放大，不入训练集


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lora", default="sd-hero-v2.safetensors")
    ap.add_argument("--weight", type=float, default=0.15)
    ap.add_argument("--seed", type=int, default=777,
                    help="挖掘种子（777 类姿态族本体）")
    args = ap.parse_args()

    enc = FaceEncoder(library_root=str(MANJU / "backend" / "face_library_sd"))
    ref = enc.extract_feature(str(HERO))
    assert enc.last_mode == "insightface", "参考特征必须真实模型提取"

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ACCEPT_DIR.mkdir(parents=True, exist_ok=True)

    rows = []
    for i, pose in enumerate(POSE_VARIANTS):
        wf = build_workflow(PORTRAIT, args.seed, args.lora, args.weight)
        wf["6"]["inputs"]["text"] = f"{PORTRAIT}, {pose}"  # 覆写正向提示词
        wf["9"]["inputs"]["filename_prefix"] = "yyc3/pose_mine"
        out = OUT_DIR / f"mine_{i:02d}_s{args.seed}.png"
        comfy_generate(wf, out)
        f = enc.extract_feature(str(out))
        sim = None if f is None else round(float(ref @ f), 4)
        accepted = sim is not None and sim >= SIM_GATE
        if accepted:
            (ACCEPT_DIR / out.name).write_bytes(out.read_bytes())
        rows.append({"pose": pose, "sim": sim, "accepted": accepted})
        print(f"[pose-mine] {i:02d} sim={sim} accept={accepted} <- {pose}")

    ok = [r for r in rows if r["accepted"]]
    report = {
        "testcase": "M3 三轮 777 类姿态样本挖掘（身份门 sim>=0.75）",
        "lora": args.lora, "weight": args.weight, "seed": args.seed,
        "sim_gate": SIM_GATE, "candidates": len(rows), "accepted": len(ok),
        "rows": rows,
    }
    (OUT_DIR / "pose_mining.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in
                      ("candidates", "accepted", "sim_gate")}, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
