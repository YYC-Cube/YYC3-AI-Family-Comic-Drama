# ==============================================================
# run_cost_report.py — G4 单集成本核算执行器（TC-G4-007）
# 口径：全本地链（ComfyUI 本地生成 / piper 本地 TTS / H3 DGX 本地推理 /
#       SyncNet 本地评分）→ 外部 API 成本 0 元；算力耗时如实分阶段计量。
# 核算单字段：分阶段耗时（脚本分镜/图像/TTS/合成/动态生成/串联/评分）+
#   外部成本 + 本地算力秒 + 达标判定（≤2 元/集）。
# 用法：
#   .venv/bin/python scripts/run_cost_report.py \
#     --projects g4-ep01,g4-ep02,g4-ep03 \
#     --dynamic-seconds '{"g4-ep01":1109.1,"g4-ep02":780.0,"g4-ep03":780.0}' \
#     --electricity-rate 0.6 --gpu-power-w 140 --out /tmp/g4_cost_report.json
# ==============================================================
import argparse
import json
import sys
from pathlib import Path

# 单集综合成本红线（YYC3-60 TC-G4-007）
BUDGET_CNY = 2.0


def episode_cost(proj_dir: Path, dynamic_seconds: float,
                 rate: float, power_w: float,
                 compose_seconds: float, score_seconds: float) -> dict:
    """单集核算：manifest 分阶段耗时 + 动态镜头 + 合成串联评分。"""
    name = proj_dir.name
    m = json.loads((proj_dir / "state" / "manifest.json").read_text(encoding="utf-8"))
    shots = m.get("shots", [])
    img_shots = sum(1 for s in shots if s.get("gen_status") == "ok")
    tts_shots = sum(1 for s in shots if s.get("tts") == "ok")

    # 本地算力秒折算电费（Mac M4 Max 整机 ~55W 稳态；DGX GB10 按传入功率）
    mac_seconds = float(m.get("elapsed_s", 0)) + compose_seconds + score_seconds
    dgx_seconds = dynamic_seconds
    kwh = (mac_seconds * 55 + dgx_seconds * power_w) / 3600 / 1000
    elec = round(kwh * rate, 4)

    return {
        "episode": name,
        "stages": {
            "脚本分镜+图像+TTS（manifest.elapsed_s）": round(float(m.get("elapsed_s", 0)), 1),
            "合成+串联+评分（补录）": round(compose_seconds + score_seconds, 1),
            "H3 动态镜头生成（DGX）": round(dynamic_seconds, 1),
        },
        "counts": {"shots": len(shots), "image_ok": img_shots, "tts_ok": tts_shots},
        "external_api_cost_cny": 0.0,
        "local_compute": {"mac_seconds": round(mac_seconds, 1),
                          "dgx_seconds": round(dgx_seconds, 1),
                          "kwh": round(kwh, 5),
                          "electricity_cny": elec},
        "total_cost_cny": round(0.0 + elec, 4),
        "budget_cny": BUDGET_CNY,
        "passed": (0.0 + elec) <= BUDGET_CNY,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--projects", default="g4-ep01,g4-ep02,g4-ep03")
    ap.add_argument("--root", default="/tmp/yyc3_projects")
    ap.add_argument("--dynamic-seconds", default="{}",
                    help='JSON：{集名: H3 动态镜头生成秒}')
    ap.add_argument("--compose-seconds", type=float, default=30.0,
                    help="单集合成+串联耗时补录（ffmpeg 链实测口径）")
    ap.add_argument("--score-seconds", type=float, default=60.0,
                    help="单集 SyncNet 评分耗时补录")
    ap.add_argument("--electricity-rate", type=float, default=0.6, help="电价 元/kWh")
    ap.add_argument("--gpu-power-w", type=float, default=140.0, help="DGX GB10 功率 W")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    dyn = json.loads(args.dynamic_seconds)
    rows = [episode_cost(Path(args.root) / p.strip(), dyn.get(p.strip(), 0.0),
                         args.electricity_rate, args.gpu_power_w,
                         args.compose_seconds, args.score_seconds)
            for p in args.projects.split(",") if p.strip()]

    report = {"testcase": "TC-G4-007 单集成本核算",
              "executor": "run_cost_report.py",
              "口径说明": "全本地链零外部 API 成本；电费按实测功率折算（Mac 55W/DGX 传入功率）",
              "episodes": rows,
              "max_cost": max(r["total_cost_cny"] for r in rows),
              "all_passed": all(r["passed"] for r in rows)}
    out = json.dumps(report, ensure_ascii=False, indent=2)
    print(out)
    if args.out:
        Path(args.out).write_text(out, encoding="utf-8")
    print(f"[结论] 单集最高成本 {report['max_cost']} 元 / 预算 {BUDGET_CNY} 元 / "
          f"{'PASS' if report['all_passed'] else 'FAIL'}")
    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
