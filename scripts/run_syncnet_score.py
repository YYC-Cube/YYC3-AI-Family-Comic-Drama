# ==============================================================
# run_syncnet_score.py — SyncNet 口型同步评分包装器（M4 · ③攻坚落地）
# 不改上游 syncnet_python 源码（其 run_syncnet 与本 fork 裁切布局不匹配），
# 直接驱动 SyncNetInstance.evaluate 对扁平 pycrop/*.avi 评分。
# 运行：/Users/yanyu/YYC-Cube/tools/ComfyUI/.venv/bin/python \
#       scripts/run_syncnet_score.py [--crop_dir /tmp/syncnet_work/pycrop]
# ==============================================================
import argparse
import glob
import os
import sys
from types import SimpleNamespace

REPO = "/Users/yanyu/YYC-Cube/tools/syncnet/syncnet_python"
sys.path.insert(0, REPO)

os.chdir(REPO)  # SyncNetInstance 内部相对路径（data/、tmp/）依赖 cwd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--crop_dir", default="/tmp/syncnet_work/pycrop")
    ap.add_argument("--model", default="data/syncnet_v2.model")
    ap.add_argument("--batch_size", type=int, default=32)
    ap.add_argument("--vshift", type=int, default=15)
    args = ap.parse_args()

    from SyncNetInstance import SyncNetInstance  # noqa: E402  上游模型驱动

    tracks = sorted(glob.glob(os.path.join(args.crop_dir, "*.avi")))
    if not tracks:
        print(f"[syncnet] {args.crop_dir} 无裁切轨（先跑 run_pipeline.py 产脸裁切）")
        return 2

    s = SyncNetInstance()
    s.loadParameters(args.model)
    print(f"[syncnet] model={args.model} tracks={len(tracks)}")

    results = []
    for fname in tracks:
        opt = SimpleNamespace(
            reference=os.path.splitext(os.path.basename(fname))[0],
            tmp_dir="/tmp/syncnet_work/pytmp",
            work_dir="/tmp/syncnet_work/pywork",
            batch_size=args.batch_size, vshift=args.vshift)
        offset, conf, dist = s.evaluate(opt, videofile=fname)

        def _f(x):
            import numpy as _np
            return float(_np.asarray(x).reshape(-1)[0])
        offset, conf, dist = _f(offset), _f(conf), _f(dist)
        verdict = "达标(≥0.75)" if conf >= 0.75 else "打回(<0.75)"
        print(f"[syncnet] track={os.path.basename(fname)} "
              f"offset={offset} conf={conf:.4f} dist={dist:.4f} → {verdict}")
        results.append({"track": os.path.basename(fname), "offset": offset,
                        "conf": round(conf, 4), "dist": round(dist, 4),
                        "verdict": verdict})
    import json
    print(json.dumps({"syncnet": results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
