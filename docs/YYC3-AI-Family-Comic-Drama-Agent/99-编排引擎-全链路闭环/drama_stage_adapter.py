# ==============================================================
# 漫剧生产六阶段编排适配器 v1.1（闭环审核补全件 + H3 跨仓对接）
# 定位：将 ReAct-C 九步闭环引擎适配到 YYC3-03 漫剧六大生产阶段，
#       补齐「九步闭环（通用协同）↔ 六阶段（漫剧生产）」的落地断点
# v1.1 变更（2026-09-26）：DramaToolGateway.image_to_video 由 stub 替换为经
#       YYC3-MiniMax-H3 agent 网关真实调用（HA：未配置/不可达自动回落 stub，
#       本地调试链路永不断流）；新增 H3VisionClient（仅标准库，零新依赖）
# 对齐文档：
#   - docs/YYC3-03-AI漫剧智能体编排方案.md §2.3（漫剧×ReAct-C 九步映射）
#   - docs/YYC3-AI-Family-Comic-Drama-Agent/YYC3-AI-Family-Agent-全量闭环架构总纲.md §6
#   - docs/YYC3-AI-Family-Comic-Drama-完整版文件树.md（仓库三 conductor/workflows）
# 行业对标（2026-09 调研）：
#   - AniME（Bilibili, SIGGRAPH Asia 2025）：Director Agent 全局记忆 + MCP 工具集
#   - ArcReel：子 Agent 大上下文内部消化、只回传摘要（防上下文爆炸）
#   - 纳米漫剧流水线（360）：单向车道→可回退多车道；资产先行锁定一致性
# 依赖：与 ai_family_orchestrator.py 同目录；无新增第三方依赖
# ==============================================================
import time
from enum import Enum
from urllib.parse import urlparse

import hashlib
import hmac
import ipaddress
import os
import socket

from ai_family_orchestrator import AIFamilyOrchestrator


# -------------------------- 阶段与状态定义 --------------------------
class Stage(str, Enum):
    """漫剧生产六大阶段（对齐 YYC3-03 §2.2）"""
    CREATIVE_KICKOFF = "01_creative_kickoff"      # 阶段1 创意立项
    SCRIPT_STORYBOARD = "02_script_storyboard"    # 阶段2 剧本分镜
    PRODUCTION_DISPATCH = "03_production_dispatch" # 阶段3 生产调度
    AUDIOVISUAL_GEN = "04_audiovisual_gen"        # 阶段4 视听生成
    COMPOSE_DELIVER = "05_compose_deliver"        # 阶段5 合成交付
    OPS_FEEDBACK = "06_ops_feedback"              # 阶段6 运营闭环


class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"        # 质检/审计通过
    REWORK = "rework"        # 打回重做（质量闭环）
    BLOCKED = "blocked"      # 安全拦截（合规红线）


# 阶段→ReAct-C 步骤+场景分支映射（对齐 YYC3-03 §2.3 / 总纲 §6）
STAGE_SCENE_MAP = {
    Stage.CREATIVE_KICKOFF:      {"scene": "C", "steps": "Step1/2/3 + brainstorm"},
    Stage.SCRIPT_STORYBOARD:     {"scene": "B", "steps": "Step3/4（语枢·剧本分镜）"},
    Stage.PRODUCTION_DISPATCH:   {"scene": "A", "steps": "Step2/6 + plan_tasks"},
    Stage.AUDIOVISUAL_GEN:       {"scene": "F", "steps": "Step5 + Step7 质检重绘闭环"},
    Stage.COMPOSE_DELIVER:       {"scene": "A", "steps": "Step6 + Step8 审计交付"},
    Stage.OPS_FEEDBACK:          {"scene": "F", "steps": "Step4（预见）+ Step9 产能画像"},
}

# 阶段→主责 Agent（对齐 YYC3-03 §2.1 漫剧专属角色）
STAGE_OWNERS = {
    Stage.CREATIVE_KICKOFF:      ["创想·灵韵", "格物·宗师", "元启·天枢"],
    Stage.SCRIPT_STORYBOARD:     ["语枢·万物", "智云·守护"],
    Stage.PRODUCTION_DISPATCH:   ["元启·天枢", "言启·千行"],
    Stage.AUDIOVISUAL_GEN:       ["创想·灵韵", "智云·守护"],
    Stage.COMPOSE_DELIVER:       ["元启·天枢", "创想·灵韵"],
    Stage.OPS_FEEDBACK:          ["预见·先知", "知遇·伯乐"],
}

# NAS 标准落位（对齐完整版文件树 projects/{project_id}/）
PROJECT_SUBDIRS = ("script", "storyboard", "images", "clips", "audio", "state", "output")


