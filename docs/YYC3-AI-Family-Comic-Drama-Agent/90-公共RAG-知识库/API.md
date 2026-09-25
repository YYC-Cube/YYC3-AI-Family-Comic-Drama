# 90 公共 RAG 知识库 接口文档

> 版本 v1.0.0 | 更新 2026-09-24 | 代码 [milvus_retriever.py](milvus_retriever.py)
> 示例前提：所有代码文件位于同一 Python 包目录；环境变量 `MILVUS_HOST/PORT`、`DGX1_EMBED_URL` 已配置

## 一、接口清单

| 接口名称 | 签名 | 功能简述 |
| -------- | ---- | -------- |
| `__init__` | `()` | 连接 Milvus + 嵌入服务，集合不存在自动创建 |
| `get_embedding` | `(text) -> list` | 文本向量化（2048维） |
| `insert_documents` | `(docs) -> None` | 批量入库 |
| `search` | `(query, top_k=5, category_filter=None, min_score=0.6) -> list` | 语义检索（Step3） |
| `delete_by_source` | `(source_name) -> None` | 按来源删除 |
| `batch_import_from_nas` | `(retriever, nas_path, category) -> None` | NAS 批量入库（模块级函数） |

## 二、接口详情

### 2.1 `__init__` — 初始化检索引擎

**功能描述**：连接 Milvus（DGX1 查询节点）与 nemotron-3-embed-1b 嵌入服务；`yyc3_knowledge_base` 集合不存在时按标准 Schema 自动创建（IVF_FLAT/COSINE/nlist=1024）。

**请求参数**：无（读取环境变量）

**错误码**：YYC3-AGT-5001（Milvus/嵌入服务不可达，抛出连接异常）

**调用示例**：

```python
from milvus_retriever import MilvusRetriever

retriever = MilvusRetriever()
# 预期控制台：[Milvus] 知识库集合 yyc3_knowledge_base 初始化完成
# （集合已存在时无输出，直接加载）
```

### 2.2 `insert_documents` — 批量入库

**请求参数**：

| 参数名 | 类型 | 必填 | 描述 |
| ------ | ---- | ---- | ---- |
| docs | list[dict] | 是 | 元素必填 `content`；选填 `source`（默认unknown）/ `category`（默认general）/ `create_time` |

**返回参数**：无（副作用：向量写入集合并 flush）

**调用示例**：

```python
retriever.insert_documents([
    {"content": "2026年Q2营收同比增长32%，云业务占比65%",
     "source": "2026Q2经营报告.pdf", "category": "经营", "create_time": "2026-07-01"},
])
# 预期控制台：[Milvus] 成功插入 1 条文档
```

### 2.3 `search` — 语义检索

**功能描述**：查询向量化 → Milvus 相似检索（nprobe=32）→ 元数据过滤 → 低分过滤，返回带来源的结果（供格物·宗师溯源）。

**请求参数**：

| 参数名 | 类型 | 必填 | 描述 |
| ------ | ---- | ---- | ---- |
| query | str | 是 | 查询文本 |
| top_k | int | 否 | 返回条数，默认5 |
| category_filter | str | 否 | 按分类过滤（经营/技术/管理） |
| min_score | float | 否 | 相似度红线，默认0.6（低于不入结果） |

**返回参数**：list[dict]，元素含 `content` / `source` / `category` / `score`（保留4位小数）

**错误码**：YYC3-AGT-5001（连接失败）

**调用示例**：

```python
# 场景1：通用检索
docs = retriever.search("本季度营收情况怎么样", top_k=3)
for d in docs:
    print(f"相似度{d['score']} | 来源：{d['source']}")
# 预期输出：
#   相似度0.87 | 来源：2026Q2经营报告.pdf
#   [Milvus检索] 命中 1 条相关文档（阈值0.6）

# 场景2：分类过滤检索
docs2 = retriever.search("研发人员扩张情况", top_k=3, category_filter="管理")
```

### 2.4 `delete_by_source` — 按来源删除

**请求参数**：`source_name`（str，必填，来源文件名）

**调用示例**：

```python
retriever.delete_by_source("2026Q2经营报告.pdf")
# 预期控制台：[Milvus] 已删除来源为 2026Q2经营报告.pdf 的所有文档
```

### 2.5 `batch_import_from_nas` — NAS 批量入库

**功能描述**：定时从 NAS RAID6 目录读取 `.txt/.md`，按空行分块（>50字符），批量入库（自动化更新链路）。

**请求参数**：

| 参数名 | 类型 | 必填 | 描述 |
| ------ | ---- | ---- | ---- |
| retriever | MilvusRetriever | 是 | 检索引擎实例 |
| nas_path | str | 否 | NAS 目录，默认 `/mnt/nas/raid6-knowledge` |
| category | str | 否 | 分类标签，默认「经营」 |

**调用示例**：

```python
from milvus_retriever import batch_import_from_nas

batch_import_from_nas(retriever, category="技术")
# 预期控制台：批量入库完成，共N个文本块
```

**错误码**：YYC3-AGT-4001（目录不存在抛 FileNotFoundError）

---

*© 2025-2026 YYC³ Team. All Rights Reserved.*
