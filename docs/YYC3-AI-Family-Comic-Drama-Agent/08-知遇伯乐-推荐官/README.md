<!--
  ============================================================
  YYC³ AI Family — 人从众曌众从人
  亦师亦友亦伯乐 · 一言一语一协同
  拟人为本，AI为核，纯粹为心
  ============================================================
  Document : 08 知遇·伯乐 Recommender 标准规范
  Version  : v1.1.0
  Contact  : admin@0379.email
  Homepage : https://matrix.yyc3.top
  License  : Apache-2.0 · 永久开源
  ============================================================
-->

# 08 知遇·伯乐 Recommender — 推荐官 · 个性化服务

![知遇·伯乐](https://img.shields.io/badge/知遇·伯乐-推荐官-%23dc143c?style=for-the-badge&logo=heart)

> 🌹 **YYC³ AI Family** — 人从众曌众从人 · 亦师亦友亦伯乐，一言一语一协同
> 「知遇伯乐」—— 知人善任，遇见成长。

## 一、成员档案（拟人化协同架构对齐）

```
┌──────────────────────────────────────────────┐
│ 🎯 知遇·伯乐 Recommender                     │
│ 推荐官 · 个性化服务 ｜ 业务执行层             │
│ 家族角色：成长伯乐 · 信任构筑者               │
│ 九层架构定位：第八层 · AI Family层（个性化）  │
└──────────────────────────────────────────────┘
```

**核心职责**
- 用户画像构建与更新
- 个性化内容推荐
- 学习路径规划
- 体验优化建议

**💡 My管理思维融合**
- **亦伯乐**：发掘用户潜能，推荐最适合的成长路径
- **以认知信任为极致**：建立长期信任关系
- **共同成长**：随用户成长动态调整推荐策略

## 二、五维五高五标五化对齐

| 维度 | 对齐项 |
| ---- | ------ |
| 五高-高智能 | 规则引擎与轻量 LLM 混合画像建模，随交互持续进化 |
| 五高-高安全 | 画像数据本地存储（localStorage/IndexedDB），零上传零收集零追踪 |
| 五高-高性能 | nemotron-mini-4b 多实例并发，秒级画像更新 |
| 五标-标准化 | 画像7字段标准（core_tags/growth_stage/interest_preferences/interaction_style/knowledge_gaps/potential_assessment/recent_activity_summary） |
| 五标-智能化 | match_score 匹配分 + recommend_reason 推荐理由透明可解释 |
| 五化-服务化 | 画像/推荐/路径/体验四大服务闭环 |

## 三、ReAct-C 协同工作流对齐

- **Step9 用户画像更新与个性化补充**：依据本次任务更新画像（user_id≠default_user 才触发）
- **画像反哺**：画像上下文注入后续会话，实现千人千面
- 人-人力资源/效-效率提升/成-成长赋能映射：学习路径、能力提升规划主责

## 四、接口规范

| 方法 | 签名 | 说明 |
| ---- | ---- | ---- |
| `build_user_profile` | `(user_id, interaction_data, existing_profile=None) -> dict` | 画像构建与增量更新 |
| `recommend_content` | `(user_profile, candidate_contents, top_k=3) -> list` | 个性化推荐（match_score+recommend_reason） |
| `plan_growth_path` | `(user_profile, target_goal) -> str` | 成长路径规划 |
| `optimize_experience` | `(user_profile, service_feedback) -> str` | 体验优化建议 |

详细参数表、错误码与调用示例见 [API.md](API.md)。

## 五、模型与部署映射

nemotron-mini-4b-instruct ｜ 节点2 ｜ 多实例并发 ｜ 与言启千行共享轻量基座服务

## 六、协同关系

- **上游输入**：全链路执行结果 + 用户交互数据（Step9 收口）
- **下游反哺**：画像注入下次会话上下文；推荐内容联动创想灵韵生成
- **映射定位**：人-人力资源主责（人才画像与成长）、营-营销增长协同（与创想灵韵协同）、成-成长赋能/效-效率提升主责、进-渐进式披露协同

## 七、信任架构承诺（五维五高五标五化）

对齐「纯开源→本地化→一用户一端→极致信任」：画像完全本地化存储，用户拥有导入/导出/删除/重置完全主权，无 Cookie、无指纹、无会话 ID 追踪。

## 八、典型场景

- 新用户首交互 → 冷启动画像构建 → 个性化内容推荐
- 老用户增量更新画像 → 技能成长路径规划
- 服务反馈收集 → 体验优化建议闭环

## 十、AI 漫剧生产场景化对齐（YYC3-03）

| 对齐项 | 内容 |
| ------ | ---- |
| 漫剧专属角色 | **产能资源管理者** |
| 漫剧核心职责 | 生产产能评估、任务分工匹配；生产进度追踪、交付风险预警；团队效能分析、产能优化建议 |
| 参与阶段 | 阶段6 运营闭环（主责：产能与交付效率统计 → 流程优化点 → 资产沉淀登记为新 Skill） |
| ReAct-C 映射 | Step9 用户画像更新与个性化补充（漫剧场景=产能画像+效能反哺） |
| 绑定漫剧工具 | 项目进度数据、资源监控数据、效能分析模型、用户画像库 |
| 网关能力 | 监控数据、效能分析模型 |
| 漫剧调用示例 | `agent.build_user_profile(user_id="project_fenglin", interaction_data="本月完赛3集/平均周期4.2天/重绘率18%", existing_profile=last_profile)` → 产能画像更新，反哺元启天枢排期决策 |

## 十一、代码

见 [zhiyu_bole_agent.py](zhiyu_bole_agent.py)。

---
<p align="center">
  🌹 <b>YYC³ AI Family</b><br>
  人从众曌众从人 · 亦师亦友亦伯乐<br>
  <sub>永久开源 · 感恩前行 · <a href="https://matrix.yyc3.top">matrix.yyc3.top</a></sub>
</p>
