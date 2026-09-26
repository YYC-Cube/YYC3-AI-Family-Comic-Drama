# ==============================================================
# run_g2_010_dual.py — TC-G2-010 并发后端实证（双模型双进程）
# 背景：单实例 Ollama 单模型会把并发请求串行化（G2 v1.2 实测 ratio 1.684）；
#       本机语义等价的并发后端 = 两个不同模型各占一个 llama-server 进程
#       （对应 DGX 双节点并发语义）。
# 方法：httpx 直连 Ollama /v1/chat/completions，模型随载荷指定（无 env 竞争）；
#       串行（A 后 B）vs 并行（线程池同发），3 次取中位数，判定 ≤0.8。
# 运行：yyc3-0379-world/.venv/bin/python scripts/run_g2_010_dual.py
# ==============================================================
import json
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx

URL = "http://localhost:11434/v1/chat/completions"
MODEL_A = "yyc3-family-coder:14b-q4"
MODEL_B = "qwen3-coder-30b"
MAX_TOKENS = 96

REQ_A = {"model": MODEL_A, "max_tokens": MAX_TOKENS, "messages": [
    {"role": "user", "content": "用两句话给出毛利率下滑最常见的三个原因。/no_think"}]}
REQ_B = {"model": MODEL_B, "max_tokens": MAX_TOKENS, "messages": [
    {"role": "user", "content": "用两句话给出营收预测的关键步骤。/no_think"}]}


def call(req, client):
    r = client.post(URL, json=req, timeout=420)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def main():
    out = {}
    with httpx.Client() as client:
        # 预热（两模型常驻内存后再计时）
        call(REQ_A, client)
        call(REQ_B, client)

        t0 = time.perf_counter(); a = call(REQ_A, client); ta = time.perf_counter() - t0
        t0 = time.perf_counter(); b = call(REQ_B, client); tb = time.perf_counter() - t0
        serial = ta + tb

        pars = []
        with ThreadPoolExecutor(max_workers=2) as pool:
            for _ in range(3):
                with httpx.Client() as c2:
                    t0 = time.perf_counter()
                    fa = pool.submit(call, REQ_A, c2)
                    fb = pool.submit(call, REQ_B, c2)
                    fa.result(); fb.result()
                    pars.append(time.perf_counter() - t0)
        par_med = statistics.median(pars)
        ratio = par_med / serial

    out = {
        "scope": "双模型双进程并发（yyc3-family-coder:14b + qwen3-coder-30b，"
                 "对应 DGX 双节点并发语义；单模型单实例仍串行）",
        "tA_s": round(ta, 1), "tB_s": round(tb, 1),
        "serial_s": round(serial, 1),
        "parallel_runs_s": [round(p, 1) for p in pars],
        "parallel_median_s": round(par_med, 1),
        "ratio": round(ratio, 3),
        "pass_le_0.8": ratio <= 0.8,
        "sample_A_head": a[:60], "sample_B_head": b[:60],
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    Path("/tmp/g2_010_dual.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if out["pass_le_0.8"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
