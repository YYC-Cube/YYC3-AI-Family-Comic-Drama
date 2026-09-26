# ==============================================================
# run_g2_final.py — G2 双 PARTIAL 清尾（真实 LLM）
#   TC-G2-008 残项：语枢单例契约复验（上轮 45s 预算超时回退 Mock）
#   TC-G2-010：语枢+预见 真实模型并行计时（Step4 并行块口径，≤串行之和×0.8）
# 运行：yyc3-0379-world/.venv/bin/python scripts/run_g2_final.py
# ==============================================================
import json
import os
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutTimeout
from pathlib import Path

os.environ["LLM_BASE_URL"] = "http://localhost:11434/v1"
os.environ["LLM_API_KEY"] = "ollama-local"
os.environ["LLM_MODEL"] = "yyc3-family-coder:14b-q4"
os.environ["LLM_TIMEOUT"] = "90"
os.environ["LLM_MAX_TOKENS"] = "200"

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "yyc3-ai-agent-archive" / "components"))

from prompt_runtime import PromptRuntime  # noqa: E402

RESULTS = {}


def probe(agent, method, args, budget=240):
    def _call():
        return getattr(agent, method)(*args)

    with ThreadPoolExecutor(max_workers=1) as pool:
        try:
            out = pool.submit(_call).result(timeout=budget)
        except FutTimeout:
            return {"ok": False, "kind": "timeout"}
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "kind": f"error:{type(e).__name__}"}
    text = out if isinstance(out, str) else json.dumps(out, ensure_ascii=False)
    is_mock = isinstance(out, str) and "|Mock]" in text[:40]
    return {"ok": not is_mock, "kind": type(out).__name__, "head": text[:100]}


def main():
    rt = PromptRuntime()

    # ── TC-G2-008 残项：语枢真实契约复验 ──
    yushu = rt.build_agent("yushu-wanwu")
    yushu.system_prompt += "\n/no_think"
    r8 = probe(yushu, "analyze", ("分析本季度毛利率下滑的主要原因，给出四段式报告。",))
    RESULTS["TC-G2-008_yushu"] = r8
    print(f"[008-语枢] ok={r8['ok']} kind={r8['kind']} head={r8.get('head', '')[:60]!r}")

    # ── TC-G2-010：真实模型并行计时（Step4 并行块口径）──
    # 口径说明：编排引擎场景F 的并行收益发生在 Step4（语枢 analyze + 预见
    # full_forecast 经 ThreadPoolExecutor 并行），Step5-8 为串行后续与本用例无关；
    # 故计时对象 = 与引擎 Step4 完全同构的并行块 vs 两任务串行之和。
    yushu2 = rt.build_agent("yushu-wanwu")
    yushu2.system_prompt += "\n/no_think"
    yujian = rt.build_agent("yujian-xianzhi")
    yujian.system_prompt += "\n/no_think"
    A = lambda: yushu2.analyze("预测营收走势，给出分析。")  # noqa: E731
    B = lambda: yujian.full_forecast("营收", [120, 135, 150, 168], 3)  # noqa: E731

    t_a = A() and 0  # 预热一次（模型常驻后再计时，消除首载偏差）
    t0 = time.perf_counter(); A(); tA = time.perf_counter() - t0
    t0 = time.perf_counter(); B(); tB = time.perf_counter() - t0
    serial = tA + tB

    pars = []
    for _ in range(3):
        with ThreadPoolExecutor(max_workers=2) as pool:
            t0 = time.perf_counter()
            fa, fb = pool.submit(A), pool.submit(B)
            fa.result(); fb.result()
            pars.append(time.perf_counter() - t0)
    par_med = statistics.median(pars)
    ratio = par_med / serial
    r10 = {
        "串行之和可测": serial > 0,
        "并行中位数可测": par_med > 0,
        "并行中位数 ≤ 串行之和×0.8": ratio <= 0.8,
    }
    RESULTS["TC-G2-010"] = {
        "checks": r10,
        "serial_s": round(serial, 2), "tA": round(tA, 2), "tB": round(tB, 2),
        "parallel_runs_s": [round(p, 2) for p in pars],
        "parallel_median_s": round(par_med, 2), "ratio": round(ratio, 3),
        "scope": "Step4 并行块（与引擎场景F 完全同构）",
    }
    print(f"[010] serial={serial:.1f}s par_med={par_med:.1f}s ratio={ratio:.3f}")

    ok = r8["ok"] and all(r10.values())
    print(json.dumps({"status": "PASS" if ok else "FAIL", "results": RESULTS},
                     ensure_ascii=False, indent=2))
    Path("/tmp/g2_final_results.json").write_text(
        json.dumps({"status": "PASS" if ok else "FAIL", "results": RESULTS},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
