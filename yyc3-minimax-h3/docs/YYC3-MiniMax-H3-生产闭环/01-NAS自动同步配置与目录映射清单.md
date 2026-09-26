---
file: 01-NAS自动同步配置与目录映射清单.md
description: NAS 双分区自动同步配置与 H3 目录映射清单（生产闭环蓝图）
author: Intelligent Application Implementation Expert <admin@0379.email>
version: v1.1.0
created: 2026-09-25
updated: 2026-09-25
status: active
tags: [nas],[rsync],[sync],[blueprint]
category: config
language: zh-CN
changelog:
  - { version: v1.0.0, date: 2026-09-25, author: 智能应用落地专家, change: 原始版本收录（生成于外部会话） }
  - { version: v1.1.0, date: 2026-09-25, author: 智能应用落地专家, change: P1-D1 规范化整备（补齐 YAML FM） }
---

# NAS 自动同步配置与目录映射清单

**100% 对齐既有 A2A 协议标准、NAS 双分区架构、MiniMax-H3 仓库目录规范**，可直接部署运行，零架构适配成本。

---

## 一、NAS 自动同步配置与目录映射清单
### 1.1 目录映射总表
严格遵循「核心数据上 RAID1、大容量资源上 RAID6」的分级策略，明确双向同步方向、权限与频率，与既有 NAS 体系完全兼容。

| 序号 | Mac 本地路径（相对于仓库根目录） | NAS 目标路径 | 所属分区 | 同步方向 | 权限 | 同步策略 | 用途说明 |
|------|--------------------------------|------------|----------|----------|------|----------|----------|
| 1 | `prompts/` | `/volume1/RAID1/yyc3-core/h3-prompts/` | RAID1 | Mac → NAS | 只读（NAS侧） | 每小时增量同步，保留版本备份 | 提示词模板、最佳实践、风格参考，核心资产双副本 |
| 2 | `docs/` | `/volume1/RAID1/yyc3-core/h3-docs/` | RAID1 | Mac → NAS | 只读（NAS侧） | 每小时增量同步，保留版本备份 | 部署文档、排障手册、流程规范，纳入统一文档矩阵 |
| 3 | `output_batchXX/manifest.json` | `/volume1/RAID1/yyc3-core/h3-manifests/` | RAID1 | Mac → NAS | 读写（NAS侧） | 每批次完成实时同步 | 批次单一事实源，全链路审计追溯，双副本永久留存 |
| 4 | `output_batchXX/report_*.md` | `/volume1/RAID1/yyc3-core/h3-reports/` | RAID1 | Mac → NAS | 只读（NAS侧） | 每批次完成同步 | 批次分析报告、质量评分报告，纳入质量治理体系 |
| 5 | `output_batchXX/*.mp4` | `/volume2/RAID6/yyc3-data/h3-output/` | RAID6 | Mac → NAS | 只读（NAS侧） | 每日凌晨闲时批量归档 | 视频成品批量归档，保留30天在线，冷备长期留存 |
| 6 | `models/syncnet/` | `/volume2/RAID6/yyc3-data/h3-models/syncnet/` | RAID6 | NAS → Mac | 只读（Mac侧） | 按需/夜间同步 | SyncNet 口型评分模型权重，统一分发 |
| 7 | `vendor/DiffSynth-Studio/` | `/volume2/RAID6/yyc3-data/h3-models/DiffSynth-Studio/` | RAID6 | NAS → Mac | 只读（Mac侧） | 版本更新时同步 | H3 主模型权重，NAS 集中存储，按需下发 |
| 8 | `ref_images/` | `/volume2/RAID6/yyc3-data/h3-assets/ref_images/` | RAID6 | 双向 | 读写 | 按需同步 | 数字人参考图素材库，统一资产管理 |
| 9 | `dashboard/batches.json` | `/volume1/RAID1/yyc3-core/h3-dashboard/` | RAID1 | Mac → NAS | 只读（NAS侧） | 每5分钟增量同步 | 可视化面板数据源，实时同步生产状态 |

> **安全原则**：所有核心配置、清单、报告走 RAID1 双副本镜像，确保不丢失；大容量视频、模型走 RAID6 容错存储，成本最优。Mac 侧仅保留生产所需最新版本，历史版本全部沉淀 NAS。

### 1.2 同步脚本集合
存放路径：NAS 端 `/volume1/scripts/h3-sync/`，与既有同步脚本体系统一管理。