class H3VisionClient:
    """H3 视听生成网关客户端 v1.0（对接 YYC3-MiniMax-H3 agent/h3_agent/gateway.py）

    - 端点：POST {H3_AGENT_GATEWAY}/api/tasks（task_type=generate_single，同步回执；
      批次闭环走 /api/stages/audiovisual，产物经 H3 manifest / NAS batches.json 查询）
    - 鉴权：X-Claim-Token——HMAC-SHA256 签名算法与 H3 侧 security.issue_claim 完全一致；
      共享密钥 AGENT_CLAIM_SECRET（发放自 H3 仓库 .secrets/agent_claim.env，勿入库）
    - 高可用：网关未配置或调用失败 → 调用方回落 stub（status=stub_fallback），永不断流
    - 依赖：仅标准库（urllib/hashlib/hmac），零新增第三方
    """

    def __init__(self):
        self.base = os.getenv("H3_AGENT_GATEWAY", "").rstrip("/")
        self.secret = os.getenv("AGENT_CLAIM_SECRET", "")
        self.timeout = int(os.getenv("H3_GATEWAY_TIMEOUT", "30"))
        self._validate_base()

    def _validate_base(self):
        """SSRF 防护三道闸：①仅 http(s)；②主机白名单（默认仅本机回环）；③解析 IP 边界校验。

        白名单默认只含本机回环（H3 网关为本机基础设施）；指向内网其他主机必须
        显式配置 H3_ALLOWED_HOSTS。每次校验都重新解析 DNS（防 rebinding），并
        无条件拒绝链路本地/组播/保留地址。
        """
        if not self.base:
            return
        u = urlparse(self.base)
        host = (u.hostname or "").lower()
        explicit = {h.strip().lower() for h in os.getenv(
            "H3_ALLOWED_HOSTS", "localhost,127.0.0.1,::1").split(",") if h.strip()}
        if u.scheme not in ("http", "https") or not host:
            raise PermissionError(f"H3_AGENT_GATEWAY 非法 URL（须为 http/https）: {self.base}")
        if host not in explicit:
            raise PermissionError(
                f"H3_AGENT_GATEWAY 主机不在白名单（SSRF 防护）: {host}；"
                f"如需内网地址请显式配置 H3_ALLOWED_HOSTS")
        self._allowed_hosts = explicit
        for sa in {info[4][0] for info in socket.getaddrinfo(host, None)}:
            ip = ipaddress.ip_address(sa)
            if ip.is_loopback:
                continue  # 本机回环：白名单默认目标（H3 网关为本机基础设施）
            if ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified:
                # 注意：Python 3.13+ 将 ::1 归入保留段的判定不用于回环放行，
                # 回环已在上方显式放行；此处拦截链路本地（含云元数据 169.254）等
                raise PermissionError(f"SSRF 防护：解析地址 {ip} 不可用（链路本地/组播/保留段）")

    def _call(self, path: str, body: bytes | None = None,
              headers: dict | None = None) -> bytes:
        """唯一网络出口（SSRF 收敛点）：白名单复验 → Request → urlopen。

        每次调用都强制重跑 _validate_base 并断言主机在白名单内，
        防止运行期环境变量被篡改后绕过初始化校验。
        """
        import urllib.request as _rq
        if not self.enabled:
            raise RuntimeError("H3_AGENT_GATEWAY 未配置")
        self._validate_base()
        u = urlparse(self.base)
        host = (u.hostname or "").lower()
        assert host in self._allowed_hosts, f"SSRF 防护：主机不在白名单 {host}"
        url = f"{self.base}{path}"
        req = _rq.Request(url, data=body, headers=headers or {})
        with _rq.urlopen(req, timeout=self.timeout) as resp:
            return resp.read()

    @property
    def enabled(self) -> bool:
        return bool(self.base)

    def _claim(self, trace_id: str, task_type: str) -> str:
        """签发 X-Claim-Token（与 H3 issue_claim 同构：trace|task|issued_at|ttl）"""
        import json as _json
        if not self.secret:
            raise PermissionError("AGENT_CLAIM_SECRET 未配置，无法签发 claim")
        issued_at = int(time.time())
        ttl = int(os.getenv("H3_CLAIM_TTL", "300"))
        payload = f"{trace_id}|{task_type}|{issued_at}|{ttl}"
        sig = hmac.new(self.secret.encode(), payload.encode(),
                       hashlib.sha256).hexdigest()
        return _json.dumps({"trace_id": trace_id, "task_type": task_type,
                            "issued_at": issued_at, "ttl": ttl,
                            "signature": sig})

    def healthz(self) -> dict:
        """网关健康探测（传输模式 / claim 就绪状态）"""
        import json as _json
        return _json.loads(self._call("/api/healthz").decode())

    def generate_single(self, batch: str, seeds: str = "42",
                        prompt_file: str = "", variant: str = "",
                        preview: bool = False) -> dict:
        """阶段4 任务式单条 → POST /api/tasks（不改 H3 源文件，seeds 白名单仅数字）"""
        import json as _json
        import uuid as _uuid
        if not self.enabled:
            raise RuntimeError("H3_AGENT_GATEWAY 未配置")
        trace_id = f"trace-{time.strftime('%Y%m%d')}-{_uuid.uuid4().hex[:8]}"
        payload = {"batch": str(batch), "seeds": str(seeds)}
        if prompt_file:
            payload["prompt_file"] = prompt_file
        if variant in ("nf4", "pruned"):
            payload["variant"] = variant
        if preview:
            payload["preview"] = True
        body = _json.dumps({"task_type": "generate_single",
                            "payload": payload}).encode()
        resp = self._call(
            "/api/tasks", data=body,
            headers={"Content-Type": "application/json",
                     "X-Claim-Token": self._claim(trace_id, "generate_single")})
        return _json.loads(resp.decode())


