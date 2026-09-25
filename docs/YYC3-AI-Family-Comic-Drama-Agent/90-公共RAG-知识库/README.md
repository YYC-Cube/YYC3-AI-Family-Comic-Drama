<!--
  ============================================================
  YYC³ AI Family — 人从众曌众从人
  亦师亦友亦伯乐 · 一言一语一协同
  拟人为本，AI为核，纯粹为心
  ============================================================
  Document : 90 公共RAG知识库 标准规范
  Version  : v1.1.0
  Contact  : admin@0379.email
  Homepage : https://matrix.yyc3.top
  License  : Apache-2.0 · 永久开源
  ============================================================
-->

# 90 公共 RAG 知识库 — 全家族共享记忆中枢

![公共RAG](https://img.shields.io/badge/公共RAG-知识库-%231e2b4f?style=for-the-badge&logo=database)

> 🌹 **YYC³ AI Family** — 人从众曌众从人 · 亦师亦友亦伯乐，一言一语一协同

## 一、家族定位

```
┌──────────────────────────────────────────────┐
│ 🗄️ 公共RAG知识库                             │
│ 全家族共享记忆中枢 ｜ 公共能力                 │
│ 九层架构定位：第五/六层支撑（知识供给）        │
└──────────────────────────────────────────────┘
```

全体成员共享的企业知识记忆：** nemotron-3-embed-1b（2048维）向量化 + Milvus 2.4.5 检索 + llama-nemotron-rerank-1b-v2 精排 + nemotron-ocr-v2 文档解析**，从机制上降低幻觉、支撑溯源。

## 二、五维五高五标五化对齐

| 维度 | 对齐项 |
| ---- | ------ |
| 五高-高性能 | IVF_FLAT + COSINE，nlist=1024，Top-K 毫秒级召回 |
| 五高-高安全 | 知识库冷存储落 NAS RAID6，配置与审计日志落 RAID1；min_score=0.6 相关性红线 |
| 五高-高可用 | 检索失败自动降级为无 RAG 直答，链路不中断 |
| 五高-高扩展 | 集合 schema 6字段标准（id/content/embedding/source/category/create_time），按 category 平滑扩容 |
| 五标-标准化 | 统一索引类型/度量方式/top_k 参数族 |
| 五标-智能化 | rerank 精排二阶段检索，相关性红线过滤 |
| 五化-数字化 | NAS 知识资产数字化入库（batch_import_from_nas） |

## 三、ReAct-C 协同工作流对齐

- **Step3 知识检索与上下文注入**：`[来源：xxx]` 前缀格式注入全体成员 context
- 供给对象：语枢万物（分析）、预见先知（行业上下文）、创想灵韵（素材）等全成员

## 四、接口规范

| 方法 | 签名 | 说明 |
| ---- | ---- | ---- |
| `insert_documents` | `(documents) -> dict` | 文档向量化入库（自动 embedding） |
| `search` | `(query, top_k=3, min_score=0.6) -> list` | 语义检索（相关性红线过滤） |
| `delete_by_source` | `(source) -> dict` | 按来源删除重建 |
| `batch_import_from_nas` | `(nas_dir, category) -> dict` | NAS 目录批量导入 |

详细参数表、错误码与调用示例见 [API.md](API.md)（错误码 YYC3-AGT-5001 向量库连接失败）。

## 五、组件与部署映射

| 组件 | 版本/规格 | 部署位置 |
| ---- | ---------- | -------- |
| Milvus 向量库 | 2.4.5（IVF_FLAT/COSINE/nlist=1024） | 节点1 |
| Embedding | nemotron-3-embed-1b（2048维） | 节点1 |
| Rerank 精排 | llama-nemotron-rerank-1b-v2 | 节点1 |
| OCR 解析 | nemotron-ocr-v2 | 节点1 |
| 冷存储 | NAS RAID6 大容量池 | 群晖 NAS |

## 六、协同关系

- **上游供给**：Step3 统一检索入口，向九步闭环全成员注入知识
- **数据闭环**：NAS 文档 → batch_import → 检索 → 格物宗师溯源核查
- **映射定位**：知-知识学习/学-持续进化主责、库-知识库沉淀主责

## 七、典型场景

- 企业经营文档批量入库（NAS 目录一键导入）
- 言启千行 need_rag=true 时的 Step3 上下文注入
- 格物宗师依据 source 字段溯源核查事实断言

## 八、AI 漫剧生产场景化对齐（YYC3-03）

| 对齐项 | 内容 |
| ------ | ---- |
| 漫剧场景定位 | 漫剧生产知识资产中枢：题材规范/历史剧本/分镜规则/角色 LoRA 元数据统一向量化入库 |
| 参与阶段 | 阶段1 创意立项（题材规范检索）/ 阶段2 剧本分镜（历史剧本+分镜规则库检索） |
| ReAct-C 映射 | Step3 知识检索与上下文注入 |
| 绑定漫剧工具 | NAS 资产层（LoRA/素材/模板/音色 经 `batch_import_from_nas` 资产 Skill 化）、Embedding、RAG 知识库 |
| 漫剧调用示例 | `retriever.search("古风玄幻题材 分镜节奏规范", top_k=5)` → 注入语枢万物分镜生成上下文；`retriever.batch_import_from_nas("/NAS/漫剧资产/角色LoRA", category="lora")` |

## 九、代码

见 [milvus_retriever.py](milvus_retriever.py)。

---
<p align="center">
  🌹 <b>YYC³ AI Family</b><br>
  人从众曌众从人 · 亦师亦友亦伯乐<br>
  <sub>永久开源 · 感恩前行 · <a href="https://matrix.yyc3.top">matrix.yyc3.top</a></sub>
</p>
