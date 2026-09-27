# ==============================================================
# tts_service.py — YYC³ 独立 TTS 服务（M4 配音链 · OpenAI 兼容）
# 后端：piper（纯 Python 调用，无 subprocess；音色 zh_CN-huayan-medium）
# 端点：POST /v1/audio/speech {model, input, voice, response_format:"wav"}
#       GET /healthz
# 运行：yyc3-ai-manju-studio/.venv/bin/python scripts/tts_service.py
# 端口：42118（AI 服务 4xxxx 红线段）
# ==============================================================
import io
import os
import wave
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

VOICE_DIR = Path(os.getenv("PIPER_VOICE_DIR",
                           "/Users/yanyu/YYC-Cube/tools/piper-voices"))
VOICE_ONNX = os.getenv("PIPER_VOICE", "zh_CN-huayan-medium")

app = FastAPI(title="YYC³ TTS Service (piper)")
_voice = None


def get_voice():
    global _voice
    if _voice is None:
        from piper import PiperVoice
        _voice = PiperVoice.load(str(VOICE_DIR / f"{VOICE_ONNX}.onnx"))
    return _voice


class SpeechRequest(BaseModel):
    model: str = "piper-zh"
    input: str
    voice: str = VOICE_ONNX
    response_format: str = "wav"


@app.get("/healthz")
def healthz():
    return {"status": "ok", "backend": "piper", "voice": VOICE_ONNX}


@app.post("/v1/audio/speech")
def speech(req: SpeechRequest):
    if not req.input.strip():
        raise HTTPException(400, "input 为空")
    chunks = get_voice().synthesize(req.input)
    pcm = b"".join(c.audio_int16_bytes for c in chunks)
    if not pcm:
        raise HTTPException(500, "合成失败（空音频）")
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(get_voice().config.sample_rate)
        w.writeframes(pcm)
    return Response(content=buf.getvalue(),
                    media_type="audio/wav",
                    headers={"Content-Disposition": "attachment; filename=speech.wav"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=int(os.getenv("TTS_PORT", "42118")),
                log_level="warning")
