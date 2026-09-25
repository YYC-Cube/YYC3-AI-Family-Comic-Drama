<!--
  ============================================================
  YYC³ AI Family — 人从众曌众从人
  亦师亦友亦伯乐 · 一言一语一协同
  拟人为本，AI为核，纯粹为心
  ============================================================
  Document : 91 A2A通信协议 标准规范
  Version  : v1.1.0
  Contact  : admin@0379.email
  Homepage : https://matrix.yyc3.top
  License  : Apache-2.0 · 永久开源
  ============================================================
-->

# 91 A2A 通信协议 — 全家族神经脉络

![A2A协议](https://img.shields.io/badge/A2A-通信协议-%230088cc?style=for-the-badge&logo=networkx)

> 🌹 **YYC³ AI Family** — 人从众曌众从人 · 亦师亦友亦伯乐，一言一语一协同

## 一、家族定位

```
┌──────────────────────────────────────────────┐
│ 🕸️ A2A 通信协议                             │
│ Agent-to-Agent 全家族神经脉络 ｜ 公共能力     │
│ 九层架构定位：第四层 Agent服务层（通信底座）  │
└──────────────────────────────────────────────┘
```

成员间协同的通信基石：**Redis Stream 消息队列 + Agent Card 身份卡片自动发现 + trace_id 全链路追踪 + 死信队列可靠投递**，让 8 位家人像家庭一样平等对话、异步协作。

## 二、五维五高五标五化对齐

| 维度 | 对齐项 |
| ---- | ------ |
| 五高-高可用 | 死信队列 3 次重试 + nack 回队，消息不丢失 |
| 五高-高性能 | Redis Stream 毫秒级投递，AsyncOrchestrator 多 Agent 并发 |
| 五高-高安全 | 消息级 trace_id 审计，全程可追溯；审计流独立隔离 |
| 五高-高扩展 | AgentRegistry 能力注册自动发现，新成员即插即用 |
| 五标-标准化 | 消息封套标准：message_id/from/to/type/payload/timestamp/trace_id |
| 五标-自动化 | 心跳 30s 线程 + 任务监听线程，全生命周期自动托管 |
| 五标-可视化 | get_task_status / get_online_agents 状态透明可查 |
| 五化-生态化 | capability 能力注册表支撑跨系统生态接入 |

## 三、ReAct-C 协同工作流对齐

- 全链路消息底座：Step1-9 各环节 Agent 间任务分发/结果回传均经此协议
- **C = Collaborating 落地处**：异步多 Agent 并行协作（Step4 双引擎并行）由 AsyncOrchestrator 承载

## 四、接口规范

| 组件 | 关键接口 | 说明 |
| ---- | -------- | ---- |
| 消息协议 | `build_message` / `parse_message` | 消息封套构建与解析 |
| AgentRegistry | `register` / `heartbeat` / `get_online_agents` / `get_agent_by_capability` | 身份注册·心跳·发现 |
| MessageProducer | `send_task`（写审计流） | 任务投递 |
| MessageConsumer | `poll` / `ack` / `nack` | 消费·确认·重试（3次入死信） |
| A2ABaseAgent | 心跳线程 + 任务监听线程 | 成员异步化基类 |
| AsyncOrchestrator | `submit_multi_agent_task` / `get_task_status` | 多 Agent 异步编排 |

详细参数表、错误码与调用示例见 [API.md](API.md)（错误码 YYC3-AGT-5101 消息队列连接失败）。

## 五、组件与部署映射

| 组件 | 规格 | 部署位置 |
| ---- | ---- | -------- |
| Redis | 7.x（Stream + Pub/Sub） | 节点1 |
| 消息主题 | `stream:audit:log` + 各 Agent 任务流 | 双机 |
| 心跳周期 | 30s | 全体成员 |

## 六、协同关系

- **承载对象**：全部 8 位成员 + 编排引擎 + RAG 的通信层
- **依赖关系**：BaseAgent → A2ABaseAgent 增强 → AsyncOrchestrator 编排
- **映射定位**：协-协同化主责、网-网络协同/通-互联互通主责

## 七、典型场景

- 综合报告任务：编排引擎拆解 → 多成员流并行 → 结果汇聚
- 成员下线感知：心跳超时 → get_online_agents 剔除 → 任务改派
- 审计溯源：任意消息凭 trace_id 反查全链路

## 八、AI 漫剧生产场景化对齐（YYC3-03）

| 对齐项 | 内容 |
| ------ | ---- |
| 漫剧场景定位 | 漫剧多智能体协同调度通信底座：替代原 Celery 固定 DAG，支撑「Agent 自主排产、自主优化」 |
| 参与阶段 | 全阶段贯通：任务工单流转（阶段3 提交 DGX 队列）、状态实时同步前端、审计留痕（全流程安全审计） |
| ReAct-C 映射 | Step1-9 全链消息底座；AsyncOrchestrator 支撑阶段4 多任务并行生成 |
| 绑定漫剧工具 | conductor 编排引擎、DGX 任务队列、前端状态同步、审计流 |
| 漫剧调用示例 | `orchestrator.submit_multi_agent_task("漫剧生产", {"分镜任务": storyboards, "质检规则": quality_rules})` → 各任务经 Redis Stream 分发至双 DGX，`get_task_status` 实时追踪 |

## 九、代码

见 [a2a_protocol.py](a2a_protocol.py)。

---
<p align="center">
  🌹 <b>YYC³ AI Family</b><br>
  人从众曌众从人 · 亦师亦友亦伯乐<br>
  <sub>永久开源 · 感恩前行 · <a href="https://matrix.yyc3.top">matrix.yyc3.top</a></sub>
</p>
