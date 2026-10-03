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
    def __init__(self, *_args, **_kwargs):
        pass

    def search(self, *_args, **_kwargs):
        raise ConnectionError("stub")


setattr(_m, "MilvusRetriever", _S)  # ModuleType 动态属性：setattr 规避类型检查误报
sys.modules["milvus_retriever"] = _m
for p in (COMPONENTS, MANJU / "backend", SCRIPT_ENGINE):
    sys.path.insert(0, str(p))

from drama_stage_adapter import DramaToolGateway  # type: ignore
from app.modules.consistency_engine.face_encoder import FaceEncoder  # type: ignore
from app.modules.consistency_engine.anchor_guard import AnchorGuard  # type: ignore
from splitter import split_chapters  # type: ignore
from episode_planner import plan_episodes  # type: ignore
from extractor import extract_elements  # type: ignore
from storyboard_schema import draft_storyboard  # type: ignore

# 三章各 ~220 字：章末残留 ≥183 字独立成集（plan_episodes budget=367/2 门槛），
# 两章累计 <367 字不提前合并 → 严格切出 3 集（扩产 ≥3 集样片前提）
NOVEL = ("第一章 夜雨叩门\n"
         "暴雨倾盆的深夜，沈青梧提着灯笼叩响了义庄的大门。木门吱呀半开，守夜的老汉举着油灯，眯眼打量来客。"
         "「这么晚来义庄，您找谁？」她的声音比雨声还冷：「找一具三日前的尸体。」"
         "老汉引她穿过停满棺木的长廊，灯笼的光在墙上摇晃出细长影子。停在最里间的棺前，盖着官府的封条。"
         "「这尸首古怪，姑娘三思。」老汉低声劝。她掀开一角——棺中人竟是她失踪七日的兄长。"
         "雨声轰鸣，她握灯笼的手稳如磐石，心却沉入冰窟。是谁封的棺？兄长又为何暴毙？"
         "这一夜叩门，叩开的是复仇之路的第一道门。\n"
         "第二章 棺中疑云\n"
         "沈青梧撬开官府封条，凑近细看。棺中兄长面色如生，嘴角却凝着一丝黑血，指缝里还嵌着几缕灰线。"
         "「中毒？」守夜老汉举灯近看，忽然浑身发抖——尸斑竟呈诡异青紫色，指尖隐有黑气。"
         "「这不是普通的毒。」老汉声音压得极低，「三日前深夜，有一队黑衣人来过义庄，抬走了一口棺材。」"
         "沈青梧翻检兄长随身之物，玉佩完好，银票不见，唯有一张揉皱的字条，上面画着一道朱砂符。"
         "她攥紧剑柄，指节发白。兄长之死，远比想象更深。字条上的符，她在一本禁书里见过——那是引魂符。\n"
         "第三章 夜半尸行\n"
         "子时刚过，义庄内忽起阴风，烛火齐灭。黑暗里，棺中传出指甲抓挠木板的声响，一下，又一下。"
         "沈青梧提剑守在棺侧，剑穗在风中绷得笔直。棺盖无声滑开，兄长双眼猛然睁开，瞳孔泛着灰白。"
         "「兄长？」她的声音第一次颤抖。尸身坐起，却越过她直扑门外，像被什么牵引着，冲进暴雨深夜。"
         "她提剑追出，雨幕深处，一串黑衣人的灯笼连成一线，正朝城外乱葬岗移动。"
         "尸行在前，人影在后。她咬破指尖在剑身画下破煞符——今夜，要么救回兄长魂魄，要么让引魂者偿命。")

REF_STYLE = "portrait of a young chinese wuxia heroine, ancient hanfu, ink wash background"


def load_style_file(path: str | None) -> dict:
    """加载动态 prompt 定制配置（生产化：按集/按镜覆盖样式提示词）。

    JSON 结构：{"default_style": str?, "episodes": {"1": str},
                "shot_overrides": {"EP01-SHOT-03": str}}
    三级优先：shot_overrides > episodes[集号] > default_style > 内置 REF_STYLE 保底。
    """
    if not path:
        return {}
    p = Path(path)
    if not p.exists():
        print(f"[batch] 警告：--style-file 不存在，回退内置 REF_STYLE：{path}")
        return {}
    cfg = json.loads(p.read_text(encoding="utf-8"))
    print(f"[batch] 动态 prompt 定制已加载：{path}（episodes={len(cfg.get('episodes', {}))} "
          f"shot_overrides={len(cfg.get('shot_overrides', {}))}）")
    return cfg