class DramaToolGateway:
    """漫剧工具网关（v1.1：image_to_video 已对接 H3 agent 网关）

    生产环境经 0379-World 网关 /v1/mcp 代理调用（统一鉴权审计）；
    H3 视听生成走 YYC3-MiniMax-H3 agent 网关（H3_AGENT_GATEWAY）；
    其余工具当前仍为接口桩：真实接入时替换各 method 内部实现即可，签名不变。
    对标：AniME「每个 Specialist Agent 绑定专属 MCP 工具集」模式。
    """

    def __init__(self):
        self.h3 = H3VisionClient()

    def text_to_image(self, prompt: str, ref_assets: list = None) -> dict:
        """文生图（关键帧生成；生产对接 ComfyUI/SDXL，经网关标签路由 preview/quality）"""
        return {"task_type": "text_to_image", "status": "stub",
                "prompt": prompt, "ref_count": len(ref_assets or [])}

    def image_to_video(self, image_ref: str, motion_prompt: str = "") -> dict:
        """图生视频（对接 MiniMax-H3：Mac剪枝版预览 / DGX NF4批量）

        v1.1 真实对接：经 H3 agent 网关下发任务——
          image_ref     → H3 批次号（如 "93"，任务落在 output_batch93/）
          motion_prompt → 提示词文件路径（.txt，经 --prompt-file 注入）
        未配置 H3_AGENT_GATEWAY / 未配置密钥 / 网关不可达时回落
        stub_fallback（本地调试链路永不断流，符合五高-高可用）。
        """
        try:
            result = self.h3.generate_single(
                batch=str(image_ref),
                prompt_file=(motion_prompt if motion_prompt.endswith(".txt") else ""))
        except Exception as e:
            return {"task_type": "image_to_video", "status": "stub_fallback",
                    "image_ref": image_ref, "reason": str(e)}
        return {"task_type": "image_to_video", "status": "submitted",
                "image_ref": image_ref,
                "trace_id": result.get("trace_id"),
                "result": result.get("result")}

    def tts(self, text: str, voice_id: str = "default") -> dict:
        """配音 TTS（对接 XTTS v2）"""
        return {"task_type": "tts", "status": "stub", "voice_id": voice_id,
                "text_len": len(text)}

    def sync_score(self, clip_ref: str) -> dict:
        """口型同步评分（对接 SyncNet 双后端；<0.75 打回重生成）"""
        return {"task_type": "sync_score", "status": "stub", "clip_ref": clip_ref,
                "threshold": 0.75}

    def compose(self, timeline: list) -> dict:
        """后期合成（Mac Media Engine VideoToolbox 硬件加速）"""
        return {"task_type": "compose", "status": "stub", "segments": len(timeline)}


