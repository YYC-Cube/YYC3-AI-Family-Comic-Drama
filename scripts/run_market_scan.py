# ==============================================================
# run_market_scan.py — 市场情报前置（63 号 A1 落位，40 轮执行）
# 对标 OnlyShot Phase 0（近 30 天平台热门题材/衰退赛道/反同质化建议）
# 合规红线：数据源仅限「检索快照人工导入」（不爬虫、不自动化抓取平台
#   数据）；本脚本只做 schema 校验与汇总分析，采集动作在人。
# 快照 schema（--snapshots 目录下 *.json 数组或单对象）：
#   {"platform": "红果", "captured_at": "2026-10-05",
#    "items": [{"title": "...", "genre": "战神", "tags": ["逆袭"],
#               "heat": 95.0, "url": "..."}]}
# 汇总输出 market_intel.json：
#   genre_heat（题材热度榜）/ stale_genres（衰退赛道）/ avoid_tags
#   （高频同质化标签）/ differentiation（低频组合差异化建议）
# 用法：
#   python scripts/run_market_scan.py --snapshots docs/market/ \
#     --out docs/market/market_intel.json
# 夜批集成：run_batch_shots --market-file <market_intel.json>（情报留证）
# ==============================================================
import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

REQUIRED_TOP = ("platform", "captured_at", "items")
REQUIRED_ITEM = ("title", "genre", "heat")
MIN_HEAT = 80.0  # 高热题材线
MAX_SAME = 3     # 高频标签同质化线（出现 >= MAX_SAME 部作品的 tag 视为拥挤）


def load_snapshots(root: Path) -> tuple[list[dict], list[str]]:
    """加载并校验快照，返回（合法快照列表, 错误列表）。"""
    snaps: list[dict] = []
    errors: list[str] = []
    for p in sorted(root.glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{p.name}: JSON 解析失败 {exc}")
            continue
        items = data if isinstance(data, list) else [data]
        for i, snap in enumerate(items):
            missing = [k for k in REQUIRED_TOP if k not in snap]
            if missing:
                errors.append(f"{p.name}[{i}]: 缺字段 {missing}")
                continue
            bad = [it for it in snap["items"]
                   if any(k not in it for k in REQUIRED_ITEM)]
            if bad:
                errors.append(f"{p.name}[{i}]: {len(bad)} 条 item 缺 "
                              f"{REQUIRED_ITEM}")
                continue
            snaps.append(snap)
    return snaps, errors


def build_intel(snaps: list[dict]) -> dict:
    """题材热度/衰退赛道/反同质化三表（纯统计，无外部依赖）。"""
    genre_heat: dict[str, list[float]] = defaultdict(list)
    tag_count: Counter = Counter()
    genre_tags: dict[str, Counter] = defaultdict(Counter)
    platforms = set()
    for snap in snaps:
        platforms.add(snap["platform"])
        for it in snap["items"]:
            genre_heat[it["genre"]].append(float(it["heat"]))
            for tag in it.get("tags", []):
                tag_count[tag] += 1
                genre_tags[it["genre"]][tag] += 1

    heat = sorted(((g, round(sum(v) / len(v), 1), len(v))
                   for g, v in genre_heat.items()),
                  key=lambda x: x[1], reverse=True)
    hot = [(g, h, n) for g, h, n in heat if h >= MIN_HEAT]
    stale = [(g, h, n) for g, h, n in heat if h < MIN_HEAT]
    avoid = [t for t, c in tag_count.most_common() if c >= MAX_SAME]
    # 差异化：热门题材 x 拥挤度低的标签组合建议
    differentiation = []
    for g, h, _n in hot[:3]:
        sparse = [t for t, c in genre_tags[g].most_common()
                  if tag_count[t] < MAX_SAME]
        if sparse:
            differentiation.append(f"{g} × {('、'.join(sparse[:3]))}"
                                   f"（题材热度 {h}，标签未拥挤）")
    advice = []
    if stale:
        advice.append("衰退赛道避让：" + "、".join(g for g, _h, _n in stale[:5]))
    if avoid:
        advice.append("同质化标签避让：" + "、".join(avoid[:8]))
    if differentiation:
        advice.append("差异化组合：" + "；".join(differentiation[:3]))
    return {"generated_at": datetime.now().isoformat(timespec="seconds"),
            "sources": sorted(platforms),
            "snapshot_count": len(snaps),
            "genre_heat_all": heat,
            "hot_genres": hot, "stale_genres": stale,
            "avoid_tags": avoid,
            "differentiation": differentiation,
            "advice": advice or ["快照数据不足，暂无可用建议（补充快照）"]}


def validate_intel(path: Path) -> dict:
    """夜批侧校验：market_intel.json 结构合法性（--market-file 前置）。"""
    data = json.loads(path.read_text(encoding="utf-8"))
    missing = [k for k in ("generated_at", "sources", "advice")
               if k not in data]
    return {"ok": not missing, "missing": missing, "advice":
            data.get("advice", [])[:3]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshots", required=True, help="快照目录（*.json）")
    ap.add_argument("--out", default="", help="情报 JSON 落盘路径")
    ap.add_argument("--validate", default="",
                    help="校验既有 market_intel.json（夜批前置用）")
    args = ap.parse_args()

    if args.validate:
        r = validate_intel(Path(args.validate))
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0 if r["ok"] else 1

    snaps, errors = load_snapshots(Path(args.snapshots))
    for e in errors:
        print(f"[market] 快照不合格：{e}", file=sys.stderr)
    if not snaps:
        print("[market] 无合法快照（采集动作在人：检索快照人工导入）",
              file=sys.stderr)
        return 1
    intel = build_intel(snaps)
    print(json.dumps({k: intel[k] for k in
                      ("generated_at", "sources", "snapshot_count",
                       "hot_genres", "stale_genres", "avoid_tags",
                       "differentiation", "advice")},
                     ensure_ascii=False, indent=2))
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(intel, ensure_ascii=False, indent=2),
                       encoding="utf-8")
        print(f"[market] 情报落位：{out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