def resolve_style(cfg: dict, episode: int, shot_id: str) -> tuple[str, str]:
    """返回（生效 prompt，来源标记）——来源留证入 manifest。"""
    if shot_id in cfg.get("shot_overrides", {}):
        return cfg["shot_overrides"][shot_id], "shot_override"
    if str(episode) in cfg.get("episodes", {}):
        return cfg["episodes"][str(episode)], "episode"
    if cfg.get("default_style"):
        return cfg["default_style"], "default"
    return REF_STYLE, "builtin"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default="demo-001")
    ap.add_argument("--char", default="sd-hero")
    ap.add_argument("--ref-image", default="hero_base.png",
                    help="IPAdapter 参考图（ComfyUI/input/ 内文件名）")
    ap.add_argument("--limit", type=int, default=2, help="本次批量镜头数")
    ap.add_argument("--episode", type=int, default=1,
                    help="集号（1 起，取分集计划第 N 集；扩产 ≥3 集用）")
    ap.add_argument("--root", default=os.getenv("PROJECT_ROOT", "/tmp/yyc3_projects"))
    ap.add_argument("--style-file", default=os.getenv("STYLE_FILE", ""),
                    help="动态 prompt 定制 JSON（按集/按镜覆盖样式，缺省复用内置 REF_STYLE）")
    ap.add_argument("--lora", default=os.getenv("CHAR_LORA", ""),
                    help="combo 生产配置：LoRA 文件名（ComfyUI/models/loras/ 内；"
                         "缺省空=纯 IPAdapter 旧口径）")
    ap.add_argument("--ipa-weight", type=float,
                    default=float(os.getenv("IPA_WEIGHT", "0.15")),
                    help="IPAdapter 权重（M3 二轮 combo 实证：LoRA 组合时 0.15 最优，"
                         "历史默认 0.85 为负交互区）")
    args = ap.parse_args()
    style_cfg = load_style_file(args.style_file)

    proj = Path(args.root) / args.project
    for sub in ("storyboard", "images", "audio", "state", "output"):
        (proj / sub).mkdir(parents=True, exist_ok=True)

    gw = DramaToolGateway()
    enc = FaceEncoder(library_root=str(LIBRARY))
    if not (LIBRARY / args.char / "feature.npy").exists():
        shutil.rmtree(LIBRARY, ignore_errors=True)
        # 参考图锚定历史设定图本体（2026-10-02 参考系漂移治理：
        # /tmp 纯生成图禁作跨日参考系；CHAR_BASE_IMAGE 仍可显式覆盖）
        src = os.environ.get(
            "CHAR_BASE_IMAGE",
            "/Users/yanyu/YYC-Cube/tools/ComfyUI/input/hero_base.png")
        enc.save_character(args.char, args.char, src)
    guard = AnchorGuard(library_root=str(LIBRARY))

    # 1) 分镜（--episode 取对应集；分集计划按章节流 105s 预算切分）
    els = extract_elements(NOVEL)
    eps = plan_episodes(split_chapters(NOVEL))
    ep_idx = args.episode - 1
    if ep_idx < 0 or ep_idx >= len(eps):
        print(f"[batch] 错误：--episode {args.episode} 超界（分集计划共 {len(eps)} 集）")
        return 1
    ep = eps[ep_idx]
    trace_id = f"trace-BATCH-EP{args.episode:02d}"
    sb = draft_storyboard(args.project, ep, els, trace_id=trace_id)
    (proj / "storyboard" / "storyboard.v1.json").write_text(
        json.dumps(sb, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[batch] {args.project} ep{args.episode}: 章节={ep.get('title', '-')} "
          f"镜头池={len(sb['shots'])} trace={trace_id}")

    manifest = {"project": args.project, "char": args.char,
                "comfy": gw.comfy.enabled, "tts": gw.tts_client.enabled,
                "style_file": args.style_file or None,
                "anchor_config": {"lora": args.lora or None,
                                  "ipa_weight": args.ipa_weight,
                                  "strategy": "combo+seed_lock" if args.lora
                                  else "ipadapter+seed_lock"},
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
        style, style_src = resolve_style(style_cfg, args.episode, sid)
        row["style_source"] = style_src  # 动态 prompt 定制留证（builtin=三集复用旧口径）
        gen = gw.text_to_image(f"{style}, {shot['description']}",
                               ref_assets=[args.char], out_path=str(out),
                               seed=seed, ref_image=args.ref_image,
                               lora=args.lora or None,
                               ipa_weight=args.ipa_weight)
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
                gen = gw.text_to_image(f"{style}, {shot['description']}",
                                       ref_assets=[args.char], out_path=str(out),
                                       seed=base_seed, ref_image=args.ref_image,
                                       lora=args.lora or None,
                                       ipa_weight=args.ipa_weight)
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
