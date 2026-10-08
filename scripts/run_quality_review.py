# ==============================================================
# run_quality_review.py — G4 内容质检评审 + 交付物规范校验执行器
# 覆盖：TC-G4-005（五维自动评审，≥80 红线，对齐格物宗师 validate 契约）
#       TC-G4-008（交付物规范：命名/元数据/落位）
#       YYC3-74 G1/G2（2026-10-08 视频层门禁：九 gates + 聚合仲裁）
# 说明：格物宗师 LLM validate 依赖 vLLM 后端；本执行器为其规则化降级
#       实现（架构文档 4.1 降级策略合法路径），五维各 20 分确定性打分。
#       五维分数自 YYC3-74 起为「参考分」：终判 PASS 须同时满足
#       分数红线 + 全部 critical/major gates 通过（warn 仅留证不阻断）。
# 门禁层（rule_version: yyc374_gates_20261008，依据 YYC3-74 §五/§六）：
#   critical  gate_arbitration     manifest.gate_critique=revise/reject 强制 BLOCKED
#   critical  gate_freeze          freezedetect 冻结总时长 ≤1.5s
#   critical  gate_segment_identity 段级抽帧 vs 已验收关键帧 SSIM ≥0.75
#   critical  gate_plan_integrity  storyboard 占位复制/钩子占位拦截
#   major     gate_keyframe_diversity 关键帧两两 SSIM ≤0.85（镜间多样性）
#   major     gate_video_bitrate   视频流 ≥2.5 Mbps
#   major     gate_silence         silencedetect(-40dB/0.3s) 成片 0 段（BGM 垫底）
#   major     gate_cfr             avg_frame_rate == r_frame_rate
#   warn      gate_completeness    planned vs produced 完成度对账（G3 验收口径：告警）
# 用法：
#   自动评审：.venv/bin/python scripts/run_quality_review.py \
#     --projects g4-ep01,g4-ep02,g4-ep03 --dynamic-conf '{"g4-ep01":6.413}'
#   人工抽检回填：--human-check g4-ep02 --human-agree 3 --human-total 3
# ==============================================================
import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

# 集中配置（P2 专项 2026-10-05 迁移）：生产根单一出口 scripts/env.py
sys.path.insert(0, str(Path(__file__).resolve().parent))
from env import PROJECT_ROOT  # noqa: E402

RED_LINE = 80.0
GATE_VERSION = "yyc374_gates_20261008"

# 门禁阈值（YYC3-74 §六；调整须走决议修订）
FREEZE_MAX_S = 1.5          # critical：成片冻结总时长上限
SEG_SSIM_MIN = 0.75         # critical：段级帧 vs 关键帧一致性下限
DIVERSITY_SSIM_MAX = 0.85   # major：关键帧两两 SSIM 上限（镜间多样性）
VIDEO_BITRATE_MIN = 2_500_000   # major：1080p 视频流码率下限
SILENCE_MAX_SEGMENTS = 0    # major：-40dB/0.3s 静音段上限（BGM 垫底后）
CFR_TOLERANCE_FPS = 0.05    # major：avg vs r_frame_rate 容差
COMPLETENESS_MIN = 1.0      # warn：produced/planned 完成度下限


def ffprobe(path: str) -> dict:
    """取视频轨规格（codec,width,height,r_frame_rate）与格式时长。"""
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=codec_name,width,height,r_frame_rate",
             "-show_entries", "format=duration",
             "-of", "json", path],
            capture_output=True, text=True, timeout=30)
        j = json.loads(r.stdout)
        st = (j.get("streams") or [{}])[0]
        return {"codec": st.get("codec_name"), "width": st.get("width"),
                "height": st.get("height"), "fps": st.get("r_frame_rate"),
                "duration": float(j.get("format", {}).get("duration", 0) or 0)}
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)}


def probe_video_stream(path: str) -> dict:
    """视频流完整元数据（G2 帧率口径/码率门禁数据源）。"""
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries",
             "stream=codec_name,width,height,r_frame_rate,avg_frame_rate,"
             "nb_frames,bit_rate,duration",
             "-of", "json", path],
            capture_output=True, text=True, timeout=30)
        st = (json.loads(r.stdout).get("streams") or [{}])[0]
        return {"r_fps": _parse_fps(st.get("r_frame_rate")),
                "avg_fps": _parse_fps(st.get("avg_frame_rate")),
                "bit_rate": int(st["bit_rate"]) if str(st.get("bit_rate", "")).isdigit() else None,
                "nb_frames": int(st["nb_frames"]) if str(st.get("nb_frames", "")).isdigit() else None,
                "raw": st}
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)}