class DramaStageAdapter:
    """漫剧六阶段编排适配器

    职责：
    1. 阶段状态机管理：pending→running→passed/rework/blocked（可回退，拒绝单向车道）
    2. 复用九步闭环引擎：每阶段以 scene 分支调用 AIFamilyOrchestrator.execute
    3. 资产记忆bank：阶段产物登记（对标 AniME Asset Memory Bank / ArcReel Character DNA）
    4. 状态事件落位：projects/{project_id}/state/（六环节埋点，对齐完整版文件树）
    """

    def __init__(self, project_id: str):
        self.project_id = project_id
        self.engine = AIFamilyOrchestrator()
        self.tools = DramaToolGateway()
        # 资产记忆库：character DNA / 场景 / 道具 → 后续阶段一致性锚点
        self.asset_memory = {"characters": {}, "scenes": {}, "props": {}}
        # 阶段状态表：{stage: {"status", "qc_score", "attempts", "updated_at"}}
        self.stage_state = {s: {"status": StageStatus.PENDING.value,
                                "qc_score": None, "attempts": 0,
                                "updated_at": None} for s in Stage}

    # ---------------- 阶段状态机 ----------------
    def _update_state(self, stage: Stage, status: StageStatus,
                      qc_score: float = None):
        st = self.stage_state[stage]
        st.update({"status": status.value, "updated_at": time.strftime("%H:%M:%S"),
                   "attempts": st["attempts"] + 1})
        if qc_score is not None:
            st["qc_score"] = qc_score
        print(f"[状态机] {stage.value} → {status.value}")

    def rewind(self, stage: Stage):
        """阶段回退（反「单向车道」：任一阶段可打回上游重做）"""
        self._update_state(stage, StageStatus.PENDING)
        print(f"[状态机] {stage.value} 已回退，可重做")

    # ---------------- 阶段执行 ----------------
    def run_stage(self, stage: Stage, brief: str, user_id: str = "default_user") -> dict:
        """执行单个漫剧生产阶段

        :param brief: 该阶段的创作指令（如剧本大纲/分镜要求/运营目标）
        :return: 阶段执行结果（含九步闭环产出 + 状态机记录）
        """
        scene = STAGE_SCENE_MAP[stage]["scene"]
        print(f"\n{'='*60}\n[漫剧阶段] {stage.value}（场景{scene}｜主责：{'、'.join(STAGE_OWNERS[stage])}）\n{'='*60}")
        self._update_state(stage, StageStatus.RUNNING)

        # 复用 ReAct-C 九步闭环（安全→路由→RAG→执行→质检→审计→画像）
        result = self.engine.execute(brief, user_id=user_id, scene=scene)

        if result["status"] == "blocked":
            self._update_state(stage, StageStatus.BLOCKED)
            return result

        # 质检分回填状态机（格物宗师 ≥80 红线）
        qc = next((s for s in result["steps"] if s["step"] == "quality_check"), None)
        qc_score = qc["result"]["score"] if qc else None
        passed = bool(qc and qc["result"]["passed"])
        self._update_state(stage, StageStatus.PASSED if passed else StageStatus.REWORK,
                           qc_score=qc_score)

        # 阶段产物登记资产记忆库（一致性锚点）
        self.asset_memory.setdefault("artifacts", {})[stage.value] = {
            "brief": brief, "output_digest": result["final_output"][:200],
            "trace_id": result["trace_id"],
        }
        return result

    def run_pipeline(self, briefs: dict, user_id: str = "default_user") -> dict:
        """顺序执行全六阶段（可中断：rework/blocked 阶段停止流水线）

        :param briefs: {Stage: 阶段创作指令}
        """
        pipeline = {"project_id": self.project_id,
                    "stages": {}, "halted_at": None, "status": "success"}
        for stage in Stage:
            if briefs.get(stage) is None:
                continue
            r = self.run_stage(stage, briefs[stage], user_id)
            pipeline["stages"][stage.value] = {
                "status": self.stage_state[stage]["status"],
                "qc_score": self.stage_state[stage]["qc_score"],
                "trace_id": r.get("trace_id"),
            }
            if (self.stage_state[stage]["status"]
                    in (StageStatus.REWORK.value, StageStatus.BLOCKED.value)):
                pipeline["halted_at"] = stage.value
                pipeline["status"] = self.stage_state[stage]["status"]
                break  # 质量闭环：打回后停止，待修正后 rewind 重跑
        return pipeline

    def snapshot(self) -> dict:
        """项目状态快照（写入 projects/{id}/state/ 的标准化事件）"""
        return {"project_id": self.project_id,
                "stage_state": {k.value: v for k, v in self.stage_state.items()},
                "assets_indexed": {k: len(v) for k, v in self.asset_memory.items()},
                "subdirs": PROJECT_SUBDIRS}


# -------------------------- 端到端演示 --------------------------
if __name__ == "__main__":
    adapter = DramaStageAdapter(project_id="demo_001")

    pipeline = adapter.run_pipeline({
        Stage.CREATIVE_KICKOFF: "立项：古风言情漫剧《云鬓》，女主设定+三集钩子规划",
        Stage.SCRIPT_STORYBOARD: "将第一集大纲拆解为12字段分镜JSON，含景别/运镜/时长",
        # 后续阶段按需补充 brief
    })

    print("\n📌 流水线结果：")
    print(pipeline)
    print("\n📌 项目状态快照（→ projects/demo_001/state/）：")
    print(adapter.snapshot())
