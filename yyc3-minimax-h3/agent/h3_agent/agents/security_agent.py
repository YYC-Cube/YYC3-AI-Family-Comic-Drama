# ==============================================================
# 智云·安全哨 Agent（H3 侧）v1.0 —— 安全横切件
# @file agent/h3_agent/agents/security_agent.py
# @author Intelligent Application Implementation Expert <admin@0379.email>
# @version v1.0.0
# @created 2026-09-26
# @status stable
#
# 对齐：漫剧 02-智云守护-安全官（H3 侧无 LLM，纯规则扫描）+ P0-S1 教训
#       （密钥/令牌一律不入库不入日志）
# 职责：security_audit 任务 = claim 体系健康检查 + 审计日志尾部回放
#       + 产物目录密钥模式扫描（防 .env/token 泄漏进批次产物）
# ==============================================================
import re
import time
from pathlib import Path

from .. import config
from ..base_agent import H3BaseAgent
from ..protocol import get_transport
from ..security import AuditLog, issue_claim

_SECRET_PATTERNS = {
    "api_key_like": re.compile(r"(sk-[A-Za-z0-9]{16,}|AIza[A-Za-z0-9_-]{30,})"),
    "redis_url_with_password": re.compile(r"redis://:[^@\s]+@"),
    "bearer_token": re.compile(r"Bearer\s+[A-Za-z0-9._-]{24,}"),
    "private_key_block": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
}


class H3SecurityAgent(H3BaseAgent):
    """智云·安全哨（H3 侧）：fail-closed 安全检查 + 审计回放"""

    def __init__(self, agent_id: str = "h3-zhiyun-001",
                 agent_name: str = "智云·安全哨(H3)",
                 transport=None, enforce_claim: bool = True):
        super().__init__(
            agent_id=agent_id, agent_name=agent_name,
            role="横切·安全审计（security_audit）",
            capabilities=["security_audit"],
            stream_name="stream:agent:request:h3-security",
            transport=transport, enforce_claim=enforce_claim)
        self.audit = AuditLog()

    def _handle_task(self, task_type: str, payload: dict, trace_id: str) -> dict:
        if task_type != "security_audit":
            raise ValueError(f"安全哨不支持的任务类型：{task_type}")
        report = {
            "stage": "cross_cutting", "task": "security_audit",
            "trace_id": trace_id,
            "claim_system": self._check_claim_system(),
            "transport_mode": get_transport()[1],
            "secret_scan": self._scan_outputs(payload.get("scan_glob", "output_batch*/**/*.json")),
            "audit_tail": self.audit.tail(n=10),
            "checked_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        findings = report["secret_scan"]["findings"]
        report["verdict"] = "blocked" if findings else "passed"
        self.audit.emit("security_audit", trace_id=trace_id,
                        verdict=report["verdict"], findings=len(findings))
        return report

    @staticmethod
    def _check_claim_system() -> dict:
        """claim 体系自检：签发→校验→篡改拒绝；密钥缺失 = blocked（fail-closed）"""
        secret = config.load_claim_secret()
        if not secret:
            return {"status": "blocked", "reason": "AGENT_CLAIM_SECRET 未配置"}
        try:
            claim = issue_claim("selfcheck", "security_audit", secret=secret, ttl=60)
            from ..security import verify_claim
            ok = verify_claim(claim, secret=secret)
            tampered = dict(claim, signature="0" * 64)
            return {"status": "online", "sign_ok": ok, "tamper_rejected": not verify_claim(tampered, secret=secret)}
        except Exception as e:  # pragma: no cover
            return {"status": "blocked", "reason": str(e)}

    def _scan_outputs(self, pattern: str) -> dict:
        """产物密钥模式扫描：命中即 blocked（对齐 P0-S1「按泄露处理」原则）"""
        findings = []
        scanned = 0
        for p in config.REPO_ROOT.glob(pattern):
            if not p.is_file() or p.stat().st_size > 2_000_000:
                continue
            scanned += 1
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for name, pat in _SECRET_PATTERNS.items():
                if pat.search(text):
                    findings.append({"file": str(p.relative_to(config.REPO_ROOT)),
                                     "pattern": name})
        return {"scanned_files": scanned, "findings": findings}
