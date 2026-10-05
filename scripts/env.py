# ==============================================================
# env.py — 根仓 scripts/ 集中配置模块（P2 专项 · 03 交接 TOP2 落地）
# 解决（首审 P1-6/P1-7）：23 个脚本各自 sys.path.insert×30、字面绝对路径×4、
#   三 venv 无声明、~35 环境变量靠头注释考古、生产根默认 /tmp（重启即失）。
# 用法（脚本头部三行替代散装派生）：
#     import sys; sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
#     from env import REPO, MANJU, COMPONENTS, PROJECT_ROOT, ...
# 迁移策略：run_batch_shots 已接入（范式）；其余脚本渐进迁移（新脚本必须用 env）。
# 环境变量覆盖：YYC3_PROJECT_ROOT / YYC3_TOOLS / YYC3_HERO 优先于内置默认。
# ==============================================================
import os
from pathlib import Path

# ── 仓库与子仓路径 ─────────────────────────────────────────
REPO = Path(__file__).resolve().parents[1]
MANJU = REPO / "yyc3-ai-manju-studio"
WORLD = REPO / "yyc3-0379-world"
ARCHIVE = REPO / "yyc3-ai-agent-archive"
H3 = REPO / "yyc3-minimax-h3"
COMPONENTS = ARCHIVE / "components"
SCRIPT_ENGINE = MANJU / "backend" / "app" / "modules" / "script_engine"
AGENTS_DIR = ARCHIVE / "agents"

# ── 外部工具仓（首审硬编码×6 的单一出口） ──────────────────
TOOLS = Path(os.getenv("YYC3_TOOLS", str(Path.home() / "YYC-Cube" / "tools")))
COMFYUI_DIR = TOOLS / "ComfyUI"
HERO = COMFYUI_DIR / "input" / "hero_base.png"   # 参考系唯一锚点（2026-10-02 规则）
PIPER_VOICES = TOOLS / "piper-voices"
SYNCNET_DIR = TOOLS / "syncnet" / "syncnet_python"

# ── 三 venv 声明（首审「无声明文件」收口） ─────────────────
VENV = {
    "manju": MANJU / ".venv" / "bin" / "python",      # insightface/PIL/fastapi/piper（产线主力）
    "world": WORLD / ".venv" / "bin" / "python",      # httpx/jwt（G1/G2 系）
    "comfy": COMFYUI_DIR / ".venv" / "bin" / "python",  # torch/diffusers/peft（训练族）
}

# ── 端口表（首审「默认值分散 10+ 处」收口；分段红线见 README） ──
PORTS = {
    "comfyui": 41888,        # AI 服务 4xxxx
    "tts": 42118,
    "syncnet": 42218,
    "gateway_local": 25080,  # 后端 25xxx
    "stub_upstream": 25290,
    "console": 3100,
    "frontend_dev": 20300,   # 前端 2xxxx
}

# ── 生产项目根（P1-7 迁出 /tmp：默认家目录持久区） ──────────
# 优先级：YYC3_PROJECT_ROOT env > ~/yyc3_projects（新默认）。
# 旧 /tmp/yyc3_projects 若存在产物 → ensure_project_root() 打迁移提示（不自动搬，留人工确认）。
PROJECT_ROOT = Path(os.getenv("YYC3_PROJECT_ROOT",
                              str(Path.home() / "yyc3_projects")))

# ── 常用工作区（原 40+ 处 /tmp 散写；新脚本经 env 取用） ────
WORK = {
    "lora_out": Path("/tmp/kohya_out_sdxl"),        # 训练产物（持久副本在 n1 + ~/YYC-Cube/YYC3-assets）
    "sdxl_combo": Path("/tmp/sdxl_combo"),
    "h3_dyn": Path("/tmp/h3_dyn"),
    "archive_local": Path.home() / "YYC-Cube" / "YYC3-assets",  # 本地持久归档区（仓外）
}

# ── SDXL 产线档（冠军配置单一出口，G4 §三十一/三十二） ───────
SDXL = {
    "ckpt": "DreamShaperXL_Lightning.safetensors",
    "lora": "sd-hero-xl-v1.safetensors",
    "lora_strength": 0.6,
    "instantid_weight": 0.6,
}


def ensure_project_root() -> Path:
    """创建生产根并提示旧 /tmp 产物迁移（幂等）。"""
    PROJECT_ROOT.mkdir(parents=True, exist_ok=True)
    legacy = Path("/tmp/yyc3_projects")
    if legacy.exists() and any(legacy.iterdir()) and PROJECT_ROOT not in legacy.parents:
        print(f"[env] 提示：旧根 {legacy} 仍有产物；"
              f"新根={PROJECT_ROOT}。归档/搬迁后可清理旧根（勿自动搬，留人工确认）")
    return PROJECT_ROOT


def comfy_env(model: str | None = None, timeout: int = 900) -> None:
    """ComfyUI 相关环境变量统一 setdefault（替代各脚本散装 os.environ 行）。"""
    os.environ.setdefault("COMFYUI_URL",
                          f"http://localhost:{PORTS['comfyui']}")
    os.environ.setdefault("COMFYUI_MODEL", model or "DreamShaper_8_pruned.safetensors")
    os.environ.setdefault("COMFYUI_TIMEOUT", str(timeout))
