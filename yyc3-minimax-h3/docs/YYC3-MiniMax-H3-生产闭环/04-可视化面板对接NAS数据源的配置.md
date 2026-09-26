---
file: 04-可视化面板对接NAS数据源的配置.md
description: 可视化面板对接 NAS 数据源配置（P1-C2 已归一：结构与路径对齐仓库真源契约 batchesPayloadSchema）
author: Intelligent Application Implementation Expert <admin@0379.email>
version: v1.2.0
created: 2026-09-25
updated: 2026-09-26
status: active
tags: [dashboard],[nas],[config],[blueprint]
category: config
language: zh-CN
changelog:
  - { version: v1.0.0, date: 2026-09-25, author: 智能应用落地专家, change: 原始版本收录（生成于外部会话） }
  - { version: v1.1.0, date: 2026-09-25, author: 智能应用落地专家, change: P1-D1 规范化（修复腐蚀链接/清理对话残留/补齐 YAML FM） }
  - { version: v1.2.0, date: 2026-09-26, author: 智能应用落地专家, change: P1-C2 契约归一（envelope 结构/0-10 刻度/data/ 路径/生成者修正） }
---

# 可视化面板对接NAS数据源的配置

**100% 复用既有 A2A 消息基础设施、对齐 NAS 目录映射规范、匹配 H3 生产节点适配器协议**，可直接复制部署，零适配成本。

## 可视化面板对接 NAS 数据源配置说明

### 1.1 数据源架构与同步链路

完全对齐前文 NAS 目录映射规范，形成「生产端生成 → 增量同步 NAS → 多终端读取」的三级数据链路：

```
pipeline_auto ⑤' 节点（批次完成后自动触发 export_dashboard_data.py，全量幂等重建）
    ↓ 批次完成后静默刷新（失败不阻断流水线）
Mac 生产节点：dashboard/data/batches.json（envelope 结构，契约 batchesPayloadSchema）
    ↓ 每5分钟增量同步（sync_h3_core_up.sh）
NAS RAID1 高可用区：/volume1/RAID1/yyc3-core/h3-dashboard/data/batches.json
    ↓ HTTP（静态站点 / 网关代理）
Ref2VA 流水线管理面板（fetch './data/batches.json'，失败自动降级内置模拟数据）
```

- **唯一写端（P1-C2 归一）**：`scripts/pipeline-tools/export_dashboard_data.py`，由 `pipeline_auto.py` ⑤' 节点自动调用；每次运行扫描全部 `output_batch*/manifest.json` **全量重建**，天然幂等。
- **唯一契约**：envelope 结构 `{schema_version, generated_at, score_scale, batches[], top10[]}`，与 `packages/manifest-schema` 的 `batchesPayloadSchema`（zod）逐字段一致；评分统一 **0-10 刻度**（lipsync score_norm×10 或 human 1~10 直用）。
- **同步机制**：复用前文 `sync_h3_core_up.sh` 同步脚本，每 5 分钟增量同步至 NAS RAID1，双副本保障不丢失。
- **访问方式**：支持「本地静态服务模式」与「HTTP 服务模式」两种部署方式。⚠️ 浏览器 `fetch()` 仅支持 http(s)，本地模式须经静态服务提供（见 1.2.1）。

### 1.2 两种部署模式配置

#### 1.2.1 本地静态服务模式（内网快速部署）

适合内网办公、单用户使用，经本地静态服务读取 `dashboard/data/batches.json`，零外部依赖。

1. **前置条件**：本地 `dashboard/data/batches.json` 已由 export 脚本生成（或经 SMB 挂载 NAS 目录作为站点根，路径为 `/Volumes/YYC3-NAS/`）。
2. **启动静态服务**：

   ```bash
   # 站点根 = dashboard/（或将站点根指向 SMB 挂载的 NAS h3-dashboard/ 目录）
   cd dashboard && python3 -m http.server 8080
   ```

3. **面板数据源配置**（相对路径，浏览器安全策略禁止 `file://` 或 `/Volumes/...` 直接 fetch）：

   ```javascript
   // ==================== 数据源配置 ====================
   const CONFIG = {
       // 数据源：相对 dashboard/ 的 batches.json（envelope 契约）
       dataSource: "./data/batches.json",
       // 自动刷新间隔（毫秒）
       refreshInterval: 300000,  // 5分钟，与NAS同步间隔对齐
       // 默认展示批次数量
       defaultShowBatches: 20
   };
   ```

