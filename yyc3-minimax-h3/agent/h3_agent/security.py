# ==============================================================
# YYC³ MiniMax-H3 多Agent 框架 · 安全层 v1.0（智云·守护 H3 侧横切件）
# @file agent/h3_agent/security.py
# @author Intelligent Application Implementation Expert <admin@0379.email>
# @version v1.0.0
# @created 2026-09-26
# @status stable
#
# 职责：
#   1. claim 令牌：HMAC-SHA256 签发/校验（trace_id+task_type+签发时刻），fail-closed
#   2. 批次名/脚本键白名单校验（对齐本仓库铁律④与 video_task_runner 惯例）
#   3. 审计事件落盘（JSONL，NAS 可同步；对齐智云守护「审计流→NAS 落盘」职责）
# 对齐：YYC3-AI-Family-Comic-Drama-Agent/02-智云守护-安全官（H3 侧无 LLM，纯规则实现）
# ==============================================================
import hashlib
import hmac
import json
import re
import threading
import time
from pathlib import Path

from . import config

_BATCH_RE = re.compile(config.BATCH_NAME_PATTERN)


# ---------------- claim 令牌 ----------------
def issue_claim(trace_id: str, task_type: str, secret: str | None = None,
                ttl: int | None = None) -> dict:
    """签发 claim 令牌；未配置密钥时抛错（fail-closed，不静默放行）"""
    secret = secret if secret is not None else config.load_claim_secret()
    if not secret:
        raise PermissionError("未配置 AGENT_CLAIM_SECRET，拒绝签发 claim（fail-closed）")
    issued_at = int(time.time())
    ttl = ttl if ttl is not None else config.CLAIM_TTL
    payload = f"{trace_id}|{task_type}|{issued_at}|{ttl}"
    sig = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return {"trace_id": trace_id, "task_type": task_type,
            "issued_at": issued_at, "ttl": ttl, "signature": sig}


def verify_claim(claim: dict, secret: str | None = None) -> bool:
    """校验 claim 令牌：签名一致 + 未过期；任何异常一律拒绝"""
    secret = secret if secret is not None else config.load_claim_secret()
    if not secret or not isinstance(claim, dict):
        return False
    try:
        payload = (f"{claim['trace_id']}|{claim['task_type']}"
                   f"|{int(claim['issued_at'])}|{int(claim['ttl'])}")
        expect = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expect, str(claim["signature"])):
            return False
        age = time.time() - int(claim["issued_at"])
        return 0 <= age <= int(claim["ttl"])
    except (KeyError, TypeError, ValueError):
        return False


# ---------------- 白名单校验 ----------------
def valid_batch_name(batch: str) -> bool:
    """批次名白名单：仅 [0-9A-Za-z_-]+（与 video_task_runner 同规）"""
    return bool(batch) and bool(_BATCH_RE.fullmatch(str(batch)))


def validate_task_payload(task_type: str, payload: dict) -> list[str]:
    """任务载荷静态校验：返回违规项列表（空列表=通过）

    覆盖：批次名白名单、seeds 数字白名单、脚本键存在性。
    生产 Agent 在 argv 组装前必须调用本函数。
    """
    errors: list[str] = []
    batch = payload.get("batch")
    if batch is not None and not valid_batch_name(batch):
        errors.append(f"批次名违规：{batch!r}（白名单 {config.BATCH_NAME_PATTERN}）")
    seeds = payload.get("seeds")
    if seeds is not None:
        for s in str(seeds).split(","):
            s = s.strip()
            if s and not s.isdigit():
                errors.append(f"seed 违规（仅数字）：{s!r}")
    script_key = payload.get("script_key")
    if script_key is not None and script_key not in config.SCRIPT_ALLOWLIST:
        errors.append(f"脚本键不在白名单：{script_key!r}")
    if task_type not in SUPPORTED_TASK_TYPES:
        errors.append(f"任务类型不受支持：{task_type!r}")
    return errors


SUPPORTED_TASK_TYPES = {
    "generate_batch",      # 批次闭环（pipeline_auto）
    "generate_single",     # 任务式单条（batch_ref2va_nf4 --seeds）
    "score_lipsync",       # 口型评分
    "export_dashboard",    # 面板数据桥
    "validate_manifest",   # manifest 契约校验
    "quality_check",       # 格物·质检
    "security_audit",      # 智云·安全哨
}


# ---------------- 审计落盘（线程安全 JSONL） ----------------
class AuditLog:
    """审计事件追加写：agent/data/audit_log.jsonl（NAS 同步友好：单行 JSON）"""

    def __init__(self, path: Path | None = None):
        self.path = path or config.AUDIT_LOG_PATH
        self._lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, action: str, trace_id: str = "", **fields):
        event = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                 "action": action, "trace_id": trace_id, **fields}
        line = json.dumps(event, ensure_ascii=False)
        with self._lock, self.path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
        return event

    def tail(self, n: int = 20) -> list[dict]:
        """读取最近 n 条审计（安全 Agent security_audit 任务复用）"""
        if not self.path.exists():
            return []
        lines = self.path.read_text(encoding="utf-8").splitlines()[-n:]
        out = []
        for ln in lines:
            try:
                out.append(json.loads(ln))
            except json.JSONDecodeError:
                continue
        return out
