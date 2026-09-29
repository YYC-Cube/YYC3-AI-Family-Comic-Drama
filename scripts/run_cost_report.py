# ==============================================================
# run_cost_report.py — G4 单集成本核算执行器（TC-G4-007）
# 口径：全本地链（ComfyUI 本地生成 / piper 本地 TTS / H3 DGX 本地推理 /
#       SyncNet 本地评分）→ 外部 API 成本 0 元；算力耗时如实分阶段计量。
# 核算单字段：分阶段耗时（脚本分镜/图像/TTS/合成/动态生成/串联/评分）+
#   外部成本 + 本地算力秒 + 达标判定（≤2 元/集）。
# v1.1.0 生产化：Token-Console 真实计量接入成本链——网关可达时拉取
#   /v1/models/stats（用量）+ /v1/models（价表）折算 Token 成本（USD→CNY）
#   均摊入各集；网关不可达如实标注 unreachable（不虚构 0，沿用全本地口径）。
# 用法：
#   .venv/bin/python scripts/run_cost_report.py \
#     --projects g4-ep01,g4-ep02,g4-ep03 \
#     --dynamic-seconds '{"g4-ep01":1109.1,"g4-ep02":780.0,"g4-ep03":780.0}' \
#     --gateway-url http://localhost:8000 \
#     --electricity-rate 0.6 --gpu-power-w 140 --out /tmp/g4_cost_report.json
# 密钥：GATEWAY_API_KEY 环境变量（不入库）。
# ==============================================================
import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

# 单集综合成本红线（YYC3-60 TC-G4-007）
BUDGET_CNY = 2.0


def fetch_gateway_metering(gateway_url: str, api_key: str,
                           usd_cny: float) -> dict:
    """拉取网关真实计量（Token-Console 数据源）并折算 Token 成本。

    数据面：GET /v1/models/stats（各模型 usage_count/total_tokens）
          + GET /v1/models（cost_per_1k_tokens 价表）。
    网关不可达/未配置时返回 reachable=false——成本链如实降级，不虚构数字。
    """
    if not gateway_url:
        return {"reachable": False, "source": "未配置 --gateway-url（沿用全本地链口径）",
                "token_cost_cny": None, "models": []}
    try:
        headers = {"X-API-Key": api_key} if api_key else {}
        req = urllib.request.Request(f"{gateway_url.rstrip('/')}/v1/models",
                                     headers=headers)
        # 超时 8s：PG 不可达时网关端点实测 ~4s（DB 重试拖慢），3s 会误判不可达
        with urllib.request.urlopen(req, timeout=8) as r:
            prices = {m["id"]: float(m.get("cost_per_1k_tokens") or 0)
                      for m in json.loads(r.read().decode())}
        req = urllib.request.Request(f"{gateway_url.rstrip('/')}/v1/models/stats",
                                     headers=headers)
        with urllib.request.urlopen(req, timeout=8) as r:
            stats = json.loads(r.read().decode())
        rows, cost_usd = [], 0.0
        for s in stats:
            tokens = int(s.get("total_tokens") or 0)
            price = prices.get(s.get("model_id"), 0.0)
            c = tokens * price / 1000.0
            cost_usd += c
            if tokens:
                rows.append({"model": s.get("model_id"), "total_tokens": tokens,
                             "cost_usd": round(c, 6)})
        return {"reachable": True,
                "source": "Token-Console 计量链（网关 /v1/models/stats + /v1/models 价表）",
                "usd_cny": usd_cny,
                "token_cost_usd": round(cost_usd, 6),
                "token_cost_cny": round(cost_usd * usd_cny, 4),
                "models": rows}
    except Exception as e:
        return {"reachable": False, "source": f"网关不可达（{e.__class__.__name__}），沿用全本地链口径",
                "token_cost_cny": None, "models": []}


def episode_cost(proj_dir: Path, dynamic_seconds: float,
                 rate: float, power_w: float,
                 compose_seconds: float, score_seconds: float,
                 token_share: float = 0.0) -> dict:
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
        "external_api_cost_cny": round(token_share, 4),
        "external_api_note": "Token-Console 计量均摊" if token_share else "全本地链零外部 API",
        "local_compute": {"mac_seconds": round(mac_seconds, 1),
                          "dgx_seconds": round(dgx_seconds, 1),
                          "kwh": round(kwh, 5),
                          "electricity_cny": elec},
        "total_cost_cny": round(token_share + elec, 4),
        "budget_cny": BUDGET_CNY,
        "passed": (token_share + elec) <= BUDGET_CNY,
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
    ap.add_argument("--gateway-url", default=os.environ.get("GATEWAY_URL", ""),
                    help="网关地址（Token-Console 计量接入成本链，空=沿用全本地口径）")
    ap.add_argument("--gateway-key", default=os.environ.get("GATEWAY_API_KEY", ""),
                    help="网关 X-API-Key（缺省读 GATEWAY_API_KEY 环境变量，不入库）")
    ap.add_argument("--usd-cny", type=float, default=7.2, help="USD→CNY 汇率")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    dyn = json.loads(args.dynamic_seconds)
    metering = fetch_gateway_metering(args.gateway_url, args.gateway_key, args.usd_cny)
    projs = [p.strip() for p in args.projects.split(",") if p.strip()]
    # Token 成本按集均摊（网关计量为全链公共段，无逐集 trace 时如实均摊口径）
    token_share = (metering["token_cost_cny"] / len(projs)
                   if metering.get("token_cost_cny") else 0.0)
    rows = [episode_cost(Path(args.root) / p, dyn.get(p, 0.0),
                         args.electricity_rate, args.gpu_power_w,
                         args.compose_seconds, args.score_seconds, token_share)
            for p in projs]

    report = {"testcase": "TC-G4-007 单集成本核算",
              "executor": "run_cost_report.py",
              "口径说明": "全本地链零外部 API 成本；电费按实测功率折算（Mac 55W/DGX 传入功率）；"
                         "网关可达时 Token-Console 真实计量均摊入各集",
              "gateway_metering": metering,
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