4. **验证**：浏览器打开 `http://localhost:8080/<面板>.html`，面板自动加载批次数据。

#### 1.2.2 HTTP 服务模式（多终端 / 公网访问）

适合团队共享、多终端访问、公网集成，通过 HTTP 服务暴露数据源，对齐 `api.0379.world` 网关规范。

**方案 A：NAS 端开启静态站点（推荐）**

1. 在 NAS 上创建静态站点，根目录指向 `/volume1/RAID1/yyc3-core/h3-dashboard/`。
2. 开启权限：只读，内网访问，绑定域名 `dashboard-h3.0379.world`。
3. 面板配置修改：

   ```javascript
   dataSource: "https://dashboard-h3.0379.world/data/batches.json",
   ```

**方案 B：DGX 端 Nginx 代理（复用现有网关）**

1. 在 DGX 节点 2 的 Nginx 配置中追加：

   ```nginx
   location /h3-dashboard/ {
       alias /mnt/nas/raid1-core/h3-dashboard/;
       autoindex on;
       add_header X-YYC3-Upstream "h3-dashboard";
   }
   ```

2. 面板配置修改：

   ```javascript
   dataSource: "https://api.0379.world/h3-dashboard/data/batches.json",
   ```

3. 优势：复用现有网关鉴权、限流、HTTPS 体系，无需额外服务。

### 1.3 面板核心功能与字段说明

`batches.json` 为 envelope 结构（P1-C2 归一），字段与 `batchesPayloadSchema`（zod 契约）一一对应。

**envelope 顶层**：

| 字段 | 说明 |
| ---- | ---- |
| `schema_version` | 契约版本（当前 1） |
| `generated_at` | 导出时刻 |
| `score_scale` | 评分刻度说明（0-10） |
| `batches[]` | 批次聚合数组（按批次号升序） |
| `top10[]` | 全历史最优 Top10（rank/batch/img/seed/score/tags） |

**batches[] 批次单元**：

| 字段 | 来源 | 说明 |
| ---- | ---- | ---- |
| `id` | manifest.batch | 批次标识（batchXX） |
| `time` / `ended` | started_at / ended_at | 启动/结束时间 |
| `model` / `pipeline` | model.variant / model.pipeline | NF4、PRUNED 等 / ref2va |
| `refImages` / `seeds` | records 去重计数 | 参考图数 / 种子数 |
| `success` / `failed` / `skipped` | records 状态计数 | 三态计数 |
| `avgScore` / `maxScore` | 人工分或口型分×10 | **0-10 刻度** |
| `status` | ended 是否存在 | completed / running |
| `videos[]` | SUCCESS 记录明细 | name/ref/seed/score/source/tags/video_path/gen_seconds/peak_rss_gb/av_offset |
| `defects` | 人工标签计数 | 缺陷分布（按频次降序） |
| `params` | manifest.params | height/width/num_frames/num_inference_steps/fps |
| `durationMin` | started↔ended | 批次耗时（分钟） |

### 1.4 自动刷新与一致性保障

1. **生产端更新**：批次生产完成后，pipeline_auto ⑤' 自动调用 export 脚本，全量重建本地 `dashboard/data/batches.json`。
2. **NAS 同步**：每 5 分钟增量同步一次，确保 NAS 数据延迟不超过 5 分钟。
3. **面板刷新**：默认 5 分钟自动刷新一次，与同步间隔对齐，避免无效请求。
4. **一致性校验**：面板 `fetch(..., { cache: 'no-store' })` 禁用缓存，每次拉取最新数据；加载失败自动降级内置模拟数据（永不断流，与 score_lipsync 双后端策略一致）。

### 1.5 部署验证步骤

1. 执行 `python3 scripts/pipeline-tools/export_dashboard_data.py`，确认本地 `dashboard/data/batches.json` 已更新（含全部历史批次）。
2. 手动执行一次同步脚本，确认 NAS `…/h3-dashboard/data/batches.json` 出现最新文件。
3. 打开面板，查看是否展示最新批次数据，各项指标是否正确（评分应为 0-10 刻度）。
4. 等待 5 分钟，验证自动刷新是否正常触发。

---

> 📌 关联文档：契约归一决策与废弃字段映射见 [05-batches自动生成脚本.md](./05-batches自动生成脚本.md)（P1-C2 已归一，唯一写端 export_dashboard_data.py）。
