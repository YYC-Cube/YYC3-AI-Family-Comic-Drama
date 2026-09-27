# ==============================================================
# run_batch_shots.py — 多镜头批量流水线骨架（M3 · nightly 批量前身）
# 链路（逐镜）：剧本→分镜（script_engine）→ pre_anchor → text_to_image
#   （IPAdapter 锚定 + 镜头稳定种子）→ post_check 打回（≤2）→ 落盘
#   + 对白 TTS（tts_service 在线时）→ manifest + 汇总报告
# 目录：镜像 NAS 规范 projects/{id}/{images,audio,state,output}（本地根
#   /tmp/yyc3_projects，NAS 就绪后改 PROJECT_ROOT=/mnt/nas/projects）
# 降级：ComfyUI/TTS 未配置 → stub 记入 manifest（流水线不断流）
# 运行：COMFYUI_MODEL=DreamShaper_8_pruned.safetensors \
#   yyc3-ai-manju-studio/.venv/bin/python scripts/run_batch_shots.py \
#   --project demo-001 --limit 2 --char sd-hero
# ==============================================================
import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MANJU = REPO / "yyc3-ai-manju-studio"
COMPONENTS = REPO / "yyc3-ai-agent-archive" / "components"
SCRIPT_ENGINE = MANJU / "backend" / "app" / "modules" / "script_engine"
LIBRARY = MANJU / "backend" / "face_library_sd"

os.environ.setdefault("COMFYUI_URL", "http://localhost:41888")
os.environ.setdefault("COMFYUI_MODEL", "DreamShaper_8_pruned.safetensors")
os.environ.setdefault("COMFYUI_TIMEOUT", "900")
os.environ.setdefault("TTS_API_URL", "http://localhost:42118")

import types  # noqa: E402
_m = types.ModuleType("milvus_retriever")


class _S:
    def __init__(self, *a, **k):
        pass

    def search(self, *a, **k):
        raise ConnectionError("stub")


_m.MilvusRetriever = _S
sys.modules["milvus_retriever"] = _m
for p in (COMPONENTS, MANJU / "backend", SCRIPT_ENGINE):
    sys.path.insert(0, str(p))

from drama_stage_adapter import DramaToolGateway  # noqa: E402
from app.modules.consistency_engine.face_encoder import FaceEncoder  # noqa: E402
from app.modules.consistency_engine.anchor_guard import AnchorGuard  # noqa: E402
from splitter import split_chapters                  # noqa: E402
from episode_planner import plan_episodes            # noqa: E402
from extractor import extract_elements               # noqa: E402
from storyboard_schema import draft_storyboard       # noqa: E402

NOVEL = ("第一章 夜雨叩门\n暴雨倾盆的深夜，沈青梧提着灯笼叩响了义庄的大门。"
         "「这么晚来义庄，您找谁？」守夜的老汉眯着眼问。「找一具三日前的尸体。」"
         "她声音很冷。谁也没想到，棺中人是她失踪七日的兄长，脸上盖着官府的封条。"
         "难道义庄里还藏着第三个人？")

REF_STYLE = "portrait of a young chinese wuxia heroine, ancient hanfu, ink wash background"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default="demo-001")
    ap.add_argument("--char", default="sd-hero")
    ap.add_argument("--ref-image", default="hero_base.png",
                    help="IPAdapter 参考图（ComfyUI/input/ 内文件名）")
    ap.add_argument("--limit", type=int, default=2, help="本次批量镜头数")
    ap.add_argument("--root", default=os.getenv("PROJECT_ROOT", "/tmp/yyc3_projects"))
    args = ap.parse_args()

    proj = Path(args.root) / args.project
    for sub in ("storyboard", "images", "audio", "state", "output"):
        (proj / sub).mkdir(parents=True, exist_ok=True)

    gw = DramaToolGateway()
    enc = FaceEncoder(library_root=str(LIBRARY))
    if not (LIBRARY / args.char / "feature.npy").exists():
        shutil.rmtree(LIBRARY, ignore_errors=True)
        src = os.environ.get("CHAR_BASE_IMAGE", f"/tmp/comfy_out/hero_base.png")
        enc.save_character(args.char, args.char, src)
    guard = AnchorGuard(library_root=str(LIBRARY))

    # 1) 分镜
    els = extract_elements(NOVEL)
    eps = plan_episodes(split_chapters(NOVEL))
    sb = draft_storyboard(args.project, eps[0], els, trace_id="trace-BATCH-000001")
    (proj / "storyboard" / "storyboard.v1.json").write_text(
        json.dumps(sb, ensure_ascii=False, indent=2), encoding="utf-8")

    manifest = {"project": args.project, "char": args.char,
                "comfy": gw.comfy.enabled, "tts": gw.tts_client.enabled,
                "shots": []}
    t_start = time.time()
    for shot in sb["shots"][:args.limit]:
        sid = shot["shot_id"]
        seed = int(sid.split("-")[-1]) * 7 + 1000  # 镜头稳定种子（跨批可复现）
        row = {"shot_id": sid, "seed": seed, "dialogue": shot["dialogue"][:30]}

        pre = guard.pre_anchor(args.char, shot["image_prompt"])
        if not pre["ok"]:
            row.update(status="blocked", reason=pre["reason"])
            manifest["shots"].append(row)
            continue

        out = proj / "images" / f"{sid}.png"
        gen = gw.text_to_image(f"{REF_STYLE}, {shot['description']}",
                               ref_assets=[args.char], out_path=str(out),
                               seed=seed, ref_image=args.ref_image)
        row["gen_status"] = gen["status"]
        attempts = 1
        base_seed = int(os.environ.get("CHAR_BASE_SEED", "42"))
        while gen["status"] == "ok" and attempts <= guard.max_attempts:
            chk = guard.post_check(args.char, str(out), attempts=attempts)
            row.update(similarity=chk.get("similarity"), action=chk["action"])
            if chk["action"] == "accept":
                break
            if chk["action"] == "redraw":
                # 生产策略（G3 v1.3/v1.4 实证）：IPAdapter 锚定不足时回退
                # seed-lock（角色基础种子确定性重绘，同参缓存近零成本）
                row["redraw"] = "seed_lock"
                gen = gw.text_to_image(f"{REF_STYLE}, {shot['description']}",
                                       ref_assets=[args.char], out_path=str(out),
                                       seed=base_seed, ref_image=args.ref_image)
                attempts += 1
                continue
            break  # escalate/blocked
        if gen["status"] != "ok":
            row["status"] = gen["status"]  # stub / stub_fallback（降级留证）

        # TTS（有对白且服务在线）
        if shot["dialogue"] and gw.tts_client.enabled:
            wav = proj / "audio" / f"{sid}.wav"
            r = gw.tts(shot["dialogue"], out_path=str(wav))
            row["tts"] = r.get("status")

        manifest["shots"].append(row)
        print(f"[batch] {sid}: gen={row.get('gen_status')} sim={row.get('similarity')} "
              f"action={row.get('action')} tts={row.get('tts', '-')}")

    manifest["elapsed_s"] = round(time.time() - t_start, 1)
    (proj / "state" / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    ok = sum(1 for s in manifest["shots"] if s.get("action") == "accept")
    print(json.dumps({"summary": {"shots": len(manifest["shots"]), "accepted": ok,
                                  "elapsed_s": manifest["elapsed_s"],
                                  "comfy": manifest["comfy"], "tts": manifest["tts"]}},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
