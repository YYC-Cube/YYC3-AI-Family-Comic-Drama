#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@file YYC3-团队文档-引擎模版.py
@description YYC³文档模版引擎 - 可复用、可迭代、可追溯的文档闭环生成系统
@author YanYuCloudCube Team <admin@0379.email>
@version v3.1.0
@created 2026-03-27
@updated 2026-05-02
@status stable
@copyright Copyright (c) 2026 YYC³ Team
@license MIT
"""

import os
import sys
import json
import hashlib
import datetime
import argparse
import logging
import shutil
import difflib
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import OrderedDict
import re
import yaml

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class DocumentType(Enum):
    MAIN = "main"
    README = "readme"
    ROOT_README = "root_readme"
    RESERVED = "reserved"
    TEMPLATE = "template"
    CHANGELOG = "changelog"
    API = "api"
    ARCHITECTURE = "architecture"


@dataclass
class DocumentMetadata:
    file_name: str
    description: str
    author: str = "YanYuCloudCube Team"
    version: str = "v3.0.0"
    created: str = ""
    updated: str = ""
    status: str = "published"
    tags: List[str] = field(default_factory=list)
    checksum: str = ""
    trace_id: str = ""
    parent_doc: str = ""
    related_docs: List[str] = field(default_factory=list)
    category: str = ""
    language: str = "zh-CN"

    def __post_init__(self):
        now = datetime.datetime.now().strftime("%Y-%m-%d")
        if not self.created:
            self.created = now
        if not self.updated:
            self.updated = now
        if not self.trace_id:
            self.trace_id = self._generate_trace_id()

    def _generate_trace_id(self) -> str:
        raw = f"{self.file_name}:{self.version}:{datetime.datetime.now().isoformat()}"
        return f"TRC-{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:12].upper()}"


@dataclass
class TemplateConfig:
    template_id: str
    template_name: str
    template_version: str
    template_type: DocumentType
    content_template: str
    variables: Dict[str, Any] = field(default_factory=dict)
    validation_rules: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TraceRecord:
    timestamp: str
    document: str
    action: str
    version: str
    checksum: str
    author: str
    trace_id: str
    diff_summary: str = ""


class YYC3TemplateEngine:

    BRAND_HEADER = """> ***YanYuCloudCube***
> *言启象限 | 语枢未来*
> ***Words Initiate Quadrants, Language Serves as Core for Future***
> *万象归元于云枢 | 深栈智启新纪元*
> ***All things converge in cloud pivot; Deep stacks ignite a new era of intelligence***"""

    BRAND_FOOTER = """<div align="center">

> 「***YanYuCloudCube***」
> 「***<admin@0379.email>***」
> 「***Words Initiate Quadrants, Language Serves as Core for the Future***」
> 「***All things converge in cloud pivot; Deep stacks ignite a new era of intelligence***」

**© 2025-2026 YYC³ Team. All Rights Reserved.**
</div>"""

    CORE_PHILOSOPHY = """## 核心理念

