#!/usr/bin/env python3
"""
@file: check_doc_links.py
@description: docs 内链检查——扫描 markdown 相对链接指向的文件是否存在（防幽灵引用回归）
@author: YanYuCloudCube Team <admin@0379.email>
@version: v1.0.0
@created: 2026-09-23
@status: active
@tags: [tooling],[docs],[ci]
"""

import re
import sys
from pathlib import Path

# 相对链接语法：[text](path) ；#L1-L5 行锚
_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
_MD_FILE_RE = re.compile(r"\.md($|#)", re.IGNORECASE)

# 豁免区（按路径前缀）：历史归档不改写；第三方目录不检查；
# 外部输入资料（原型参考库）自带残缺内链，完整性不由本工程门禁负责
EXCLUDE_PREFIXES = (
    "docs/archive/",
    "docs/templates/",
    "docs/YYC3-多端部署-Agent代码/",
)
EXCLUDE_PARTS = {"node_modules", ".venv", "htmlcov", "test-results", ".git"}


def iter_broken_links(root: Path):
    for md in sorted(root.rglob("*.md")):
        rel = md.relative_to(root).as_posix()
        if rel.startswith(EXCLUDE_PREFIXES):
            continue
        if EXCLUDE_PARTS.intersection(md.parts):
            continue
        text = md.read_text(encoding="utf-8", errors="replace")
        # 剥代码块（``` 围栏内的链接不检查）
        stripped = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        for m in _LINK_RE.finditer(stripped):
            target = m.group(1).strip()
            if not _MD_FILE_RE.search(target):
                continue  # 仅检查 markdown 内链；外链(http/mailto/#锚)交由 lychee 类工具
            path_part = target.split("#", 1)[0]
            if not path_part or path_part.startswith(("http://", "https://", "mailto:", "file://")):
                continue  # 外链/锚点/file协议不检查（file:// 为本机绝对路径，无法静态验证）
            resolved = (md.parent / path_part).resolve()
            if not resolved.exists():
                yield rel, target


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    broken = list(iter_broken_links(root))
    if broken:
        print(f"❌ 发现 {len(broken)} 处 markdown 内链指向不存在的文件：")
        for src, tgt in broken:
            print(f"  - {src} → {tgt}")
        print("\n修复指引：删除/更新该链接，或补齐目标文件后再提交。")
        return 1
    print("✅ docs 内链检查通过（markdown 相对链接全部有效）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
