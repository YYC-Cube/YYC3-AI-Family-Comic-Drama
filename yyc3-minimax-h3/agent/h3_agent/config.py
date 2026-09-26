# ==============================================================
# YYC³ MiniMax-H3 多Agent 框架 · 统一配置层 v1.0
# @file agent/h3_agent/config.py
# @author Intelligent Application Implementation Expert <admin@0379.email>
# @version v1.0.0
# @created 2026-09-26
# @status stable
# @copyright Copyright (c) 2025-2026 YYC3 Team
#
# 对齐：
#   - YYC3-AI-Family-Comic-Drama-Agent/00-公共基座 + 91-A2A-通信协议（配置项同名迁移）
#   - 本仓库安全铁律：密钥只走环境变量（.secrets/ 不入库）；脚本 argv 白名单
# 高可用：配置缺失时给出安全默认值，不阻断框架加载
# ==============================================================
import os
from pathlib import Path

# 仓库根（agent/h3_agent/config.py → 上两级）
AGENT_DIR = Path(__file__).resolve().parent.parent      # agent/
REPO_ROOT = AGENT_DIR.parent                            # 仓库根
SECRETS_DIR = REPO_ROOT / ".secrets"

# ---------------- Redis / A2A 传输 ----------------
REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")        # P2-S4：生产须 requirepass

AGENT_REGISTRY_KEY = "a2a:agent:registry"
HEARTBEAT_TIMEOUT = 90          # 心跳超时（秒），与参照设计一致
DEFAULT_TTL = 300               # 默认消息 TTL（秒）
MAX_RETRY = 3                   # 最大重试次数，超过入死信队列
HEARTBEAT_INTERVAL = 30         # 心跳周期（秒）

# ---------------- H3 执行层（铁律④：零命令拼接） ----------------
# 可被 Agent 调用的脚本白名单（相对 REPO_ROOT；缺席脚本运行时报错，不静默跳过）
SCRIPT_ALLOWLIST = {
    "pipeline_auto":     "scripts/pipeline-tools/pipeline_auto.py",
    "generate_single":   "scripts/batch_ref2va_nf4.py",
    "score_lipsync":     "scripts/score_lipsync.py",
    "export_dashboard":  "scripts/pipeline-tools/export_dashboard_data.py",
    "validate_manifest": "scripts/pipeline-tools/validate_manifest.py",
}
BATCH_NAME_PATTERN = r"^[0-9A-Za-z_-]+$"        # 批次名白名单（防注入，同 video_task_runner）
TASK_TIMEOUT = int(os.getenv("H3_AGENT_TASK_TIMEOUT", "16200"))   # 秒；对齐生产实测 ~7000s/条 × 余量
PYTHON_BIN = os.getenv("H3_PYTHON_BIN", "")     # 强制显式解释器；空则回退 sys.executable

# ---------------- 安全（claim 令牌 / 审计） ----------------
# claim 密钥：优先环境变量，回退 .secrets/agent_claim.env 中的 AGENT_CLAIM_SECRET
CLAIM_SECRET = os.getenv("AGENT_CLAIM_SECRET", "")
CLAIM_TTL = int(os.getenv("AGENT_CLAIM_TTL", "300"))             # claim 有效期（秒）
AUDIT_LOG_PATH = Path(os.getenv(
    "H3_AGENT_AUDIT_LOG", str(REPO_ROOT / "agent" / "data" / "audit_log.jsonl")))

# ---------------- 质量/安全阈值（格物·质检红线） ----------------
QC_PASS_SCORE = float(os.getenv("H3_QC_PASS_SCORE", "6.0"))      # 0-10 刻度合格线
QC_GOOD_SCORE = float(os.getenv("H3_QC_GOOD_SCORE", "8.0"))      # 良好线
QC_EXCELLENT_SCORE = float(os.getenv("H3_QC_EXCELLENT_SCORE", "9.0"))  # 优秀线
QC_MAX_REWORK = int(os.getenv("H3_QC_MAX_REWORK", "2"))          # 最大打回重做次数
SYNC_NORM_THRESHOLD = 0.75      # 口型 score_norm 红线（对齐漫剧 DramaToolGateway.sync_score）


def load_claim_secret() -> str:
    """加载 claim HMAC 密钥：环境变量优先，回退 .secrets/agent_claim.env

    返回空串表示未配置——安全 Agent 将拒绝签发/校验（fail-closed）。
    """
    if CLAIM_SECRET:
        return CLAIM_SECRET
    env_file = SECRETS_DIR / "agent_claim.env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("AGENT_CLAIM_SECRET="):
                return line.split("=", 1)[1].strip()
    return ""


def resolve_script(key: str) -> Path:
    """白名单脚本键 → 绝对路径；不在白名单直接抛错（铁律④，禁止路径拼接绕过）"""
    rel = SCRIPT_ALLOWLIST.get(key)
    if not rel:
        raise ValueError(f"脚本键不在白名单：{key}（允许：{sorted(SCRIPT_ALLOWLIST)}）")
    path = REPO_ROOT / rel
    if not path.exists():
        raise FileNotFoundError(f"白名单脚本缺失：{path}")
    return path
