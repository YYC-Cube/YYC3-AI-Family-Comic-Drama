# ==============================================================
# sensitive_scan.py — 分镜/manifest 内容合规预检（63 号 A5 落位）
# 对标 OnlyShot --check-sensitive（sinister→moody 替换表思路，中文短剧域本土化）
# 用法：
#   模块内嵌：from sensitive_scan import scan_text, summarize_hits
#   CLI 扫描：python scripts/sensitive_scan.py --storyboard <storyboard.v1.json>
#   CLI 回写：python scripts/sensitive_scan.py --manifest <manifest.json> --aigc
# 口径：命中仅告警 + 建议替换（不阻断夜批——替换决策留人工，留证入 manifest）
# 合规红线：本表为短剧平台高危词建议替换（克制原则，不做政治类判定，
#   政敏内容依赖平台审核侧；本预检只覆盖创作层可自愈项）
# ==============================================================
import argparse
import json
import sys
from pathlib import Path

# 平台高危词 → 建议替换（创作层可自愈项；语境无损优先）
REPLACE_TABLE: dict[str, str] = {
    # 暴力血腥类（画面提示词高危）
    "杀死": "击败", "杀掉": "除掉", "尸斑": "青痕", "剖开": "翻开",
    "断头": "倒地", "血溅": "影袭", "血迹": "红痕", "暴毙": "离世",
    # 恐怖阴森类（负面情绪过载词）
    "阴森": "幽暗", "诡异": "奇特", "恐怖": "惊险", "邪祟": "暗影",
    # 违禁品类
    "毒药": "药散", "下毒": "下药",
}

AIGC_DECLARATION = {
    "label": "AI 生成内容（AIGC）",
    "declared": True,
    "standard": "短视频平台 AIGC 内容标识规范",
}


def scan_text(text: str, source: str = "") -> list[dict]:
    """扫描单段文本，返回命中列表 [{word, suggest, source}]。

    source 用于留证定位（如 shot-EP01-001/image_prompt）。
    """
    hits: list[dict] = []
    if not text:
        return hits
    for word, suggest in REPLACE_TABLE.items():
        if word in text:
            hits.append({"word": word, "suggest": suggest, "source": source})
    return hits


def scan_storyboard(sb: dict) -> dict:
    """扫描分镜三字段（image_prompt/description/dialogue），返回汇总。"""
    hits: list[dict] = []
    for s in sb.get("shots", []):
        sid = s.get("shot_id", "?")
        for field in ("image_prompt", "description", "dialogue"):
            hits.extend(scan_text(s.get(field) or "", f"{sid}/{field}"))
    return {"scanned": len(sb.get("shots", [])), "hits": hits,
            "clean": not hits}


def apply_declaration(manifest: dict) -> dict:
    """manifest 顶层回写 AIGC 标识字段（平台发布必配，63 号 A5）。"""
    engines = []
    if manifest.get("comfy"):
        engines.append("ComfyUI-SD15")
    if manifest.get("h3") or manifest.get("dynamic"):
        engines.append("H3-Video")
    manifest["aigc"] = {**AIGC_DECLARATION,
                        "engines": engines or ["script-engine"]}
    return manifest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--storyboard", help="storyboard.v1.json 路径（扫描模式）")
    ap.add_argument("--manifest", help="manifest.json 路径（AIGC 回写模式）")
    ap.add_argument("--aigc", action="store_true",
                    help="对 --manifest 回写 AIGC 标识字段")
    ap.add_argument("--out", default="", help="扫描结果 JSON 落盘路径")
    args = ap.parse_args()

    if args.storyboard:
        sb = json.loads(Path(args.storyboard).read_text(encoding="utf-8"))
        report = scan_storyboard(sb)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        for h in report["hits"]:
            print(f"[sensitive] 命中：{h['word']} → 建议「{h['suggest']}」"
                  f"（{h['source']}）")
        if args.out:
            Path(args.out).write_text(
                json.dumps(report, ensure_ascii=False, indent=2),
                encoding="utf-8")
        return 0

    if args.manifest and args.aigc:
        p = Path(args.manifest)
        manifest = json.loads(p.read_text(encoding="utf-8"))
        apply_declaration(manifest)
        p.write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                     encoding="utf-8")
        print(f"[sensitive] AIGC 标识已回写：{p}（engines="
              f"{manifest['aigc']['engines']}）")
        return 0

    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
