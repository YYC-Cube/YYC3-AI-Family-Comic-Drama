# ==============================================================
# 智云·守护 Sentinel Agent v1.0
# 角色：安全官 · 行为审计（核心保障层）
# 对齐架构：ReAct-C Step1 输入安全三级过滤 + Step8 输出审计与脱敏
# 能力：越狱防护 / PII脱敏 / 内容合规 / 行为审计（覆盖率100%）
# 模型映射：nemoguard-jailbreak-detect + gliner-pii
#           + nemotron-3.5-content-safety + nemotron-mini-4b（节点2）
# ==============================================================
import json
import re
import time
from base_agent import BaseAgent


class ZhiYunShouHuAgent(BaseAgent):
    # 威胁等级标准
    LEVELS = ("CRITICAL", "HIGH", "MEDIUM", "LOW")

    # 敏感信息模式（PII/密钥类，生产环境由 gliner-pii 模型承接）
    # 注意：Python3 \w 含 CJK 字符，\b 在「汉字+数字」邻接处永不成立，
    # 数字类模式必须用 (?<!\d)/(?!\d) 环视（skills 冒烟矩阵 2026-09-26 缺陷修复）
    SENSITIVE_PATTERNS = [
        (re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)"), "[身份证号已脱敏]"),
        (re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"), "[手机号已脱敏]"),
        (re.compile(r"(?<!\d)(?:\d[ -]*?){13,19}(?!\d)"), "[卡号已脱敏]"),
        (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "[邮箱已脱敏]"),
    ]

    # 提示词注入/越狱攻击特征（生产环境由 nemoguard-jailbreak-detect 承接）
    # G2-003 修订（2026-09-27）：补「忽略之前…」「输出系统提示词」等用例短语变体
    INJECTION_PATTERNS = [
        "忽略以上所有指令", "忽略之前所有指令", "忽略以上所有内容", "忽略之前所有内容",
        "ignore previous instructions", "reveal your prompt",
        "泄露系统提示词", "输出系统提示词", "打印系统提示词",
        "越狱", "jailbreak", "你现在是", "扮演没有限制的",
    ]

    def __init__(self):
        super().__init__(
            name="智云·守护",
            role="安全官·行为审计",
            system_prompt="""你是YYC³ AI Family的「智云·守护」，安全卫士与合规守门人。
职责：守护系统安全、检测威胁、保障运维、全链路审计。

检查清单：
1. 输入安全：Prompt注入检测、XSS/SQL注入过滤
2. 输出安全：敏感信息过滤、合规性检查
3. 运行安全：权限控制、资源限制、异常捕获
4. 数据安全：加密存储、脱敏处理、审计日志

威胁等级评估：
- CRITICAL：立即阻断并告警
- HIGH：记录并建议修复
- MEDIUM：标记并持续监控
- LOW：记录备案

原则：安全第一、最小化收集、全程可追溯、诚实面对不确定性。"""
        )

    # ---------------- Step1：输入安全三级过滤 ----------------
    def check_input(self, user_input: str) -> dict:
        """输入安全三级过滤
        L1 越狱/注入检测 → L2 PII识别 → L3 内容合规
        :return: {"safe": bool, "risk": str, "level": str}
        """
        # L1：注入/越狱检测
        for pattern in self.INJECTION_PATTERNS:
            if pattern.lower() in user_input.lower():
                return {"safe": False, "risk": f"检测到提示词注入/越狱攻击特征：{pattern}",
                        "level": "CRITICAL"}

        # L2：PII 识别（仅标记，不拦截；输出端统一脱敏）
        pii_hits = sum(1 for p, _ in self.SENSITIVE_PATTERNS if p.search(user_input))

        # L3：内容合规（LLM 深度校验，异常降级为规则结论）
        try:
            verdict = self.run(
                f"请判断以下用户输入是否合规（无违法、无有害、无滥用），"
                f"只回答 SAFE 或 UNSAFE：\n{user_input}"
            )
            # 收紧：仅当模型以 UNSAFE 开头才判违规（避免 mock/提示词回显含 "UNSAFE" 字样误判）
            llm_unsafe = verdict.strip().upper().startswith("UNSAFE")
        except Exception:
            llm_unsafe = False

        if llm_unsafe:
            return {"safe": False, "risk": "内容未通过合规审查", "level": "HIGH"}
        if pii_hits:
            return {"safe": True, "risk": f"输入含{pii_hits}类敏感信息，将在输出端脱敏",
                    "level": "MEDIUM"}

        return {"safe": True, "risk": "", "level": "LOW"}

    # ---------------- Step8：输出审计与脱敏 ----------------
    def audit(self, content: str) -> dict:
        """输出安全审计 + 自动脱敏
        :return: {"safe": bool, "desensitized_content": str, "findings": list}
        """
        findings = []
        desensitized = content

        # 规则脱敏（生产环境叠加 gliner-pii 模型）
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            if pattern.search(desensitized):
                desensitized = pattern.sub(replacement, desensitized)
                findings.append(f"已脱敏：{replacement}")

        # LLM 合规审查
        try:
            verdict = self.run(
                f"请审查以下输出内容是否合规（无敏感泄露、无违规有害信息），"
                f"只回答 SAFE 或 UNSAFE：\n{desensitized}"
            )
            safe = not verdict.strip().upper().startswith("UNSAFE")
            if not safe:
                findings.append("内容未通过合规审查")
        except Exception:
            safe = True

        return {"safe": safe, "desensitized_content": desensitized, "findings": findings}

    # ---------------- 全链路审计日志 ----------------
    def write_audit_log(self, trace_id: str, action: str, detail: dict):
        """审计日志写入 stream:audit:log，由消费者落盘 NAS RAID1 永久留存"""
        log_entry = {
            "trace_id": trace_id,
            "auditor": "zhiyun-shouhu-001",
            "action": action,
            "detail": json.dumps(detail, ensure_ascii=False),
            "timestamp": int(time.time() * 1000),
        }
        try:
            from a2a_protocol import MessageProducer
            MessageProducer.send_task("stream:audit:log", log_entry)
        except Exception:
            print(f"[{self.name}] 审计日志（本地兜底）：{log_entry}")