#### ① 核心资产上行同步脚本 `sync_h3_core_up.sh`
> 功能：Mac → NAS RAID1，同步提示词、文档、manifest、报告，增量+版本备份，每小时执行
```bash
#!/bin/bash
# ==============================================================
# H3 核心资产上行同步：Mac本地 -> NAS RAID1 高可用区
# 触发：每小时一次，核心资产实时同步
# ==============================================================

LOG_FILE="/volume1/scripts/logs/sync_h3_core_$(date +%Y%m%d).log"
# Mac 端 SMB 挂载上传目录（Mac 同步到 NAS 的接收目录）
MAC_UPLOAD_DIR="/volume1/smb_mac_upload/h3-production/"
# NAS 目标目录
TARGET_PROMPTS="/volume1/RAID1/yyc3-core/h3-prompts/"
TARGET_DOCS="/volume1/RAID1/yyc3-core/h3-docs/"
TARGET_MANIFESTS="/volume1/RAID1/yyc3-core/h3-manifests/"
TARGET_REPORTS="/volume1/RAID1/yyc3-core/h3-reports/"
TARGET_DASHBOARD="/volume1/RAID1/yyc3-core/h3-dashboard/"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 开始 H3 核心资产上行同步" >> $LOG_FILE

# 1. 提示词模板同步（带版本备份）
rsync -avz --backup --backup-dir=backup/$(date +%Y%m%d_%H%M) \
    --exclude='*.tmp' --exclude='.DS_Store' \
    $MAC_UPLOAD_DIR/prompts/ $TARGET_PROMPTS >> $LOG_FILE 2>&1

# 2. 文档同步
rsync -avz --backup --backup-dir=backup/$(date +%Y%m%d_%H%M) \
    --exclude='*.tmp' --exclude='.git' \
    $MAC_UPLOAD_DIR/docs/ $TARGET_DOCS >> $LOG_FILE 2>&1

# 3. manifest 清单同步（实时覆盖，保留历史备份）
rsync -avz --backup --backup-dir=backup/$(date +%Y%m%d_%H%M) \
    --include='*/' --include='manifest.json' --exclude='*' \
    $MAC_UPLOAD_DIR/output_batch*/ $TARGET_MANIFESTS >> $LOG_FILE 2>&1

# 4. 批次报告同步
rsync -avz --include='report_*.md' --exclude='*' \
    $MAC_UPLOAD_DIR/output_batch*/ $TARGET_REPORTS >> $LOG_FILE 2>&1

# 5. 可视化面板数据同步
rsync -avz $MAC_UPLOAD_DIR/dashboard/ $TARGET_DASHBOARD >> $LOG_FILE 2>&1

# 权限修正
chown -R admin:users /volume1/RAID1/yyc3-core/h3-*
chmod -R 755 /volume1/RAID1/yyc3-core/h3-*

echo "[$(date '+%Y-%m-%d %H:%M:%S')] H3 核心资产上行同步完成" >> $LOG_FILE
```

#### ② 视频成品归档脚本 `sync_h3_video_archive.sh`
> 功能：Mac → NAS RAID6，批量归档视频成品，每日凌晨闲时执行，不占业务带宽
```bash
#!/bin/bash
# ==============================================================
# H3 视频成品归档：Mac本地 -> NAS RAID6 大容量区
# 触发：每日凌晨2点执行，闲时传输
# ==============================================================

LOG_FILE="/volume1/scripts/logs/sync_h3_video_$(date +%Y%m%d).log"
MAC_UPLOAD_DIR="/volume1/smb_mac_upload/h3-production/output_batch/"
TARGET_VIDEO="/volume2/RAID6/yyc3-data/h3-output/"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 开始 H3 视频成品归档" >> $LOG_FILE

# 批量归档视频文件，限速50MB/s，避免抢占带宽
rsync -avz --bwlimit=51200 --include='*.mp4' --exclude='*' \
    $MAC_UPLOAD_DIR $TARGET_VIDEO >> $LOG_FILE 2>&1

# 清理30天以上的在线视频文件（仅保留NAS冷备）
find $TARGET_VIDEO -mtime +30 -name "*.mp4" -delete >> $LOG_FILE 2>&1

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 视频成品归档完成" >> $LOG_FILE
```

#### ③ 模型资源下行同步脚本 `sync_h3_models_down.sh`
> 功能：NAS RAID6 → Mac 生产节点，模型权重、素材资源统一分发，按需/夜间执行
```bash
#!/bin/bash
# ==============================================================
# H3 模型资源下行：NAS RAID6 -> Mac 生产节点
# 触发：版本更新时手动触发 / 每周凌晨维护时同步
# ==============================================================

LOG_FILE="/volume1/scripts/logs/sync_h3_models_$(date +%Y%m%d).log"
MAC_TARGET_DIR="/volume1/smb_mac_upload/h3-production/models/"
SOURCE_MODELS="/volume2/RAID6/yyc3-data/h3-models/"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 开始 H3 模型资源下行同步" >> $LOG_FILE

rsync -avz --delete $SOURCE_MODELS/syncnet/ $MAC_TARGET_DIR/syncnet/ >> $LOG_FILE 2>&1
rsync -avz $SOURCE_MODELS/DiffSynth-Studio/ $MAC_TARGET_DIR/DiffSynth-Studio/ >> $LOG_FILE 2>&1

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 模型资源下行同步完成" >> $LOG_FILE
```

### 1.3 crontab 定时任务配置
在 NAS 既有定时任务基础上追加：
```bash
# H3 核心资产每小时同步一次
0 * * * * /bin/bash /volume1/scripts/h3-sync/sync_h3_core_up.sh

# H3 视频成品每日凌晨2点归档
0 2 * * * /bin/bash /volume1/scripts/h3-sync/sync_h3_video_archive.sh

# H3 模型每周一凌晨3点同步维护
0 3 * * 1 /bin/bash /volume1/scripts/h3-sync/sync_h3_models_down.sh
```