**五高架构**：高可用 | 高性能 | 高安全 | 高扩展 | 高智能
**五标体系**：标准化 | 规范化 | 自动化 | 可视化 | 智能化
**五化转型**：流程化 | 数字化 | 生态化 | 工具化 | 服务化
**五维评估**：时间维 | 空间维 | 属性维 | 事件维 | 关联维"""

    def __init__(self, output_dir: str = "docs", config_path: str = ""):
        self.output_dir = Path(output_dir)
        self.config_path = config_path
        self.templates: Dict[str, TemplateConfig] = {}
        self.document_registry: Dict[str, DocumentMetadata] = {}
        self.traceability_chain: List[Dict] = []
        self.global_variables: Dict[str, Any] = {}
        self.validation_rules: Dict[str, Any] = {}
        self.history_dir = self.output_dir / ".history"
        self.registry_path = self.output_dir / ".registry.json"

        if config_path and os.path.exists(config_path):
            self.load_template_config(config_path)
        if self.registry_path.exists():
            self._load_registry()

    def generate_checksum(self, content: str) -> str:
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]

    def load_template_config(self, config_path: str) -> None:
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)

            self.global_variables = config_data.get('global_variables', {})
            self.validation_rules = config_data.get('validation_rules', {})

            for template_id, config in config_data.get('templates', {}).items():
                try:
                    doc_type = DocumentType(config.get('type', 'main'))
                except ValueError:
                    doc_type = DocumentType.MAIN

                self.templates[template_id] = TemplateConfig(
                    template_id=template_id,
                    template_name=config.get('name', ''),
                    template_version=config.get('version', 'v1.0.0'),
                    template_type=doc_type,
                    content_template=config.get('content', ''),
                    variables=config.get('variables', {}),
                    validation_rules=config.get('validation', {})
                )
            logger.info(f"已加载 {len(self.templates)} 个模版配置")
        except FileNotFoundError:
            logger.warning(f"模版配置文件未找到: {config_path}")

    def _build_variables(self, extra: Dict[str, Any] = None) -> Dict[str, Any]:
        now = datetime.datetime.now()
        defaults = {
            "created_date": now.strftime("%Y-%m-%d"),
            "updated_date": now.strftime("%Y-%m-%d"),
            "author": self.global_variables.get("default_author", "YanYuCloudCube Team"),
            "version": self.global_variables.get("default_version", "v3.0.0"),
            "status": "published",
            "tags": "",
            "checksum": "",
            "trace_id": "",
            "related_docs": "",
        }
        merged = {**defaults, **self.global_variables}
        if extra:
            merged.update(extra)
        return merged

    def render_template(self, template_id: str, variables: Dict[str, Any] = None) -> str:
        if template_id not in self.templates:
            raise ValueError(f"模版不存在: {template_id}")

        template = self.templates[template_id]
        content = template.content_template
        merged_vars = self._build_variables({**template.variables, **(variables or {})})

        for key, value in merged_vars.items():
            placeholder = "{{" + str(key) + "}}"
            content = content.replace(placeholder, str(value) if value is not None else "")

        unreplaced = re.findall(r'\{\{(\w+)\}\}', content)
        if unreplaced:
            for var in unreplaced:
                content = content.replace("{{" + var + "}}", "")

        return content

    def generate_main_document(self, metadata: DocumentMetadata, content_sections: Dict[str, str]) -> str:
        metadata.checksum = metadata.checksum or self.generate_checksum(metadata.description)
        sections_md = ""
        for section_name, section_content in content_sections.items():
            sections_md += f"## {section_name}\n\n{section_content}\n\n---\n\n"

        doc_content = f"""---
@file: {metadata.file_name}
@description: {metadata.description}
@author: {metadata.author}
@version: {metadata.version}
@created: {metadata.created}
@updated: {metadata.updated}
@status: {metadata.status}
@tags: {','.join(metadata.tags)}
@trace_id: {metadata.trace_id}
@category: {metadata.category}
@language: {metadata.language}
---

{self.BRAND_HEADER}

---

# {metadata.file_name.replace('.md', '').replace('-', ' ')}

{self.CORE_PHILOSOPHY}

---

## 文档概述

{metadata.description}

---

{sections_md}
## 文档追溯信息

| 属性 | 值 |
|------|-----|
| 文档版本 | {metadata.version} |
| 创建日期 | {metadata.created} |
| 更新日期 | {metadata.updated} |
| 内容校验 | {metadata.checksum} |
| 追溯ID | {metadata.trace_id} |
| 关联文档 | {', '.join(metadata.related_docs) if metadata.related_docs else '无'} |

---

{self.BRAND_FOOTER}
"""
        return doc_content

    def generate_readme_document(self, dir_name: str, dir_description: str, doc_list: List[Dict]) -> str:
        doc_table = "| 序号 | 文档名称 | 描述 | 标签 |\n|------|----------|------|------|\n"
        for idx, doc in enumerate(doc_list, 1):
            name = doc.get('name', '')
            desc = doc.get('description', doc.get('desc', ''))
            tags = doc.get('tags', '')
            doc_table += f"| {idx} | [{name}]({name}) | {desc} | {tags} |\n"

        now = datetime.datetime.now().strftime("%Y-%m-%d")
        return f"""---
@file: README.md
@description: {dir_name} 目录文档索引
@author: YanYuCloudCube Team
@version: v3.0.0
@created: {now}
@updated: {now}
@status: published
@tags: [文档索引],[README]
---

{self.BRAND_HEADER}

---

# {dir_name}

{self.CORE_PHILOSOPHY}

---

## 目录概述

