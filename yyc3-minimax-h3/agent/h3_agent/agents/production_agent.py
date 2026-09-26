# ==============================================================
# H3·织影 生产官 Agent v1.0（阶段4 视听生成 · H3 执行层）
# @file agent/h3_agent/agents/production_agent.py
# @author Intelligent Application Implementation Expert <admin@0379.email>
# @version v1.0.0
# @created 2026-09-26
# @status stable
#
# 对齐：漫剧六阶段 Stage.AUDIOVISUAL_GEN（04_audiovisual_gen）主责执行者；
#       DramaToolGateway.image_to_video 的 H3 真实实现位
# 铁律④：subprocess 仅 argv 数组 + 白名单脚本键 + 批次名白名单 + 强制超时
# 任务类型：generate_batch / generate_single / score_lipsync / export_dashboard
# ==============================================================
import subprocess
import sys
import time
from pathlib import Path

from .. import config
from ..base_agent import H3BaseAgent


class H3ProductionAgent(H3BaseAgent):
    """H3 生产官：白名单脚本调度 → manifest 产物 → 结构化结果回传

    executor 可注入（dry_run 不落盘、测试不依赖 GPU）；生产默认 subprocess argv。
    """

    def __init__(self, agent_id: str = "h3-zhiying-001",
                 agent_name: str = "H3·织影 生产官",
                 transport=None, executor=None, enforce_claim: bool = True):
        super().__init__(
            agent_id=agent_id, agent_name=agent_name,
            role="阶段4·视听生成（image_to_video）",
            capabilities=["video_generation", "image_to_video"],
            stream_name="stream:agent:request:h3-production",
            transport=transport, enforce_claim=enforce_claim)
        self._executor = executor or self._run_script

    # ---------------- 执行核心（铁律④） ----------------
    def _run_script(self, script_key: str, argv: list[str],
                    timeout: int | None = None) -> dict:
        """argv 数组执行白名单脚本；禁 shell；强制超时；返回结构化执行档案"""
        script = config.resolve_script(script_key)          # 白名单解析（不存在即抛错）
        python = config.PYTHON_BIN or sys.executable
        cmd = [python, str(script), *argv]                  # 纯 argv，零拼接
        started = time.time()
        print(f"[{self.name}] 执行：{' '.join(cmd[:2])} {' '.join(argv)}")
        proc = subprocess.run(
            cmd, cwd=config.REPO_ROOT, capture_output=True, text=True,
            timeout=timeout or config.TASK_TIMEOUT)          # 零 shell、强制超时
        return {"script_key": script_key, "argv": argv,
                "returncode": proc.returncode,
                "stdout_tail": proc.stdout[-2000:], "stderr_tail": proc.stderr[-2000:],
                "duration_s": round(time.time() - started, 1)}

    # ---------------- 任务处理 ----------------
    def _handle_task(self, task_type: str, payload: dict, trace_id: str) -> dict:
        handler = {
            "generate_batch": self._task_generate_batch,
            "generate_single": self._task_generate_single,
            "score_lipsync": self._task_score_lipsync,
            "export_dashboard": self._task_export_dashboard,
        }.get(task_type)
        if handler is None:
            raise ValueError(f"生产官不支持的任务类型：{task_type}")
        return handler(payload, trace_id)

    def _task_generate_batch(self, payload: dict, trace_id: str) -> dict:
        """批次闭环：pipeline_auto --batch N --auto（远程触发必加 --auto）"""
        batch = payload["batch"]
        argv = ["--batch", str(batch), "--auto"]
        if payload.get("dry_run"):
            argv.append("--dry-run")
        run = self._executor("pipeline_auto", argv,
                             timeout=payload.get("timeout"))
        manifest = self._read_manifest(batch)
        return {"stage": "04_audiovisual_gen", "task": "generate_batch",
                "batch": str(batch), "trace_id": trace_id,
                "manifest": manifest, "run": run}

    def _task_generate_single(self, payload: dict, trace_id: str) -> dict:
        """任务式单条：batch_ref2va_nf4 --batch N --seeds S[,S]（不改源文件）"""
        batch = payload["batch"]
        argv = ["--batch", str(batch), "--seeds", str(payload["seeds"])]
        if payload.get("variant") in ("nf4", "pruned"):
            argv += ["--variant", payload["variant"]]
        if payload.get("preview"):
            argv.append("--preview")
        if payload.get("prompt_file"):
            pf = Path(payload["prompt_file"])
            if not pf.is_file():
                raise ValueError(f"prompt_file 不存在：{pf}")
            argv += ["--prompt-file", str(pf)]
        run = self._executor("generate_single", argv,
                             timeout=payload.get("timeout"))
        manifest = self._read_manifest(batch)
        return {"stage": "04_audiovisual_gen", "task": "generate_single",
                "batch": str(batch), "trace_id": trace_id,
                "manifest": manifest, "run": run}

    def _task_score_lipsync(self, payload: dict, trace_id: str) -> dict:
        """口型评分：score_lipsync --batch N [--backend b]"""
        argv = ["--batch", str(payload["batch"])]
        if payload.get("backend") in ("auto", "syncnet", "heuristic"):
            argv += ["--backend", payload["backend"]]
        run = self._executor("score_lipsync", argv)
        return {"stage": "04_audiovisual_gen", "task": "score_lipsync",
                "batch": str(payload["batch"]), "trace_id": trace_id, "run": run}

    def _task_export_dashboard(self, payload: dict, trace_id: str) -> dict:
        """面板数据桥（无参脚本；幂等全量重建）"""
        run = self._executor("export_dashboard", [])
        return {"stage": "04_audiovisual_gen", "task": "export_dashboard",
                "trace_id": trace_id, "run": run}

    # ---------------- 产物读取 ----------------
    @staticmethod
    def _read_manifest(batch: str) -> dict | None:
        """读取批次 manifest 摘要（单批产物单一事实源；损坏返回 None 不阻断）"""
        mf = config.REPO_ROOT / f"output_batch{batch}" / "manifest.json"
        if not mf.exists():
            return None
        try:
            import json
            m = json.loads(mf.read_text(encoding="utf-8"))
            records = m.get("records", [])
            return {"batch": m.get("batch"), "records": len(records),
                    "success": sum(1 for r in records if r.get("status") == "SUCCESS"),
                    "failed": sum(1 for r in records if r.get("status") not in
                                  ("SUCCESS", "SKIPPED")),
                    "ended_at": m.get("ended_at")}
        except (json.JSONDecodeError, OSError):
            return None
