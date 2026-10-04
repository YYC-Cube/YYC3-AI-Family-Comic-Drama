# ==============================================================
# check_agent_drift.py — Agent 代码三拷贝漂移检查（P0-7 治理机制）
# 对照三方（事实源裁定 2026-10-05）：
#   core       = yyc3-0379-world/core/agents/（可运行生产事实源）
#   components = yyc3-ai-agent-archive/components/（参考快照，只读）
#   docs       = docs/YYC3-AI-Family-Comic-Drama-Agent/（规范+快照，只读）
# 输出：逐文件行数/一致性矩阵 + 安全特征块（INJECTION/SENSITIVE_PATTERNS）
#   差异红线检查；--strict 时安全块漂移退出码 1（可入 CI 门禁）
# 运行：python3 scripts/check_agent_drift.py [--strict]
# 零第三方依赖（stdlib only）
# ==============================================================
import hashlib
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CORE = REPO / "yyc3-0379-world" / "core" / "agents"
COMP = REPO / "yyc3-ai-agent-archive" / "components"
DOCS = REPO / "docs" / "YYC3-AI-Family-Comic-Drama-Agent"

# 三方共有的 Agent 文件（core 与 components 同名；docs 目录名见映射）
SHARED = {
    "base_agent.py": ("base_agent.py", "00-公共基座/base_agent.py"),
    "orchestrator.py": ("ai_family_orchestrator.py", "99-编排引擎-全链路闭环/ai_family_orchestrator.py"),
    "zhiyun_shouhu_agent.py": ("zhiyun_shouhu_agent.py", "02-智云守护-安全官/zhiyun_shouhu_agent.py"),
    "yuanqi_tianshu_agent.py": ("yuanqi_tianshu_agent.py", "01-元启天枢-决策中枢/yuanqi_tianshu_agent.py"),
    "gewu_zongshi_agent.py": ("gewu_zongshi_agent.py", "03-格物宗师-质量官/gewu_zongshi_agent.py"),
    "chuangxiang_lingyun_agent.py": ("chuangxiang_lingyun_agent.py", "04-创想灵韵-创意官/chuangxiang_lingyun_agent.py"),
    "yanqi_qianhang_agent.py": ("yanqi_qianhang_agent.py", "05-言启千行-导航员/yanqi_qianhang_agent.py"),
    "yushu_wanwu_agent.py": ("yushu_wanwu_agent.py", "06-语枢万物-思考者/yushu_wanwu_agent.py"),
    "yujian_xianzhi_agent.py": ("yujian_xianzhi_agent.py", "07-预见先知-预言家/yujian_xianzhi_agent.py"),
    "zhiyu_bole_agent.py": ("zhiyu_bole_agent.py", "08-知遇伯乐-推荐官/zhiyu_bole_agent.py"),
}

# 安全特征块计数（红线：core 与 components 必须一致——core 少一条即生产防护缺口，
# 先例：G2-003 五条变体滞留参考库 8 天未回灌）
_SEC_BLOCK = re.compile(r'(INJECTION_PATTERNS|SENSITIVE_PATTERNS)\s*=\s*\[(.*?)\]', re.S)
_SEC_ITEM = re.compile(r'"([^"]+)"')


def fingerprint(p: Path):
    if not p.exists():
        return None
    text = p.read_text(encoding="utf-8")
    sec = {}
    for m in _SEC_BLOCK.finditer(text):
        sec[m.group(1)] = len(_SEC_ITEM.findall(m.group(2)))
    return {"lines": text.count("\n") + 1, "md5": hashlib.md5(text.encode()).hexdigest()[:8], "sec": sec}


def main() -> int:
    strict = "--strict" in sys.argv
    print(f"{'文件':<34}{'core':>14}{'components':>14}{'docs':>14}  c≡comp  c≡docs")
    print("-" * 96)
    sec_drift = []
    identical_cc = identical_cd = total = 0
    for core_name, (comp_name, docs_rel) in SHARED.items():
        total += 1
        fc, fp, fd = (fingerprint(d) for d in (CORE / core_name, COMP / comp_name, DOCS / docs_rel))
        c_md5 = fc["md5"] if fc else "-"
        p_md5 = fp["md5"] if fp else "-"
        d_md5 = fd["md5"] if fd else "-"
        eq_cp = "✓" if fc and fp and fc["md5"] == fp["md5"] else "✗"
        eq_cd = "✓" if fc and fd and fc["md5"] == fd["md5"] else "✗"
        identical_cc += eq_cp == "✓"
        identical_cd += eq_cd == "✓"
        print(f"{core_name:<34}{(fc['lines'] if fc else '-'):>8}/{c_md5:>5}"
              f"{(fp['lines'] if fp else '-'):>8}/{p_md5:>5}"
              f"{(fd['lines'] if fd else '-'):>8}/{d_md5:>5}  {eq_cp:^6}  {eq_cd:^6}")
        # 安全红线：core vs components 特征块条目数
        if fc and fp:
            for block in ("INJECTION_PATTERNS", "SENSITIVE_PATTERNS"):
                n_c, n_p = fc["sec"].get(block), fp["sec"].get(block)
                if n_c is not None and n_p is not None and n_c != n_p:
                    sec_drift.append(f"{core_name}:{block} core={n_c} components={n_p}")

    print("-" * 96)
    print(f"合计 {total} 文件：core≡components {identical_cc}/{total} · "
          f"core≡docs {identical_cd}/{total}（结构变体导致的正常分叉不计故障，"
          f"见 04 号文档 §3 漂移矩阵）")
    if sec_drift:
        print("\n🔴 安全特征块漂移（红线）：")
        for s in sec_drift:
            print(f"  - {s}")
        print("  处置：已验收安全修订须回合 core/agents（生产事实源），"
              "参见 components 对应文件头部修订注记。")
        return 1 if strict else 0
    print("\n✅ 安全特征块（INJECTION/SENSITIVE_PATTERNS）core↔components 一致")
    return 0


if __name__ == "__main__":
    sys.exit(main())
