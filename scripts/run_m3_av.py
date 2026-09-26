# ==============================================================
# run_m3_av.py — M3 视听产能：DramaToolGateway 桩→实联调 + TC-G3-008 提示词抽检
# 链路：pre_anchor → text_to_image(ComfyUI HTTP) → anchor_guard.post_check 打回闭环
# 生成后端：内置 Mock ComfyUI（stdlib HTTP，端口 41888）——客户端/HTTP/产物取回/
#       比对闭环为真实代码路径，生成本体为预设人脸图（本机无 SD 模型，诚实留证）
# 运行：yyc3-ai-manju-studio/.venv/bin/python scripts/run_m3_av.py
# ==============================================================
import json
import os
import re
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

REPO = Path(__file__).resolve().parents[1]
MANJU = REPO / "yyc3-ai-manju-studio"
COMPONENTS = REPO / "yyc3-ai-agent-archive" / "components"
SCRIPT_ENGINE = MANJU / "backend" / "app" / "modules" / "script_engine"
FACES = Path("/tmp/g3_faces")
LIBRARY = MANJU / "backend" / "face_library"
PORT = 41888

os.environ["COMFYUI_URL"] = f"http://localhost:{PORT}"

# milvus_retriever 降级桩（pymilvus 在 Py3.14 无 wheel；本链路不触 RAG，同冒烟矩阵模式）
import types  # noqa: E402
_milvus_stub = types.ModuleType("milvus_retriever")


class _StubRetriever:
    def __init__(self, *a, **k):
        pass

    def search(self, *a, **k):
        raise ConnectionError("Milvus 不可达（降级桩）")


_milvus_stub.MilvusRetriever = _StubRetriever
sys.modules["milvus_retriever"] = _milvus_stub

sys.path.insert(0, str(COMPONENTS))
sys.path.insert(0, str(MANJU / "backend"))
sys.path.insert(0, str(SCRIPT_ENGINE))

from drama_stage_adapter import DramaToolGateway  # noqa: E402
from app.modules.consistency_engine.face_encoder import FaceEncoder  # noqa: E402
from app.modules.consistency_engine.anchor_guard import AnchorGuard  # noqa: E402
from splitter import split_chapters                    # noqa: E402
from episode_planner import plan_episodes              # noqa: E402
from extractor import extract_elements                 # noqa: E402
from storyboard_schema import draft_storyboard         # noqa: E402

# ── Mock ComfyUI（生成本体=预设人脸图；fail-first 模拟首帧身份漂移）──
MOCK_STATE = {"fail_first": {"hero": 0, "villain": 0}, "images": {}, "served": []}


def _pick_image(prompt_text: str) -> bytes:
    m = re.search(r"角色 (hero|villain)", prompt_text)
    char = m.group(1) if m else "hero"
    other = "villain" if char == "hero" else "hero"
    first = MOCK_STATE["fail_first"][char] == 0
    MOCK_STATE["fail_first"][char] += 1
    chosen = other if first else char  # 首帧漂移（错人）→ 打回后正确
    path = FACES / f"char{'A' if chosen == 'hero' else 'B'}_shot2.png"
    MOCK_STATE["served"].append(f"{char}→{chosen}")
    return path.read_bytes()


class MockComfyHandler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # 静默
        pass

    def _send(self, code, body, ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/prompt":
            return self._send(404, b"{}")
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        texts = [n["inputs"]["text"] for n in body["prompt"].values()
                 if isinstance(n, dict) and n.get("class_type") == "CLIPTextEncode"]
        pid = f"mock-{int(time.time() * 1000)}"
        MOCK_STATE["images"][f"{pid}.png"] = _pick_image("\n".join(texts))
        time.sleep(0.3)  # 模拟生成延迟
        self._send(200, json.dumps({"prompt_id": pid}).encode())

    def do_GET(self):
        if self.path.startswith("/history/"):
            pid = self.path.split("/history/")[1].split("?")[0]
            entry = {"status": {"completed": True, "status_str": "success"},
                     "outputs": {"9": {"images": [
                         {"filename": f"{pid}.png", "subfolder": "", "type": "output"}]}}}
            return self._send(200, json.dumps({pid: entry}).encode())
        if self.path.startswith("/view"):
            q = parse_qs(urlparse(self.path).query)
            name = q.get("filename", [""])[0]
            img = MOCK_STATE["images"].get(name)
            return (self._send(200, img, "image/png") if img
                    else self._send(404, b"{}"))
        return self._send(404, b"{}")


def start_mock():
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), MockComfyHandler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def rebuild_library():
    enc = FaceEncoder(library_root=str(LIBRARY))
    import shutil
    if LIBRARY.exists():
        shutil.rmtree(LIBRARY)
    mapping = {"hero": FACES / "charA_shot1.png", "villain": FACES / "charB_shot1.png"}
    enc.save_character("hero", "hero", str(mapping["hero"]))
    enc.save_character("villain", "villain", str(mapping["villain"]))


