# 04 创想·灵韵 接口文档

> 版本 v1.0.0 | 更新 2026-09-24 | 代码 [chuangxiang_lingyun_agent.py](chuangxiang_lingyun_agent.py) | 继承 [BaseAgent](../00-公共基座/API.md)
> 示例前提：所有代码文件位于同一 Python 包目录

## 一、接口清单

| 接口名称 | 签名 | 功能简述 |
| -------- | ---- | -------- |
| `polish_report` | `(raw_content, style="商务正式", audience="管理层", knowledge_context=[]) -> str` | 报告润色（Step5） |
| `brainstorm_ideas` | `(topic, direction_count=3, industry="科技行业", knowledge_context=[]) -> list` | 创意头脑风暴 |
| `generate_marketing_copy` | `(product_info, scene="公众号推文", tone="专业可信", knowledge_context=[]) -> str` | 营销文案生成 |
| `visualization_suggestion` | `(data_content, chart_type="自动推荐") -> dict` | 可视化建议 |

## 二、接口详情

### 2.1 `polish_report` — 报告润色

**功能描述**：将分析原始内容优化为专业文档：语言表达、结构层级、核心结论突出，并附「可视化建议」板块。

**请求参数**：

| 参数名 | 类型 | 必填 | 描述 |
| ------ | ---- | ---- | ---- |
| raw_content | str | 是 | 原始内容（语枢/预见输出） |
| style | str | 否 | 风格：商务正式/简洁明快/技术细节，默认商务正式 |
| audience | str | 否 | 受众：管理层/全员/客户/技术团队，默认管理层 |
| knowledge_context | list[str] | 否 | 品牌规范与文档规范参考 |

**返回参数**：

| 参数名 | 类型 | 描述 |
| ------ | ---- | ---- |
| （返回值） | str | 润色后报告（含可视化建议板块） |

**调用示例**：

```python
from chuangxiang_lingyun_agent import ChuangXiangLingYunAgent

muse = ChuangXiangLingYunAgent()
report = muse.polish_report(
    raw_content="Q2营收同比增长32%，云业务占比65%，企业客户增速最快。",
    style="商务正式",
    audience="管理层",
    knowledge_context=["[来源：品牌规范v3.docx] 报告需含执行摘要与数据图表建议"],
)
```

预期返回：

```text
【执行摘要】本季度营收同比增长32%...
一、核心经营数据解读...
📊 可视化建议：营收趋势用组合柱线图，业务占比用环形图，
   主色采用品牌蓝#1E5EFF，突出企业客户增长曲线...
```

### 2.2 `brainstorm_ideas` — 创意头脑风暴

**功能描述**：围绕主题产出差异化创意方向，强制覆盖「保守稳妥/创新突破/跨界融合」三路径。

**请求参数**：

| 参数名 | 类型 | 必填 | 描述 |
| ------ | ---- | ---- | ---- |
| topic | str | 是 | 创意主题 |
| direction_count | int | 否 | 产出方向数量，默认3 |
| industry | str | 否 | 所属行业，默认科技行业 |
| knowledge_context | list[str] | 否 | 过往案例与品牌资料 |

**返回参数**：

| 参数名 | 类型 | 描述 |
| ------ | ---- | ---- |
| （返回值） | list[dict] | 元素含 `name`/`idea`/`highlight`/`expectation` |

**错误码**：YYC3-AGT-4003（非JSON时兜底为单元素数组）

**调用示例**：

```python
ideas = muse.brainstorm_ideas("AI漫剧产品Q4营销方案", direction_count=3)
for i in ideas:
    print(i["name"], "-", i["highlight"])
```

预期返回：

```text
稳进计划 - 复用成熟渠道投放，ROI可测
破圈计划 - 联名二次创作大赛引爆UGC
跨界计划 - 与动漫IP平台联合会员体系
```

### 2.3 `generate_marketing_copy` — 营销文案

**功能描述**：按渠道与调性生成营销内容。

**请求参数**：

| 参数名 | 类型 | 必填 | 描述 |
| ------ | ---- | ---- | ---- |
| product_info | str | 是 | 产品/活动信息 |
| scene | str | 否 | 公众号推文/海报文案/邮件营销/短视频脚本 |
| tone | str | 否 | 专业可信/活泼亲切/高端质感 |
| knowledge_context | list[str] | 否 | 品牌资料参考 |

**调用示例**：

```python
copy = muse.generate_marketing_copy(
    product_info="YYC³ AI漫剧创作平台，3分钟生成漫剧短片",
    scene="短视频脚本", tone="活泼亲切")
```

预期返回：分镜脚本文本（含口播文案、字幕与行动号召）

### 2.4 `visualization_suggestion` — 可视化建议

**请求参数**：

| 参数名 | 类型 | 必填 | 描述 |
| ------ | ---- | ---- | ---- |
| data_content | str | 是 | 数据内容描述 |
| chart_type | str | 否 | 优先推荐图表类型，默认自动推荐 |

**返回参数**：

| 参数名 | 类型 | 描述 |
| ------ | ---- | ---- |
| recommended_chart | str | 推荐图表类型 |
| layout | str | 布局建议 |
| color_scheme | str | 配色方案 |
| key_points | list | 需突出的核心数据点 |
| design_tips | str | 设计注意事项 |

**错误码**：YYC3-AGT-4003（非JSON时兜底 `{recommended_chart: 组合图表, design_tips: 原文}`）

**调用示例**：

```python
sug = muse.visualization_suggestion("近6期营收：120/135/150/168/192/220")
print(sug["recommended_chart"])
```

预期返回：`趋势折线图（含同比增速副轴）`

---

*© 2025-2026 YYC³ Team. All Rights Reserved.*