{dir_description}

---

## 文档索引

{doc_table}
---

## 文档规范

- **命名规范**：`{{编号}}-{{阶段}}-{{模块}}-{{文档名称}}.md`
- **版本规范**：主版本.次版本.修订版本 (如 v3.0.0)
- **标签规范**：使用方括号包裹，如 `[标签1],[标签2]`

---

{self.BRAND_FOOTER}
"""

    def register_document(self, metadata: DocumentMetadata) -> None:
        self.document_registry[metadata.trace_id] = metadata
        self._persist_registry()

    def _persist_registry(self) -> None:
        data = {
            "export_time": datetime.datetime.now().isoformat(),
            "total_documents": len(self.document_registry),
            "documents": {},
            "traceability_chain": [asdict(r) if hasattr(r, '__dataclass_fields__') else r for r in self.traceability_chain]
        }
        for doc_id, meta in self.document_registry.items():
            data["documents"][doc_id] = {
                "file_name": meta.file_name,
                "description": meta.description,
                "version": meta.version,
                "checksum": meta.checksum,
                "trace_id": meta.trace_id,
                "tags": meta.tags,
                "related_docs": meta.related_docs,
                "updated": meta.updated,
            }
        self.output_dir.mkdir(parents=True, exist_ok=True)
        with open(self.registry_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load_registry(self) -> None:
        try:
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.traceability_chain = data.get('traceability_chain', [])
            for doc_id, doc_data in data.get('documents', {}).items():
                meta = DocumentMetadata(
                    file_name=doc_data.get('file_name', ''),
                    description=doc_data.get('description', ''),
                    version=doc_data.get('version', 'v3.0.0'),
                    checksum=doc_data.get('checksum', ''),
                    trace_id=doc_data.get('trace_id', doc_id),
                    tags=doc_data.get('tags', []),
                    related_docs=doc_data.get('related_docs', []),
                )
                self.document_registry[doc_id] = meta
        except Exception as e:
            logger.warning(f"加载注册表失败: {e}")

    def add_trace_record(self, metadata: DocumentMetadata, action: str, diff_summary: str = "") -> None:
        record = TraceRecord(
            timestamp=datetime.datetime.now().isoformat(),
            document=metadata.file_name,
            action=action,
            version=metadata.version,
            checksum=metadata.checksum,
            author=metadata.author,
            trace_id=metadata.trace_id,
            diff_summary=diff_summary,
        )
        self.traceability_chain.append(asdict(record))
        self._persist_registry()

    def _compute_diff(self, old_content: str, new_content: str) -> str:
        diff = difflib.unified_diff(
            old_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile='before', tofile='after', n=1
        )
        lines = list(diff)
        if not lines:
            return "无变更"
        added = sum(1 for l in lines if l.startswith('+') and not l.startswith('+++'))
        removed = sum(1 for l in lines if l.startswith('-') and not l.startswith('---'))
        return f"+{added}/-{removed} 行变更"

    def save_document(self, content: str, output_path: str, metadata: DocumentMetadata = None) -> bool:
        try:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            diff_summary = ""
            if path.exists() and metadata:
                old_content = path.read_text(encoding='utf-8')
                diff_summary = self._compute_diff(old_content, content)
                if old_content == content:
                    logger.info(f"文档无变更，跳过: {output_path}")
                    return True
                self._archive_version(path, metadata)

            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)

            if metadata:
                metadata.checksum = self.generate_checksum(content)
                self.register_document(metadata)
                action = "update" if diff_summary else "create"
                self.add_trace_record(metadata, action, diff_summary)

            logger.info(f"文档已保存: {output_path}")
            return True
        except Exception as e:
            logger.error(f"保存文档失败: {e}")
            return False

    def _archive_version(self, file_path: Path, metadata: DocumentMetadata) -> None:
        if not self.history_dir.exists():
            self.history_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        archive_name = f"{file_path.stem}__{metadata.version}__{ts}{file_path.suffix}"
        shutil.copy2(file_path, self.history_dir / archive_name)
        logger.info(f"历史版本已归档: {archive_name}")

    def validate_document(self, content: str, rules: Dict[str, Any] = None) -> Tuple[bool, List[str]]:
        rules = rules or self.validation_rules or {}
        errors = []

        if rules.get('require_brand_header', True):
            if 'YanYuCloudCube' not in content:
                errors.append("缺少品牌标识头")

        if rules.get('require_brand_footer', True):
            if 'admin@0379.email' not in content:
                errors.append("缺少品牌标识尾")

        if rules.get('require_metadata', True):
            if not content.startswith('---'):
                errors.append("缺少元数据块")

        if rules.get('require_core_philosophy', True):
            if '五高架构' not in content:
                errors.append("缺少核心理念块")

        min_len = rules.get('min_length', 0)
        if min_len > 0 and len(content) < min_len:
            errors.append(f"文档长度不足: {len(content)} < {min_len}")

        max_len = rules.get('max_length', 0)
        if max_len > 0 and len(content) > max_len:
            errors.append(f"文档长度超限: {len(content)} > {max_len}")

        return len(errors) == 0, errors

    def validate_file(self, file_path: str) -> Tuple[bool, List[str]]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return self.validate_document(content)
        except Exception as e:
            return False, [f"读取文件失败: {e}"]

    def batch_validate(self, directory: str) -> Dict[str, Tuple[bool, List[str]]]:
        results = {}
        target = Path(directory)
        for md_file in sorted(target.rglob("*.md")):
            ok, errs = self.validate_file(str(md_file))
            results[str(md_file)] = (ok, errs)
        return results

    def export_registry(self, output_path: str = None) -> None:
        output_path = output_path or str(self.output_dir / "document_registry.json")
        self._persist_registry()
        logger.info(f"文档注册表已导出: {output_path}")


class DocumentProjectStructure:
    PROJECT_STRUCTURE = {
        "00-项目总览索引": {
            "description": "项目全局视图与导航",
            "documents": [
                {"id": "001", "name": "项目总览手册.md", "desc": "项目立项核心依据与目标范围", "tags": "[总览],[项目]"},
                {"id": "002", "name": "文档架构导航.md", "desc": "文档体系导航与索引", "tags": "[导航],[文档]"},
                {"id": "003", "name": "快速开始指南.md", "desc": "项目快速启动与使用指南", "tags": "[指南],[快速开始]"},
                {"id": "004", "name": "核心概念词典.md", "desc": "项目核心概念与术语定义", "tags": "[概念],[词典]"},
                {"id": "005", "name": "版本更新日志.md", "desc": "项目版本迭代与变更记录", "tags": "[日志],[版本]"},
            ]
        },
        "01-启动规划阶段": {
            "description": "项目启动与规划管理",
            "subcategories": {
                "0101-项目规划": {
                    "documents": [
                        {"id": "001", "name": "项目章程与愿景.md", "desc": "项目立项核心依据", "tags": "[规划],[章程]"},
                        {"id": "002", "name": "项目范围说明书.md", "desc": "项目范围边界定义", "tags": "[规划],[范围]"},
                        {"id": "003", "name": "项目里程碑计划.md", "desc": "阶段里程碑与任务拆解", "tags": "[规划],[里程碑]"},
                        {"id": "004", "name": "项目资源规划.md", "desc": "资源统筹分配", "tags": "[规划],[资源]"},
                        {"id": "005", "name": "干系人管理计划.md", "desc": "相关方识别与沟通策略", "tags": "[规划],[干系人]"},
                    ]
                },
                "0102-需求规划": {
                    "documents": [
                        {"id": "001", "name": "业务需求分析.md", "desc": "核心业务需求梳理", "tags": "[需求],[业务]"},
                        {"id": "002", "name": "用户需求调研报告.md", "desc": "用户痛点与期望分析", "tags": "[需求],[调研]"},
                        {"id": "003", "name": "产品需求文档(PRD).md", "desc": "功能规格与验收标准", "tags": "[需求],[PRD]"},
                        {"id": "004", "name": "需求优先级矩阵.md", "desc": "需求优先级评估排序", "tags": "[需求],[优先级]"},
                    ]
                },
                "0103-可行性分析": {
                    "documents": [
                        {"id": "001", "name": "技术可行性分析.md", "desc": "技术风险评估", "tags": "[可行性],[技术]"},
                        {"id": "002", "name": "经济可行性分析.md", "desc": "成本效益分析", "tags": "[可行性],[经济]"},
                        {"id": "003", "name": "市场可行性分析.md", "desc": "市场前景与竞争分析", "tags": "[可行性],[市场]"},
                        {"id": "004", "name": "操作可行性分析.md", "desc": "实施难度与运营风险", "tags": "[可行性],[运营]"},
                    ]
                },
                "0104-风险管理": {
                    "documents": [
                        {"id": "001", "name": "项目初期风险评估.md", "desc": "全周期风险识别", "tags": "[风险],[评估]"},
                        {"id": "002", "name": "风险应对预案.md", "desc": "风险应对策略", "tags": "[风险],[预案]"},
                        {"id": "003", "name": "项目预算与成本控制.md", "desc": "预算编制与控制", "tags": "[风险],[预算]"},
                        {"id": "004", "name": "项目成功标准定义.md", "desc": "成功度量指标", "tags": "[风险],[标准]"},
                    ]
                }
            }
        },
        "02-项目设计阶段": {
            "description": "系统架构与详细设计",
            "subcategories": {
                "0201-架构设计": {
                    "documents": [
                        {"id": "001", "name": "系统架构总览图.md", "desc": "整体架构视图", "tags": "[架构],[总览]"},
                        {"id": "002", "name": "九层功能架构设计.md", "desc": "分层架构设计", "tags": "[架构],[分层]"},
                        {"id": "003", "name": "技术选型论证报告.md", "desc": "技术栈选型依据", "tags": "[架构],[选型]"},
                        {"id": "004", "name": "微服务架构设计.md", "desc": "服务拆分与治理", "tags": "[架构],[微服务]"},
                        {"id": "005", "name": "网络拓扑图.md", "desc": "网络架构设计", "tags": "[架构],[网络]"},
                        {"id": "006", "name": "高可用设计.md", "desc": "容灾与高可用方案", "tags": "[架构],[高可用]"},
                    ]
                },
                "0202-详细设计": {
                    "subcategories": {
                        "基础设施层": {"documents": []},
                        "数据存储层": {"documents": []},
                        "核心服务层": {"documents": []},
                        "AI智能层": {"documents": []},
                        "业务逻辑层": {"documents": []},
                        "应用表现层": {"documents": []},
                        "用户交互层": {"documents": []},
                    }
                }
            }
        },
        "03-开发实施阶段": {
            "description": "代码开发与实施",
            "subcategories": {
                "0301-开发环境": {
                    "documents": [
                        {"id": "001", "name": "开发环境搭建指南.md", "desc": "环境配置说明", "tags": "[开发],[环境]"},
                        {"id": "002", "name": "多环境配置规范.md", "desc": "环境隔离策略", "tags": "[开发],[配置]"},
                    ]
                },
                "0302-开发规范": {
                    "documents": [
                        {"id": "001", "name": "Git工作流规范.md", "desc": "分支管理策略", "tags": "[规范],[Git]"},
                        {"id": "002", "name": "代码提交规范.md", "desc": "提交信息格式", "tags": "[规范],[提交]"},
                        {"id": "003", "name": "代码注释规范.md", "desc": "注释标准格式", "tags": "[规范],[注释]"},
                    ]
                }
            }
        },
        "04-测试审核阶段": {
            "description": "质量保障与审核",
            "subcategories": {
                "0401-测试策略": {
                    "documents": [
                        {"id": "001", "name": "测试策略总纲.md", "desc": "整体测试方案", "tags": "[测试],[策略]"},
                        {"id": "002", "name": "测试环境管理规范.md", "desc": "测试环境配置", "tags": "[测试],[环境]"},
                    ]
                },
                "0406-质量审核": {
                    "documents": [
                        {"id": "001", "name": "代码质量审核标准.md", "desc": "代码质量度量", "tags": "[质量],[审核]"},
                        {"id": "002", "name": "质量门禁标准.md", "desc": "质量准入准出标准", "tags": "[质量],[门禁]"},
                    ]
                }
            }
        },
        "05-交付部署阶段": {
            "description": "项目交付与部署",
            "subcategories": {
                "0507-交付物管理": {
                    "documents": [
                        {"id": "001", "name": "交付物清单.md", "desc": "交付物列表", "tags": "[交付],[清单]"},
                        {"id": "002", "name": "交付验收标准.md", "desc": "验收标准定义", "tags": "[交付],[验收]"},
                    ]
                }
            }
        },
        "06-运维保障阶段": {
            "description": "系统运维与保障",
            "subcategories": {
                "0601-运维策略": {
                    "documents": [
                        {"id": "001", "name": "运维策略总纲.md", "desc": "运维整体方案", "tags": "[运维],[策略]"},
                    ]
                }
            }
        },
        "07-合规安全保障": {
            "description": "安全与合规管理",
            "subcategories": {
                "0702-安全管理": {
                    "documents": [
                        {"id": "001", "name": "安全开发规范.md", "desc": "安全编码标准", "tags": "[安全],[开发]"},
                        {"id": "002", "name": "安全运维规范.md", "desc": "安全运维流程", "tags": "[安全],[运维]"},
                    ]
                }
            }
        },
        "08-资产知识管理": {
            "description": "资产与知识管理",
            "subcategories": {
                "0801-资产管理": {
                    "documents": [
                        {"id": "001", "name": "资产清单.md", "desc": "项目资产列表", "tags": "[资产],[清单]"},
                    ]
                }
            }
        },
        "09-智能演进优化": {
            "description": "持续演进与优化",
            "subcategories": {
                "0907-质量提升": {
                    "documents": [
                        {"id": "001", "name": "持续改进计划.md", "desc": "优化改进方案", "tags": "[优化],[改进]"},
                    ]
                }
            }
        }
    }

    def generate_skeleton(self, output_dir: str, engine: YYC3TemplateEngine, dry_run: bool = False) -> List[str]:
        created = []
        root = Path(output_dir)

        def _walk_structure(structure: dict, parent: Path):
            for dir_name, config in structure.items():
                current_dir = parent / dir_name
                docs = config.get("documents", [])

                if docs:
                    if not dry_run:
                        current_dir.mkdir(parents=True, exist_ok=True)
                    doc_list_for_readme = []
                    for doc in docs:
                        file_name = doc["name"]
                        file_path = current_dir / file_name
                        if not dry_run and not file_path.exists():
                            meta = DocumentMetadata(
                                file_name=file_name,
                                description=doc.get("desc", ""),
                                tags=doc.get("tags", "").replace("[", "").replace("]", "").split(","),
                                category=dir_name,
                                status="reserved",
                            )
                            content = engine.render_template("reserved_document", {
                                "category": dir_name,
                                "file_name": file_name,
                            })
                            engine.save_document(content, str(file_path), metadata=meta)
                        created.append(str(current_dir / file_name))
                        doc_list_for_readme.append({
                            "name": file_name,
                            "description": doc.get("desc", ""),
                            "tags": doc.get("tags", ""),
                        })

                    if doc_list_for_readme:
                        readme_path = current_dir / "README.md"
                        if not dry_run and not readme_path.exists():
                            readme_content = engine.generate_readme_document(
                                dir_name=dir_name,
                                dir_description=config.get("description", ""),
                                doc_list=doc_list_for_readme,
                            )
                            readme_meta = DocumentMetadata(
                                file_name="README.md",
                                description=f"{dir_name} 目录索引",
                                category=dir_name,
                            )
                            engine.save_document(readme_content, str(readme_path), metadata=readme_meta)
                        created.append(str(readme_path))

                subcats = config.get("subcategories", {})
                if subcats:
                    _walk_structure(subcats, current_dir)

        _walk_structure(self.PROJECT_STRUCTURE, root)
        return created


def cmd_generate(args):
    config_file = args.config or ""
    if config_file and not os.path.isabs(config_file):
        config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), config_file)

    engine = YYC3TemplateEngine(args.output, config_path=config_file)

    if args.skeleton:
        structure = DocumentProjectStructure()
        files = structure.generate_skeleton(args.output, engine, dry_run=args.dry_run)
        if args.dry_run:
            for f in files:
                print(f"  [DRY-RUN] {f}")
        logger.info(f"骨架生成完成: {len(files)} 个文档")
        return

    if args.template:
        variables = {}
        for pair in (args.var or []):
            if '=' in pair:
                k, v = pair.split('=', 1)
                variables[k] = v
        content = engine.render_template(args.template, variables)
        output = args.file or f"output_{args.template}.md"
        meta = DocumentMetadata(
            file_name=os.path.basename(output),
            description=variables.get("doc_description", ""),
            tags=variables.get("tags", "").split(",") if variables.get("tags") else [],
        )
        engine.save_document(content, os.path.join(args.output, output), metadata=meta)
        logger.info(f"文档已生成: {output}")


def cmd_validate(args):
    config_file = args.config or ""
    if config_file and not os.path.isabs(config_file):
        config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), config_file)

    engine = YYC3TemplateEngine(args.output, config_path=config_file)

    if args.file:
        ok, errs = engine.validate_file(args.file)
        if ok:
            print(f"✅ {args.file}: 验证通过")
        else:
            print(f"❌ {args.file}: 验证失败")
            for e in errs:
                print(f"   - {e}")
        return

    results = engine.batch_validate(args.output)
    passed = sum(1 for ok, _ in results.values() if ok)
    failed = len(results) - passed
    print(f"\n验证完成: {passed} 通过, {failed} 失败, 共 {len(results)} 个文档\n")
    for path, (ok, errs) in results.items():
        status = "✅" if ok else "❌"
        print(f"  {status} {path}")
        for e in errs:
            print(f"     - {e}")


def cmd_export(args):
    config_file = args.config or ""
    if config_file and not os.path.isabs(config_file):
        config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), config_file)

    engine = YYC3TemplateEngine(args.output, config_path=config_file)
    output_path = args.file or str(engine.output_dir / "document_registry.json")
    engine.export_registry(output_path)
    print(f"注册表已导出: {output_path}")


def cmd_trace(args):
    registry_path = Path(args.output) / ".registry.json"
    if not registry_path.exists():
        print("未找到注册表，请先生成文档")
        return
    with open(registry_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    chain = data.get("traceability_chain", [])
    if not chain:
        print("追溯链为空")
        return
    print(f"\n追溯链 ({len(chain)} 条记录):\n")
    print(f"{'时间':<22} {'操作':<10} {'文档':<30} {'版本':<12} {'变更摘要'}")
    print("-" * 100)
    for rec in chain:
        ts = rec.get("timestamp", "")[:19]
        action = rec.get("action", "")
        doc = rec.get("document", "")
        ver = rec.get("version", "")
        diff = rec.get("diff_summary", "")
        print(f"{ts:<22} {action:<10} {doc:<30} {ver:<12} {diff}")


def main():
    parser = argparse.ArgumentParser(
        description='YYC³文档模版引擎 - 可复用、可迭代、可追溯',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 %(prog)s generate --skeleton --output docs/
  python3 %(prog)s generate --template main_document --var doc_title=测试 --file test.md
  python3 %(prog)s validate --output docs/
  python3 %(prog)s validate --file docs/README.md
  python3 %(prog)s export --output docs/
  python3 %(prog)s trace --output docs/
        """
    )
    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    p_gen = subparsers.add_parser('generate', help='生成文档')
    p_gen.add_argument('--output', '-o', default='docs', help='输出目录')
    p_gen.add_argument('--config', '-c', default='', help='模版配置文件')
    p_gen.add_argument('--skeleton', '-s', action='store_true', help='生成完整项目文档骨架')
    p_gen.add_argument('--template', '-t', help='使用指定模版生成文档')
    p_gen.add_argument('--var', '-V', action='append', help='模版变量 key=value')
    p_gen.add_argument('--file', '-f', help='输出文件名')
    p_gen.add_argument('--dry-run', action='store_true', help='仅预览不写入')

    p_val = subparsers.add_parser('validate', help='验证文档')
    p_val.add_argument('--output', '-o', default='docs', help='文档目录')
    p_val.add_argument('--config', '-c', default='', help='模版配置文件')
    p_val.add_argument('--file', '-f', help='验证单个文件')

    p_exp = subparsers.add_parser('export', help='导出注册表')
    p_exp.add_argument('--output', '-o', default='docs', help='文档目录')
    p_exp.add_argument('--config', '-c', default='', help='模版配置文件')
    p_exp.add_argument('--file', '-f', help='输出文件路径')

    p_trc = subparsers.add_parser('trace', help='查看追溯链')
    p_trc.add_argument('--output', '-o', default='docs', help='文档目录')

    args = parser.parse_args()

    if args.command == 'generate':
        cmd_generate(args)
    elif args.command == 'validate':
        cmd_validate(args)
    elif args.command == 'export':
        cmd_export(args)
    elif args.command == 'trace':
        cmd_trace(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
