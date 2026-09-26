# ==============================================================
# 格物·质检 Agent（H3 侧）v1.0 —— 阶段4 质量红线
# @file agent/h3_agent/agents/quality_agent.py
# @author Intelligent Application Implementation Expert <admin@0379.email>
# @version v1.0.0
# @created 2026-09-26
# @status stable
#
# 对齐：漫剧 DramaStageAdapter 质检闭环（qc ≥80 红线 → H3 折算 0-10 刻度）；
#       DramaToolGateway.sync_score 的真实实现（score_norm ≥0.75 红线）
# 职责：读批次 manifest → 计算质检分（0-10）→ passed/rework 判定 + 整改建议
# 规则（全部可经环境变量调参，见 config）：
#   score = 0.6*avg_score + 0.25*success_rate*10 + 0.15*sync_norm_avg*10
#   passed: score ≥ QC_PASS_SCORE 且 sync_norm 均值 ≥ 0.75 且无 FAILED
# ==============================================================
import json
import time
from pathlib import Path

from .. import config
from ..base_agent import H3BaseAgent


class H3QualityAgent(H3BaseAgent):
    """格物·质检（H3 侧）：纯规则实现，无 LLM 依赖（确定性可复现）"""

    def __init__(self, agent_id: str = "h3-gewu-001",
                 agent_name: str = "格物·质检官(H3)",
                 transport=None, enforce_claim: bool = True):
        super().__init__(
            agent_id=agent_id, agent_name=agent_name,
            role="阶段4·质量检查（quality_check）",
            capabilities=["quality_check"],
            stream_name="stream:agent:request:h3-quality",
            transport=transport, enforce_claim=enforce_claim)

    def _handle_task(self, task_type: str, payload: dict, trace_id: str) -> dict:
        if task_type != "quality_check":
            raise ValueError(f"质检官不支持的任务类型：{task_type}")
        batch = str(payload["batch"])
        mf = config.REPO_ROOT / f"output_batch{batch}" / "manifest.json"
        if not mf.exists():
            raise FileNotFoundError(f"manifest 不存在：{mf}")
        manifest = json.loads(mf.read_text(encoding="utf-8"))
        return self.check_records(manifest, batch=batch, trace_id=trace_id)

    # ---------------- 质检核心（纯函数，便于单测） ----------------
    @staticmethod
    def check_records(manifest: dict, batch: str = "", trace_id: str = "") -> dict:
        records = manifest.get("records", [])
        success = [r for r in records if r.get("status") == "SUCCESS"]
        failed = [r for r in records if r.get("status") not in ("SUCCESS", "SKIPPED")]

        scores = []          # 0-10 展示分（人工优先，回退口型×10）
        sync_norms = []      # 0-1 口型同步分
        for r in success:
            human = (r.get("human") or {}).get("score")
            lip_norm = (r.get("lipsync") or {}).get("score_norm")
            if human is not None:
                scores.append(float(human))
            elif lip_norm is not None:
                scores.append(round(float(lip_norm) * 10, 1))
            if lip_norm is not None:
                sync_norms.append(float(lip_norm))

        total = len(success) + len(failed)
        success_rate = (len(success) / total) if total else 0.0
        avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0
        sync_avg = round(sum(sync_norms) / len(sync_norms), 4) if sync_norms else 0.0
        qc_score = round(0.6 * avg_score + 0.25 * success_rate * 10
                         + 0.15 * sync_avg * 10, 2)

        passed = (qc_score >= config.QC_PASS_SCORE
                  and (not sync_norms or sync_avg >= config.SYNC_NORM_THRESHOLD)
                  and not failed)
        verdict = ("passed" if passed else
                   "rework" if qc_score >= config.QC_PASS_SCORE * 0.6 else "rework")

        suggestions = []
        if failed:
            suggestions.append(f"{len(failed)} 条 FAILED，检查 stderr 与显存分配后重跑")
        if sync_norms and sync_avg < config.SYNC_NORM_THRESHOLD:
            suggestions.append(f"口型同步均值 {sync_avg} < {config.SYNC_NORM_THRESHOLD}，"
                               "优先重生成低分 seed")
        if scores and avg_score < config.QC_PASS_SCORE:
            suggestions.append(f"均分 {avg_score} < {config.QC_PASS_SCORE}，"
                               "回看人工标签聚焦缺陷簇（defects Top3）")

        return {"stage": "04_audiovisual_gen", "task": "quality_check",
                "batch": batch, "trace_id": trace_id,
                "qc_score": qc_score,
                "detail": {"avg_score": avg_score, "sync_norm_avg": sync_avg,
                           "success_rate": round(success_rate, 4),
                           "success": len(success), "failed": len(failed)},
                "verdict": verdict, "passed": passed,
                "thresholds": {"pass": config.QC_PASS_SCORE,
                               "good": config.QC_GOOD_SCORE,
                               "excellent": config.QC_EXCELLENT_SCORE,
                               "sync_norm": config.SYNC_NORM_THRESHOLD},
                "suggestions": suggestions,
                "checked_at": time.strftime("%Y-%m-%dT%H:%M:%S")}


def quality_of(avg_score: float) -> str:
    """0-10 分 → 质量档位（与 dashboard 面板 qualityOf 同阈值）"""
    if avg_score >= config.QC_EXCELLENT_SCORE:
        return "优秀"
    if avg_score >= config.QC_GOOD_SCORE:
        return "良好"
    if avg_score >= config.QC_PASS_SCORE:
        return "合格"
    return "待优化"
