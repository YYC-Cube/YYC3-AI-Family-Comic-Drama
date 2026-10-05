# ==============================================================
# run_vertical_transcode.py — 横屏成片 → 竖屏 9:16 转制（投放平台适配）
# 背景（2026-10-05 平台选型会话）：产线成片 1920×1080 横屏，B站原生适配；
#   抖音/TikTok/YouTube Shorts 为竖屏生态——本脚本产出 1080×1920 竖版。
# 模式：blur-pad（背景模糊延展 + 原片等宽居中）——零画面内容损失，
#   优于中心裁切（16:9→9:16 裁切丢两侧约 44% 画面）。
# 产物：{集}/output/{集}_vertical.mp4（原横版保留不动）
# 运行：yyc3-ai-manju-studio/.venv/bin/python scripts/run_vertical_transcode.py \
#   --src ~/YYC-Cube/YYC3-assets/projects --projects sdxl-prod-001,sdxl-prod-002
#   （缺省 --projects 时扫描 src 下全部集）
# ==============================================================
import argparse
import subprocess
import sys
from pathlib import Path

# 集中配置（P2 专项范式）：生产根单一出口 scripts/env.py
sys.path.insert(0, str(Path(__file__).resolve().parent))
from env import PROJECT_ROOT  # noqa: E402

FILTER = ("[0:v]split=2[bg][fg];"
          "[bg]scale=1080:1920:force_original_aspect_ratio=increase,"
          "crop=1080:1920,gblur=sigma=24[bgb];"
          "[fg]scale=1080:-2[fgs];"
          "[bgb][fgs]overlay=(W-w)/2:(H-h)/2")


def transcode(src: Path, dst: Path) -> tuple[bool, str]:
    cmd = ["ffmpeg", "-y", "-i", str(src),
           "-filter_complex", FILTER,
           "-c:v", "libx264", "-preset", "medium", "-crf", "20",
           "-c:a", "copy", str(dst)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    return r.returncode == 0, (r.stderr or "")[-500:]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(Path.home() / "YYC-Cube" / "YYC3-assets" / "projects"),
                    help="成片根（默认本地持久归档区）")
    ap.add_argument("--projects", default="",
                    help="逗号分隔集名（缺省扫描全部含 *_full.mp4 的集）")
    ap.add_argument("--force", action="store_true", help="已存在也重转")
    args = ap.parse_args()

    root = Path(args.src).expanduser()
    names = [p.strip() for p in args.projects.split(",") if p.strip()] \
        or sorted(d.name for d in root.iterdir()
                  if d.is_dir() and any(d.glob("output/*_full.mp4")))
    if not names:
        print(f"[v] 未发现可转制集（{root}）")
        return 1

    ok, skip, fail = 0, 0, 0
    for name in names:
        srcs = list((root / name / "output").glob("*_full.mp4"))
        if not srcs:
            print(f"[v] {name}: 无 *_full.mp4，跳过")
            continue
        src, dst = srcs[0], root / name / "output" / f"{name}_vertical.mp4"
        if dst.exists() and not args.force:
            print(f"[v] {name}: 竖版已在位，跳过（--force 重转）")
            skip += 1
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        done, err = transcode(src, dst)
        if done:
            probe = subprocess.run(
                ["ffprobe", "-v", "error", "-select_streams", "v:0",
                 "-show_entries", "stream=width,height", "-of", "csv=p=0",
                 str(dst)], capture_output=True, text=True)
            print(f"[v] {name}: ✅ {dst.name} {probe.stdout.strip()}")
            ok += 1
        else:
            print(f"[v] {name}: ❌ {err}")
            fail += 1
    print(f"[v] 汇总：成功 {ok} / 跳过 {skip} / 失败 {fail}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
