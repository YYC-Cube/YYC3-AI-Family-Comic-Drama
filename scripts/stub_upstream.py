# ==============================================================
# stub_upstream.py — OpenAI 兼容桩上游（G1-002 E2E 用，无真实 LLM 时的链路验证）
# 提供与 vLLM 相同的 /v1/chat/completions 形状 + /health 验活端点
# 运行：yyc3-0379-world/.venv/bin/python scripts/stub_upstream.py
# 端口：25290（25xxx 后端红线段）
# ==============================================================
import os
import time
import uuid

from fastapi import FastAPI, Request

app = FastAPI(title="YYC3 Stub OpenAI-Compatible Upstream")


@app.get("/health")
async def health():
    return {"status": "ok", "stub": True}


@app.post("/v1/chat/completions")
async def chat_completions(req: Request):
    body = await req.json()
    prompt = ""
    for m in reversed(body.get("messages", [])):
        if m.get("role") == "user":
            prompt = m.get("content", "")
            break
    content = f"OK from stub upstream（E2E 链路验证）· 收到 {len(prompt)} 字符"
    return {
        "id": f"chatcmpl-stub-{uuid.uuid4().hex[:12]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": body.get("model", "stub"),
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": content},
            "finish_reason": "stop",
        }],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("STUB_PORT", "25290"))
    print(f"[stub] OpenAI 兼容桩上游：http://127.0.0.1:{port}")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