def main():
    results = {}

    # ── A. ComfyUI 接入 + anchor_guard 全链打回闭环 ──
    srv = start_mock()
    rebuild_library()
    guard = AnchorGuard(library_root=str(LIBRARY))
    gw = DramaToolGateway()
    assert gw.comfy.enabled, "ComfyUI 客户端未启用"

    pre = guard.pre_anchor("hero", "月光下的义庄门口，hero 回头凝视")
    full_prompt = pre["anchor_prompt_prefix"] + "\n" + pre["user_prompt"]

    chain = []
    attempts = 1
    for round_no in (1, 2):
        out = gw.text_to_image(full_prompt, ref_assets=["hero"],
                               out_path=f"/tmp/yyc3_t2i_r{round_no}.png")
        assert out["status"] == "ok", f"生成失败：{out}"
        chk = guard.post_check("hero", out["image_path"], attempts=attempts)
        chain.append({"round": round_no, "served": MOCK_STATE["served"][-1],
                      "similarity": chk.get("similarity"), "action": chk["action"]})
        if chk["action"] == "accept":
            break
        attempts += 1

    chain_ok = (len(chain) == 2
                and chain[0]["action"] == "redraw" and chain[0]["similarity"] < 0.5
                and chain[1]["action"] == "accept" and chain[1]["similarity"] >= 0.85)

    # 未配置回落（HA）
    os.environ.pop("COMFYUI_URL", None)
    gw_fresh = DramaToolGateway()
    fallback = gw_fresh.text_to_image("测试")
    os.environ["COMFYUI_URL"] = f"http://localhost:{PORT}"
    srv.shutdown()

    results["chain"] = {
        "checks": {
            "生成前锚定 ok": pre["ok"],
            "HTTP 生成 status=ok（产物落盘）": True,
            "首帧身份漂移 → REDRAW": chain[0]["action"] == "redraw",
            "重绘 → ACCEPT（≥0.85）": chain[-1]["action"] == "accept",
            "两轮闭环收束": chain_ok,
            "未配置回落 stub（永不断流）": fallback["status"] == "stub",
        },
        "evidence": chain,
    }

    # ── B. TC-G3-008 提示词抽检（≥90% 三要素 + hook 可区分）──
    novel = ("第一章 夜雨叩门\n暴雨倾盆的深夜，沈青梧提着灯笼叩响了义庄的大门。"
             "「这么晚来义庄，您找谁？」守夜的老汉眯着眼问。「找一具三日前的尸体。」"
             "她声音很冷。谁也没想到，棺中人是她失踪七日的兄长，脸上盖着官府的封条。"
             "难道义庄里还藏着第三个人？\n第二章 封条之下\n沈青梧甩袖退开三步，"
             "义庄深处传来铁链拖地的声响。「我兄长的死因，就在这张封条下面。」"
             "她指尖的银针已扣在袖中。老汉突然跪倒在地，浑身发抖。"
             "原来义庄的每一具棺材，都少了一样东西——心脏。")
    els = extract_elements(novel)
    sb = draft_storyboard("g3av-001", plan_episodes(split_chapters(novel))[0],
                          els, trace_id="trace-G3AV-000001")
    style_ref = "古风悬疑 水墨厚涂 高对比"
    sample = sb["shots"][:20]
    three = [s for s in sample
             if s["image_prompt"].startswith(style_ref)
             and s["image_prompt"].count("，") >= 2]
    hook_shots = [s for s in sb["shots"] if s["hook_flag"]]
    non_hook = [s for s in sb["shots"] if not s["hook_flag"]][:20]
    ratio = len(three) / len(sample)
    results["tc_g3_008"] = {
        "checks": {
            f"三要素比例 ≥90%（实测 {ratio:.0%}）": ratio >= 0.90,
            "hook 镜头全部含【钩子镜头】标记": all(
                "【钩子镜头】" in s["image_prompt"] for s in hook_shots),
            "抽检非 hook 镜头无标记污染": all(
                "【钩子镜头】" not in s["image_prompt"] for s in non_hook),
            "hook_shots 非空": bool(hook_shots),
        },
        "evidence": {"sampled": len(sample), "three_element": len(three),
                     "hook_count": len(hook_shots),
                     "hook_example": hook_shots[0]["image_prompt"][:60] if hook_shots else ""},
    }

    # ── 汇总 ──
    all_ok = (all(results["chain"]["checks"].values())
              and all(results["tc_g3_008"]["checks"].values()))
    for grp in ("chain", "tc_g3_008"):
        for k, v in results[grp]["checks"].items():
            print(f"  {'PASS' if v else 'FAIL'}  [{grp}] {k}")
    print(json.dumps({"status": "PASS" if all_ok else "FAIL", "results": results},
                     ensure_ascii=False, indent=2))
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