def _parse_fps(v) -> "float | None":
    """解析 ffprobe 帧率（'30/1'、'5925/199'）为 float。"""
    if not v or "/" not in str(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return None
    num, den = str(v).split("/", 1)
    try:
        d = float(den)
        return float(num) / d if d else None
    except (TypeError, ValueError):
        return None


def audio_codec(path: str) -> str:
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "a:0",
             "-show_entries", "stream=codec_name", "-of", "csv=p=0", path],
            capture_output=True, text=True, timeout=30)
        return r.stdout.strip()
    except Exception:  # noqa: BLE001
        return ""


def audio_bitrate(path: str) -> "int | None":
    """音频流实际码率 bps（A2 码率校验数据源，YYC3-72 M1 决议）。"""
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "a:0",
             "-show_entries", "stream=bit_rate", "-of", "csv=p=0", path],
            capture_output=True, text=True, timeout=30)
        return int(r.stdout.strip()) if r.stdout.strip().isdigit() else None
    except Exception:  # noqa: BLE001
        return None


def ffmpeg_filter_scan(path: str, filt: str, patterns: dict,
                       media: str = "video") -> list:
    """通用 ffmpeg filter stderr 扫描（freezedetect/silencedetect 等）。

    media: "video"→-vf 滤镜+丢弃音频；"audio"→-af 滤镜+丢弃视频。
    patterns: {"freeze_start": float} 键→数值类型；按 stderr 出现顺序
    聚合成事件列表（键值成组）。
    """
    flag = "-vf" if media == "video" else "-af"
    drop = "-an" if media == "video" else "-vn"
    cmd = ["ffmpeg", "-hide_banner", "-i", path, flag, filt, drop,
           "-f", "null", "-"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        events, cur = [], {}
        for line in r.stderr.splitlines():
            for key, typ in patterns.items():
                m = re.search(rf"{re.escape(key)}:\s*(-?[\d.]+)", line)
                if m:
                    cur[key] = float(m.group(1)) if typ is float else m.group(1)
                    if len(cur) == len(patterns):
                        events.append(cur)
                        cur = {}
        return events
    except Exception:  # noqa: BLE001
        return []


def freeze_scan(path: str) -> dict:
    """freezedetect n=-60dB:d=1（G2 冻结门禁；006 实证 0-10.23s 双冻结段）。"""
    ev = ffmpeg_filter_scan(path, "freezedetect=n=-60dB:d=1",
                            {"freeze_start": float, "freeze_duration": float})
    total = round(sum(e.get("freeze_duration", 0) for e in ev), 3)
    return {"segments": ev, "freeze_total_s": total,
            "threshold_s": FREEZE_MAX_S}


def silence_scan(path: str) -> dict:
    """silencedetect n=-40dB:d=0.3（G2 静音空洞门禁；006 实证三段 1.27s）。"""
    ev = ffmpeg_filter_scan(path, "silencedetect=n=-40dB:d=0.3",
                            {"silence_start": float, "silence_end": float},
                            media="audio")
    out = []
    for e in ev:
        s, e2 = e.get("silence_start"), e.get("silence_end")
        out.append({"start": s, "end": e2,
                    "duration": round(e2 - s, 3) if s is not None and e2 is not None else None})
    return {"segments": out, "count": len(out),
            "total_s": round(sum(x["duration"] or 0 for x in out), 3),
            "threshold": "n=-40dB:d=0.3"}


def _ssim_png(a: Path, b: Path) -> "float | None":
    """两 PNG 的 SSIM（All 通道均值；同尺寸原分辨率直比）。

    口径对齐 YYC3-74 复核证据（1024 原生 0.718-0.744）；缩放会漂移
    数值（512² 下同对降至 0.67），故不做归一缩放——尺寸不配对时返回
    None 由调用方按 0 处理。
    """
    try:
        r = subprocess.run(
            ["ffmpeg", "-hide_banner", "-i", str(a), "-i", str(b),
             "-lavfi", "[0][1]ssim", "-f", "null", "-"],
            capture_output=True, text=True, timeout=60)
        m = re.search(r"SSIM.*All:([\d.]+)", r.stderr)
        return float(m.group(1)) if m else None
    except Exception:  # noqa: BLE001
        return None


def _extract_frame(video: str, t: float, out_png: Path, wh: str) -> bool:
    try:
        r = subprocess.run(
            ["ffmpeg", "-hide_banner", "-y", "-ss", f"{t:.3f}", "-i", video,
             "-frames:v", "1", "-vf", f"scale={wh}", str(out_png)],
            capture_output=True, timeout=30)
        return r.returncode == 0 and out_png.exists()
    except Exception:  # noqa: BLE001
        return False


def _keyframe_crops(images: list, tmp: Path, vw: int, vh: int) -> list:
    """关键帧中心裁切到成片画幅映射（compose 链 increase+crop 的逆映射）。

    1024² 方图 → 16:9 成片：scale=1920x1920 后裁中 1920x1080，等价于
    源图竖向保留 1024*(1080/1920)=576px 居中（y=224）——与 006 实测
    SSIM 0.98 的裁切映射一致（YYC3-74 复核）。
    """
    crop_h = max(2, round(1024 * vh / vw)) if vw and vh else 1024
    y = max(0, (1024 - crop_h) // 2)
    crops = []
    for i, img in enumerate(images):
        out = tmp / f"kf_{i:02d}.png"
        try:
            r = subprocess.run(
                ["ffmpeg", "-hide_banner", "-y", "-i", str(img),
                 "-vf", f"crop=1024:{crop_h}:0:{y}", str(out)],
                capture_output=True, timeout=30)
            if r.returncode == 0 and out.exists():
                crops.append(out)
        except Exception:  # noqa: BLE001
            pass
    return crops


def segment_identity(video: str, duration: float, kf_crops: list,
                     segments: "list | None", tmp: Path, vw: int, vh: int) -> dict:
    """段级一致性（critical）：抽帧 vs 已验收关键帧 SSIM ≥0.75。

    segments.json（state/segments.json，run_episode_build 落盘）存在时按镜
    分段 5%/50%/95% 三点采样；缺省（存量资产）按全片均匀 ≤12 点采样。
    每采样点取「最佳匹配关键帧」的 SSIM，全片最小值 ≥0.75 为过。
    """
    if not kf_crops:
        return {"passed": None, "note": "无关键帧可比对（images/ 为空）"}
    wh = f"1024:{max(2, round(1024 * vh / vw)) if vw and vh else 576}"
    # 采样点：优先 segments.json（镜级精确边界），否则均匀抽点
    points = []
    if segments:
        t0 = 0.0
        for seg in segments:
            d = float(seg.get("duration") or 0)
            for f in (0.05, 0.5, 0.95):
                points.append({"t": round(t0 + d * f, 3), "seg": seg.get("shot_id")})
            t0 += d
    else:
        n = max(6, min(12, int(duration / 1.2) or 6))
        points = [{"t": round(duration * (i + 0.5) / n, 3), "seg": None}
                  for i in range(n)]
    worst = {"ssim": 2.0, "t": None}
    checked = 0
    for p in points:
        fr = tmp / f"f_{p['t']:.2f}.png"
        if not _extract_frame(video, p["t"], fr, wh):
            continue
        best = max((s or 0.0) for s in
                   (_ssim_png(fr, kf) for kf in kf_crops))
        checked += 1
        if best < worst["ssim"]:
            worst = {"ssim": round(best, 4), "t": p["t"], "seg": p["seg"]}
        fr.unlink(missing_ok=True)
    return {"passed": bool(checked) and worst["ssim"] >= SEG_SSIM_MIN,
            "min_best_ssim": worst["ssim"] if checked else None,
            "worst_at": worst["t"], "worst_segment": worst.get("seg"),
            "samples": checked, "threshold": SEG_SSIM_MIN,
            "mode": "segments" if segments else "uniform"}


def keyframe_diversity(images: list, tmp: Path) -> dict:
    """镜间多样性（major）：关键帧两两 SSIM ≤0.85（006 实证 0.72 同质区间）。"""
    pairs, worst = [], 2.0
    for i in range(len(images)):
        for j in range(i + 1, len(images)):
            s = _ssim_png(images[i], images[j])
            if s is None:
                continue
            pairs.append({"a": images[i].name, "b": images[j].name,
                          "ssim": round(s, 4)})
            worst = min(worst, s)
    return {"passed": worst <= DIVERSITY_SSIM_MAX,
            "max_pair_ssim": round(worst, 4) if pairs else None,
            "pairs": pairs, "threshold": DIVERSITY_SSIM_MAX,
            "note": "阈值拦截近复制类同质（占位同图 ≥0.9）；构图塌缩"
                    "（0.7 级微变体）由 G4 出图侧景别验收承担（YYC3-74 §六注）"}


def frame_brightness(path: str, t: float) -> int:
    """单帧平均亮度（0-255）——scale=1:1 缩成单像素取 Y（纯 ffmpeg 零依赖）。"""
    try:
        r = subprocess.run(
            ["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", path,
             "-frames:v", "1", "-vf", "scale=1:1", "-pix_fmt", "gray",
             "-f", "rawvideo", "-"],
            capture_output=True, timeout=30)
        return r.stdout[0] if r.stdout else -1
    except Exception:  # noqa: BLE001
        return -1


def black_frames_5pt(path: str, duration: float) -> dict:
    """5 位等距抽帧黑场扫（YYC3-68 §8.4 P0 · Phase A1 诊断字段，不计分）。"""
    pts = [duration * f for f in (0.1, 0.3, 0.5, 0.7, 0.9)]
    vals = [frame_brightness(path, t) for t in pts]
    # 阈值 ≤25/255 视为黑帧——严格对齐 blackdetect pix_th=0.10（25.5）；
    # 六集实测暗调画风亮度带 28-36（夜戏场景），松阈值会把暗场误标为黑帧
    cut = 25
    return {"points": [round(p, 2) for p in pts], "brightness": vals,
            "black_count": sum(1 for v in vals if 0 <= v <= cut),
            "note": "亮度带 28-36 为本剧暗调画风正常范围（六集实测）"}


def audio_level(path: str) -> dict:
    """volumedetect 音频电平 mean/max dB（Phase A1 诊断字段，不计分）。"""
    try:
        r = subprocess.run(
            ["ffmpeg", "-i", path, "-vn", "-af", "volumedetect",
             "-f", "null", "-"], capture_output=True, text=True, timeout=60)
        mean = re.search(r"mean_volume:\s*(-?[\d.]+)\s*dB", r.stderr)
        peak = re.search(r"max_volume:\s*(-?[\d.]+)\s*dB", r.stderr)
        return {"mean_db": float(mean.group(1)) if mean else None,
                "max_db": float(peak.group(1)) if peak else None}
    except Exception as e:  # noqa: BLE001
        return {"mean_db": None, "max_db": None, "error": str(e)}


# ---------------- storyboard 对账（G3 门禁数据源） ----------------

PLACEHOLDER_MARK = "补拍"


def plan_integrity(sb: dict) -> dict:
    """占位镜治理（critical）：占位复制 / 钩子占位拦截（YYC3-74 G3）。"""
    shots = sb.get("shots") or []
    desc_cnt: dict = {}
    for s in shots:
        desc_cnt[s.get("description", "")] = desc_cnt.get(s.get("description", ""), 0) + 1
    dups = sorted((d, c) for d, c in desc_cnt.items() if c > 1)
    placeholders = [s["shot_id"] for s in shots if PLACEHOLDER_MARK in s.get("description", "")]
    hook_ids = set(sb.get("hook_shots") or [])
    hook_placeholder = [hid for hid in hook_ids
                        if any(hid == s.get("shot_id")
                               and PLACEHOLDER_MARK in s.get("description", "")
                               for s in shots)]
    tail = shots[-1] if shots else {}
    tail_placeholder = PLACEHOLDER_MARK in tail.get("description", "")
    return {
        "passed": not dups and not hook_placeholder and not tail_placeholder,
        "duplicate_descriptions": [{"desc": d[:24], "count": c} for d, c in dups[:3]],
        "duplicate_groups": len(dups),
        "placeholder_shots": len(placeholders),
        "hook_placeholder": hook_placeholder,
        "tail_hook_placeholder": tail_placeholder,
    }


def completeness(sb: dict, manifest: dict) -> dict:
    """完成度对账（warn，G3 验收口径「显式告警」）：produced/planned。"""
    planned = sb.get("total_shots") or len(sb.get("shots") or [])
    produced = [s for s in (manifest.get("shots") or [])
                if s.get("action") == "accept"]
    ratio = round(len(produced) / planned, 4) if planned else None
    return {"passed": bool(ratio and ratio >= COMPLETENESS_MIN),
            "planned": planned, "produced": len(produced),
            "ratio": ratio, "threshold": COMPLETENESS_MIN}


def review_episode(proj_dir: Path, dynamic_conf: "float | None" = None,
                   audio_hq: bool = False) -> dict:
    """单集评审：五维参考分（各 20）+ 九 gates（YYC3-74 视频层门禁）。

    终判：score≥红线 AND critical/major gates 全过（warn 仅留证）。
    audio_hq：A2 高音质分支开关（YYC3-72 M1 决议；对齐 batches.audio_high_quality）。
    """
    name = proj_dir.name
    # 集号解析（2026-10-05 通用化）：取项目名末段数字（g4-ep01→1，
    # sdxl-prod-001→1）；无数字回退整名去非数字（保持旧口径行为）
    tail = "".join(ch for ch in name.split("-")[-1] if ch.isdigit())
    ep_no = tail or "".join(ch for ch in name if ch.isdigit())
    full = proj_dir / "output" / f"{name}_full.mp4"
    if not full.exists():  # 兼容旧命名产物 g4_epNN_full.mp4
        full = proj_dir / "output" / f"g4_ep{ep_no}_full.mp4"
    manifest_p = proj_dir / "state" / "manifest.json"
    sb_p = proj_dir / "storyboard" / "storyboard.v1.json"
    seg_p = proj_dir / "state" / "segments.json"
    d = {"episode": name, "full": str(full), "dims": {}, "gates": {},
         "gate_version": GATE_VERSION}

    # 维度1 规格维（20）：成片 1080p30 h264（12）+ aac 音轨（4）+ 时长>0（4）
    # 画幅三档（2026-10-05 平台适配）：16:9 横 / 9:16 竖 / 1:1 方均认可
    spec = ffprobe(str(full)) if full.exists() else {"error": "成片不存在"}
    s1 = 0
    ok_video = (spec.get("codec") == "h264" and spec.get("fps") == "30/1"
                and (spec.get("width"), spec.get("height"))
                in {(1920, 1080), (1080, 1920), (1080, 1080)})
    s1 += 12 if ok_video else 0
    s1 += 4 if audio_codec(str(full)) == "aac" else 0
    s1 += 4 if float(spec.get("duration") or 0) > 0 else 0
    d["dims"]["规格"] = {"score": s1, "spec": spec, "audio": audio_codec(str(full))}

    # 维度2 时长维（20）：集时长 ≤120s（10）+ ≥3s 下限（10，排除空片）
    dur = float(spec.get("duration") or 0)
    s2 = (10 if 0 < dur <= 120 else 0) + (10 if dur >= 3 else 0)
    d["dims"]["时长"] = {"score": s2, "duration": dur, "window": "3s-120s"}

    # 维度3 元数据维（20）：manifest（5）+ storyboard（5）+ trace_id 带 EP 号（5）
    #   + 各镜 seed 留痕（5）
    m = json.loads(manifest_p.read_text(encoding="utf-8")) if manifest_p.exists() else {}
    sb = json.loads(sb_p.read_text(encoding="utf-8")) if sb_p.exists() else {}
    trace = (sb.get("trace_id") or m.get("trace_id") or "")
    s3 = (5 if m else 0) + (5 if sb else 0) + (5 if f"EP{int(ep_no):02d}" in trace else 0)
    s3 += 5 if all("seed" in s for s in m.get("shots", [])) and m.get("shots") else 0
    d["dims"]["元数据"] = {"score": s3, "trace_id": trace, "shots": len(m.get("shots", []))}

    # 维度4 质量维（20）：动态镜口型 conf（10，有 conf 且 ≥0.75 满分，
    #   有记录未达标得 4）+ 静态镜一致性链留痕（10）
    s4 = 0
    if dynamic_conf is not None:
        s4 += 10 if dynamic_conf >= 0.75 else 4
    sim_records = [s.get("similarity") for s in m.get("shots", [])
                   if s.get("similarity") is not None]
    s4 += 10 if sim_records else 0
    d["dims"]["质量"] = {"score": s4, "dynamic_conf": dynamic_conf,
                        "static_sim": sim_records}

    # 维度5 交付维（20）：{project} 目录规范（10）+ 成片命名规范（10）
    layout_ok = all((proj_dir / sub).exists()
                    for sub in ("storyboard", "images", "audio", "state", "output"))
    s5 = (10 if layout_ok else 0) + (10 if full.exists() else 0)
    d["dims"]["交付"] = {"score": s5, "layout_ok": layout_ok, "full_exists": full.exists()}

    # 诊断节（2026-10-05 Phase A1 · YYC3-68 §8.4 P0）：5 位抽帧黑场扫 + 音频电平
    # ——只采集不扣分；A2 音频码率分层校验（YYC3-72 M1 决议 · 甲方案）
    if full.exists():
        abr = audio_bitrate(str(full))
        hq_cut, base_cut = 184_000, 120_000
        d["diagnostics"] = {
            "black_frames_5pt": black_frames_5pt(str(full), dur),
            "audio_level": audio_level(str(full)),
            "audio_bitrate": {
                "bitrate_bps": abr,
                "rule_version": "m1_final_20261005",
                "branch": "high_quality" if audio_hq else "baseline",
                "threshold_bps": hq_cut if audio_hq else base_cut,
                "passed": (abr is not None and abr >= (hq_cut if audio_hq else base_cut)),
            },
        }

    # ---------------- 视频层门禁（YYC3-74 G1+G2） ----------------
    g = d["gates"]
    if full.exists() and dur > 0:
        vs = probe_video_stream(str(full))
        # G1 门禁聚合仲裁：manifest.gate_critique 非 pass → 强制 BLOCKED
        # （006 实证 revise/57.9 与五维 95 并存以宽松者放行的制度性盲区）
        crit = (m.get("gate_critique") or {})
        crit_verdict = crit.get("verdict")
        g["gate_arbitration"] = {
            "level": "critical",
            "passed": None if crit_verdict is None else crit_verdict == "pass",
            "verdict": crit_verdict,
            "total": crit.get("total"),
            "note": None if crit_verdict is not None
            else "manifest 无 gate_critique（legacy 资产），仲裁跳过留证",
        }
        # G2-a 冻结（critical）
        frz = freeze_scan(str(full))
        g["gate_freeze"] = {
            "level": "critical", **frz,
            "passed": frz["freeze_total_s"] <= FREEZE_MAX_S}
        # G2-b 段级一致性（critical）：抽帧 vs 已验收关键帧
        images = sorted((proj_dir / "images").glob("*.png")) if (proj_dir / "images").exists() else []
        segs = None
        if seg_p.exists():
            try:
                segs = json.loads(seg_p.read_text(encoding="utf-8")).get("segments")
            except Exception:  # noqa: BLE001
                segs = None
        with tempfile.TemporaryDirectory(prefix="yyc3_gate_") as td:
            tmp = Path(td)
            vw, vh = int(spec.get("width") or 1920), int(spec.get("height") or 1080)
            kf_crops = _keyframe_crops(images, tmp, vw, vh)
            g["gate_segment_identity"] = {
                "level": "critical",
                **segment_identity(str(full), dur, kf_crops, segs, tmp, vw, vh)}
            # G2-c 镜间多样性（major）：关键帧两两 SSIM（原图直接比对）
            g["gate_keyframe_diversity"] = {
                "level": "major", **keyframe_diversity(images, tmp)}
        # G2-d 视频码率（major）
        vbr = vs.get("bit_rate")
        g["gate_video_bitrate"] = {
            "level": "major",
            "bitrate_bps": vbr, "threshold_bps": VIDEO_BITRATE_MIN,
            "passed": bool(vbr and vbr >= VIDEO_BITRATE_MIN)}
        # G2-e 静音空洞（major）
        sil = silence_scan(str(full))
        g["gate_silence"] = {
            "level": "major", **sil,
            "passed": sil["count"] <= SILENCE_MAX_SEGMENTS}
        # G2-f 帧率口径 CFR（major；006 实证 avg 29.774 vs r 30 旧 concat 缺陷）
        r_fps, a_fps = vs.get("r_fps"), vs.get("avg_fps")
        g["gate_cfr"] = {
            "level": "major",
            "r_fps": r_fps, "avg_fps": a_fps,
            "tolerance": CFR_TOLERANCE_FPS,
            "passed": bool(r_fps and a_fps
                           and abs(r_fps - a_fps) <= CFR_TOLERANCE_FPS)}
    # G3 对账：占位镜治理（critical）+ 完成度（warn）
    if sb:
        g["gate_plan_integrity"] = {
            "level": "critical", **plan_integrity(sb)}
        g["gate_completeness"] = {
            "level": "warn", **completeness(sb, m)}

    # 终判聚合：五维参考分 + critical/major gates 全过（warn 不阻断，G3 验收口径）
    d["score"] = sum(v["score"] for v in d["dims"].values())
    blocking = [k for k, v in g.items()
                if v.get("level") in ("critical", "major")
                and v.get("passed") is False]
    d["blocking_gates"] = blocking
    d["verdict"] = ("PASS" if d["score"] >= RED_LINE and not blocking
                    else "BLOCKED(" + ",".join(blocking) + ")" if blocking
                    else "FAIL(score)")
    d["passed"] = d["verdict"] == "PASS"
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--projects", default="g4-ep01,g4-ep02,g4-ep03",
                    help="逗号分隔的集目录名")
    ap.add_argument("--root", default=str(PROJECT_ROOT))
    ap.add_argument("--dynamic-conf", default="{}",
                    help='JSON：{集名: 动态镜 SyncNet conf}（如 {"g4-ep01":6.413}）')
    ap.add_argument("--human-check", default=None,
                    help="人工抽检集名（≥10%% 口径：抽检集镜头数即计入）")
    ap.add_argument("--human-agree", type=int, default=0, help="人工与自动结论一致镜头数")
    ap.add_argument("--human-total", type=int, default=0, help="人工抽检镜头总数")
    ap.add_argument("--out", default=None, help="评审结果 JSON 落盘路径")
    ap.add_argument("--audio-hq", action="store_true",
                    help="A2 高音质分支（≥184k，YYC3-72 M1 决议；缺省基线 ≥120k）")
    args = ap.parse_args()

    conf_map = json.loads(args.dynamic_conf)
    results = [review_episode(Path(args.root) / p.strip(), conf_map.get(p.strip()),
                              audio_hq=args.audio_hq)
               for p in args.projects.split(",") if p.strip()]

    report = {"testcase": "TC-G4-005 内容质检评审 + TC-G4-008 交付物规范 + YYC3-74 视频层门禁",
              "executor": "run_quality_review.py（格物宗师 validate 规则化降级实现）",
              "gate_version": GATE_VERSION,
              "red_line": RED_LINE, "episodes": results,
              "avg_score": round(sum(r["score"] for r in results) / len(results), 1),
              "all_passed": all(r["passed"] for r in results)}

    if args.human_check:
        agree, total = args.human_agree, args.human_total
        rate = round(agree / total * 100, 1) if total else 0.0
        report["human_review"] = {"episode": args.human_check, "agree": agree,
                                  "total": total, "consistency_rate": rate,
                                  "threshold": "≥80%", "passed": rate >= 80.0}

    out = json.dumps(report, ensure_ascii=False, indent=2)
    print(out)
    if args.out:
        Path(args.out).write_text(out, encoding="utf-8")
    verdict = (report["all_passed"]
               and report.get("human_review", {}).get("passed", True))
    blocked = [f"{r['episode']}:{','.join(r['blocking_gates'])}"
               for r in results if r["blocking_gates"]]
    print(f"[结论] 均分 {report['avg_score']} / 红线 {RED_LINE} / "
          f"门禁 {GATE_VERSION} / {'PASS' if verdict else 'FAIL'}"
          + (f" / 阻断: {'; '.join(blocked)}" if blocked else ""))
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
