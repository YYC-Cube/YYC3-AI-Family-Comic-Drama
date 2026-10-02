---
file: YYC3-61-AI漫剧全链路闭环生产操作指导目录.md
description: YYC³ AI 漫剧全链路闭环生产教科书级操作指导目录——基座/资产/生产/质量/验收/治理六篇二十章，结合 G1-G5 验收体系与 36 轮 HANDOFF 实际沉淀，逐节给出目标/工具/参数/口径/留证五要素
author: Intelligent Application Implementation Expert <admin@0379.email>
version: v1.0.0
created: 2026-10-02
updated: 2026-10-02
status: active
tags: [指导目录, 全链路, 闭环, 生产操作, 教科书]
category: manual
language: zh-CN
related_docs: YYC3-60-测试与验收执行手册.md,G4-样片扩产与硬件日收割记录-20260929.md,YYC3-AI-HANDOFF-会话推进日志-20260926.md,YYC3-02-AI漫剧全链路生产系统-开发者文档.md
---

# YYC³ AI 漫剧全链路闭环生产操作指导目录（教科书级）

## 阅读指南

| 属性 | 说明 |
| ---- | ---- |
| 定位 | 全链路（剧本→资产→图像→视频→音频→合成→评分→验收→归档）每一环节的操作指导入口；按目录索引即可定位到具体脚本、参数、口径与留证位置 |
| 体例 | 每节按五要素描述：**目标 / 工具 / 关键参数 / 判定口径 / 留证物** |
| 适用 | AI 导师新会话入职速览、生产执行随查、验收复跑、跨会话衔接 |
| 上位文档 | 执行手册（60）定义验收判据；本文档定义"怎么做"；HANDOFF 记录"做到哪" |

**口径基线（全文档统一，冲突时以最新留证为准）**：

| 口径 | 基线值 | 出处 |
| ---- | ------ | ---- |
| 身份一致性上线门槛 | combo 峰值 mean >= 0.85（均值口径） | M3 二轮决策 |
| 稳定度参考口径 | min（最差种子），v2 组合 0.7846 为生产基线 | M3 三轮 |
| 评测参考系 | ComfyUI/input/hero_base.png（9/27 设定图本体），纯生成图禁作跨日参考系 | 2026-10-02 参考系漂移治理 |
| 漂移种子 | 777/888/999/1111 x 512px x PORTRAIT+DRIFT_SUFFIX | M3 离线协议 |
| 静态镜采样 | 25 步 euler/normal cfg7.0 denoise1.0 | 生产 adapter 逐参 |
| IPAdapter 权重 | 弱 IPA w0.15（三轴校准实证最优） | 34.4 轴 A |
| 开发服务器端口 | 3030 起 | YYC³ 团队规范 |

---

# 第一篇 基座篇：环境与资产（对应 G1 底座通电）

## 第1章 系统全景与闭环总图

### 1.1 工业化目标与六层链路
- 目标：从小说到成片的零人工干预批量产能（3 集/晚基线），身份一致性可测量（insightface 余弦）、成本可核算（元/集）、门禁可复跑（G1-G5）。
- 六层链路：剧本分镜层 → 角色资产层 → 图像生产层 → 视频生产层 → 音频合成层 → 评分验收层。

### 1.2 全链路闭环流程图

```
小说文本
  │ run_batch_shots.py（切集 + 分镜）
  ▼
剧本/分镜 manifest ──► 角色资产层（第4-6章：设定图锚定 + LoRA）
  │
  ▼ ComfyUI :41888（IPAdapter 锚定 + seed_lock 回退）
静态镜 PNG（1024）
  │ n1 H3 图生视频（720p，seed 42/43/44）
  ▼
动态镜 MP4 ──► SyncNet 预检（run_syncnet_score.py）
  │ tts_service.py
  ▼
音频 ──► run_episode_build.sh（c1/c2 compose + c3 adapt）
  │ run_episode_concat.sh（concat-filter 等比覆盖裁切）
  ▼
成片 1080p30 ──► run_quality_review.py + run_cost_report.py
  │ anchor_guard 生产判定（mean >= 0.85）
  ▼
留证归档 docs/attachments/G4-YYYYMMDD/ ──► G5 门禁复跑 ──► HANDOFF 下一轮
```

### 1.3 文档体系地图
- 目标：任何 AI 导师 10 分钟内定位"该读哪份、该写哪份"。
- 读：00 总纲（架构）→ 60 手册（判据）→ 本目录（操作）→ G1-G5 记录（事实）→ HANDOFF（进度）。
- 写：审核报告（00-）/任务规划（01-）/执行日志（02-）/总结同步（03-），入 `docs/{项目}-{导师}-{日期}/`。

### 1.4 术语与口径基线
- 目标：消除跨会话语义漂移。
- 必知术语：sim（insightface 余弦）、combo（LoRA+IPAdapter 组合）、mean/min 双口径、漂移种子、参考系锚定、anchor_guard（生产域拒收判定）、BLOCKED（手册允许的数据缺口留证态）。

## 第2章 环境基座

### 2.1 节点拓扑与分工
- Mac M4 Max：编排、ComfyUI 图像、TTS、ffmpeg 合成、insightface 评分、gate 执行器。
- yyc3-n1（ssh 别名）：kohya LoRA 训练、H3 图生视频推理。
- n2 态势：被团队 root vLLM 大服务占据，不纳入产能规划。

### 2.2 ComfyUI 运行环境
- 工具：comfyui_guardian.sh（守护拉起）。
- 端口：:41888；环境变量 `COMFYUI_URL=http://localhost:41888`、`COMFYUI_MODEL=DreamShaper_8_pruned.safetensors`（adapter 缺省 sd_xl 会 400）。
- input/ 目录：设定图锚定区（hero_base.png 本体在位即评测可信）。
- 生成耗时基线：512px 25 步约 8-10 秒；低于 3 秒疑似节点缓存命中，须以 md5/mtime 验产物真实性。

### 2.3 n1 训练环境
- venv：/home/yyc3/venvs/kohya（Py3.10）；sd-scripts：/home/yyc3/tools/sd-scripts。
- 基模：/home/yyc3/models/yyc3h3/DreamShaper_8_pruned.safetensors。
- 离线纪律：`HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1` 必设（n1 无法直连 HF）。
- 新版 sd-scripts 口径：无 `--batch_size`（toml 化默认 1）。

### 2.4 端口与进程纪律
- 开发服务器 3030 起；网关 :8010、上游桩 :25290（G1-004 E2E 链）。
- 长跑任务一律后台 job + CheckCommandStatus 观察，禁止阻塞终端。

### 2.5 密钥红线
- 运行时读取环境变量，零入库；文档中只用 `${ENV_VAR_NAME}` 或 `[REDACTED]` 占位。
- 不盲测未验证命令；破坏性 git 操作需显式授权；不 push。

## 第3章 模型资产台账

### 3.1 基模
- DreamShaper_8_pruned.safetensors（SD15）。约束：SDXL 专属模型（InstantID/PuLID）不可用，基模迁移是独立决策项。

### 3.2 IPAdapter 家族
| 模型 | 角色 | 关键值 |
| ---- | ---- | ------ |
| PLUS FACE（ip-adapter-plus-face_sd15） | 生产在役 | w0.15，单独 mean 0.67 |
| FaceID PlusV2（ip-adapter-faceid-plusv2_sd15.bin, 156,558,509 字节 + 配套 lora 51MB） | min 稳定度备选（未接线） | fv3.0 + LoRA(v2) w0.15：mean 0.8248 / min 0.8036（全实验 min 冠军） |
| InstantID / PuLID | 不可用（SDXL 专属） | 基模迁移预研后再议 |

### 3.3 LoRA 家族
| 产物 | 角色 | 关键值 |
| ---- | ---- | ------ |
| sd-hero-v2（dim32/alpha16, 19 图） | 生产上线 | combo w0.15 mean 0.8669/0.8672（历史参考系） |
| sd-hero-v3 系（v3 数据集） | 证伪归档 | rank64/r32 全线未达标，回退主因收敛至数据集 |
| sd-hero-v2m777（v2 + 8x777 续训 540 步） | 实验归档不替换 | mean 0.8586 守线，777 种子 0.7269 反降 |

### 3.4 评分模型
- insightface（余弦 vs 参考系）；库存向量库作跨日仲裁基准（ref_calibration=1.0 为校准通过标志）。

### 3.5 资产变更纪律
- 评测先行：任何新模型先离线 4 种子评测达标，再议生产接线（drama_stage_adapter 在 archive 仓，本轮纪律未动）。
- 下载通道：hf-mirror.com（直连超时）；.bin/.safetensors 以 Content-Length 校验完整性。

---

# 第二篇 资产篇：角色一致性（对应 G3 / M3）

## 第4章 参考系锚定（评测可信度的根）

### 4.1 唯一可信参考系
- 目标：跨日可比性。工具：ComfyUI/input/hero_base.png（2026-09-27 设定图本体）。
- 口径：设定图文件逐字节稳定；与库存向量校准 1.0 方可信。

### 4.2 跨日规则（红线）
- 同 seed 纯生成图随 ComfyUI 环境更新漂移（实证 0.5675），**禁止作跨日参考系**。
- 每日设定图本体入 input/ 目录存档；缺失时回落 /tmp 必须显式告警。

### 4.3 校准与仲裁方法
- 库存向量仲裁：新参考图先与库存特征比对，sim 显著低于 1.0 即判定参考系漂移，停止一切评测结论。
- 案例模板：v2 本体重测塌至 0.5108 即首信号（达标模型不可能劣化至此）。

### 4.4 HERO 硬编码治理清单
- 已修：run_lora_plusface_combo.py（锚定本体 + /tmp 回落告警）。
- 待治理（36.4 TOP2）：run_kohya_lora.py / run_batch_shots.py / run_anchor_domain_recal.py。

## 第5章 LoRA 训练

### 5.1 数据集构建
- 工具：run_lora_dataset_v2.py / run_lora_dataset_v3.py / run_lora_pose_mining.py。
- 口径：v2 = 19 图；增量 = +8 张 777 挖掘样本（27 图混合）；无 caption 走 class token。

### 5.2 质检与上采样
- 断言：图片 >= 512，否则 "image size is small" 训练失败；384x384 用 PIL LANCZOS 上采样。

### 5.3 训练口径（n1 kohya）
- 参数：dim32/alpha16、lr 1e-4 constant AdamW、bf16 训练、save_precision fp16。
- 增量续训：`--network_weights` 指向 v2 checkpoint 起步。
- 里程碑：2 epochs = 540 步（27 图 x 10 repeats，约 1.14it/s）。
- 留证：训练日志全量归档（train_v2m777.log 模板）。

### 5.4 产物管理与校验
- safetensors keys 数校验（v2/v2m777 均 792：TE=0，UNet=576）；文件大小差异先查保存精度口径（fp16 半量属正常），勿误判结构缺失。

## 第6章 资产评测与上线判定

### 6.1 离线评测协议
- 工具：run_lora_train_eval.py / run_lora_plusface_combo.py / run_faceid_plusv2_eval.py。
- 协议：4 漂移种子 x 512 x PORTRAIT+DRIFT_SUFFIX，insightface 余弦 vs 参考系本体。

### 6.2 组合权重扫描
- 网格：LoRA weight {0.10/0.15/0.20/0.30} x IPA/fv 档位；w0.15 为历史峰值区。
- 对照纪律：必含纯 IPA 与纯 LoRA 两锚点，避免归因混淆。

### 6.3 双口径判定
- mean >= 0.85：上线门槛（G5-003 触发判定同口径）。
- min：稳定度参考（防最差帧场景选型依据，FaceID 组合 0.8036 为现行冠军）。

### 6.4 上线/替换决策规则
- 生产模型替换须同时满足：mean 超现行 + min 不回退 + 复现可验证；三者缺一即维持现役（v2m777 案例模板：mean 守线但 min 反降，不替换）。

---

# 第三篇 生产篇：从剧本到成片（对应 G4）

## 第7章 剧本与分镜

### 7.1 小说→剧本切集
- 工具：run_batch_shots.py（NOVEL 三章 + `--episode`）。
- 口径：单集 90s 窗口；章末 >= 183 字独立成集、累计 < 367 字不合并；钩子齐备。

### 7.2 分镜数据结构
- shot.description（叙事 prompt 源）+ sid（镜头稳定种子 = sid x 7 + 1000）+ 镜型（静态/动态）。

### 7.3 prompt 构造
- 生产口径：`REF_STYLE + shot.description`；构图约束后缀已证伪（-0.042），禁止回潮。

## 第8章 静态镜生产

### 8.1 生产工作流逐参表（评测须逐参镜像）
| 项 | 值 |
| -- | -- |
| 采样器 | euler / normal |
| 步数 / CFG / denoise | 25 / 7.0 / 1.0 |
| 分辨率 | 1024（512 分辨率衰减假设已证伪，勿降档） |
| 负向词 | 缺省中文串（低质量、变形、多余手指、水印） |
| CLIP 链 | checkpoint 或 LoRA 节点（节点 13 全链） |

### 8.2 IPAdapter 锚定
- 生产：PLUS FACE w0.15（轴 A 单调递减实证最优）；FaceID 分支未接线（待决策）。

### 8.3 批量执行与回退
- 工具：run_batch_shots.py（gen=ok 校验）+ seed_lock 回退（锚定失败降级纯生成）。
- 耗时基线：3 集 x 3 镜约 522-740s。

### 8.4 产物真实性验证
- md5 互异 + mtime 核对；缓存命中产物（秒级返回）须人工复核有效性。

## 第9章 动态镜生产

### 9.1 H3 提交（n1）
- 口径：720p（1280x736）、ref2va NF4、30 步、73 帧。

### 9.2 性能基线
- 冷启动 1290.8s/镜；热批 434.4s/镜（13.3s/it）；GB10 串行化纪律（rsync page cache 与 CUDA 大分配互斥）。

### 9.3 seed 变量管理
- 42/43/44 与 conf/dist 逐镜记录（9001-9003 台账模板）；新镜优先继承良好带 seed。

### 9.4 SyncNet 预检
- 工具：run_syncnet_score.py + syncnet_service.py。
- 基线：conf 6.4-6.7 良好带；dist < 9 良好带；384p 细节量不足会推高 dist（已实证）。

## 第10章 音频与合成

### 10.1 TTS
- 工具：tts_service.py；音频时长与分镜 90s 窗口对齐。

### 10.2 混排构建
- 工具：run_episode_build.sh——c1/c2 静态 compose + c3 动态 adapt。

### 10.3 ffmpeg 合成
- 工具：run_episode_concat.sh / run_dynamic_clip.sh / run_clip_compose.sh。
- 关键口径：concat-filter + 等比覆盖裁切（防 6.7% 垂直变形）。

### 10.4 成片验收
- 1080p30、单集时长窗口内、音画同步（SyncNet 复测抽样）。

---

# 第四篇 质量篇：可测量与可追溯

## 第11章 评测协议汇总
- 第二篇第 6 章口径在生产域的镜像：生产分镜 2 镜（run_anchor_domain_recal.py）+ 离线 4 种子（combo 脚本）双域同测。
- 跨日对比三步：验参考系在位 → 库存向量校准 → 当日基线重测（v2 复现历史值方开闸）。

## 第12章 anchor_guard 生产判定
### 12.1 判定口径
- 生产域 mean >= 0.85 收录；低于即拒收重roll。
### 12.2 批量护航
- 留证模板：tc-g4-006-anchor-guard-batch-3eps.txt（3 集批量护航记录）。
### 12.3 拒收处置链
- 重roll → run_style_keeper.py（风格守护）→ 升级报告（tc-g4-006-style-keeper-escalate.json 模板）。

## 第13章 成本与产能
### 13.1 成本核算
- 工具：run_cost_report.py（v1.1.1：电费折算 + Token-Console 计量接入，timeout 8s）。
- 基线：0.0168-0.0335 元/集。
### 13.2 产能统计
- manifest 聚合口径，基线 3 集/晚（tc-g4-009-nightly-batch-stats.json）。
### 13.3 反哺项启用
- 锚定域再校准 + combo 复评全量启用后，G5-002/005 一键复算（执行器已就绪）。

---

# 第五篇 验收篇：G1-G5 门禁

## 第14章 门禁总览
| Gate | 范围 | 判据锚点 |
| ---- | ---- | -------- |
| G1 | 底座通电（网关/桩/计量） | 三探针 200 语义复现；G1-004 落位 BLOCKED 待 NAS 挂载 |
| G2 | 编排贯通 | run_g2_cases.py / run_g2_final.py 十用例 |
| G3 | 一致性预研 | run_g3_cases.py 五项 |
| G4 | 样片扩产 | 门禁全量完成（010 回归集） |
| G5 | 门禁与运营 | run_g5_gate.py 六用例 |

## 第15章 执行器与复跑
### 15.1 G5 执行器口径
- TC-G5-003 三步：①触发判定（四档模型 mean 过判定器，准确率 100%/误触发 0）②增量重训（DONE，540 步留证）③复测（min >= 0.85 手册口径）。
### 15.2 诚实留证原则
- 有数据真实计算；无数据 BLOCKED；未达 FAIL 如实（gate_verdict: FAIL 不虚构）；错误期 raw 报告保留不删。
### 15.3 复跑命令与落盘

```bash
yyc3-ai-manju-studio/.venv/bin/python scripts/run_g5_gate.py \
  --out docs/attachments/G4-$(date +%Y%m%d)/tc-g5-gate-run-$(date +%Y%m%d).json
```

---

# 第六篇 治理篇：文档闭环与协同

## 第16章 文档规范落地
### 16.1 front matter 必填项
- file/description/author/version/created/updated/status/tags/category/language。
### 16.2 命名与目录
- 留证：docs/attachments/G4-YYYYMMDD/；会话目录：docs/{项目}-{导师}-{YYYYMMDD}/。
### 16.3 模板索引
- 审核报告/任务规划/执行日志/总结四模板见《YYC3-团队通用-开发文档》。

## 第17章 HANDOFF 会话推进协议
### 17.1 轮次循环
- TOP3 → 执行 → 留证 → 文档（主文档版本号 +1、HANDOFF 新章）→ 多仓提交 → 下轮 TOP3。
### 17.2 上下文衔接（新会话七步）
- 定位最新会话目录 → 读 03 总结 → 读 02 日志尾部 → 核对 01 规划 → git status/log 验证 → 建目录/续用 → 向用户确认起点。
### 17.3 口径确认
- 重复指令或歧义时先 AskUserQuestion 确认执行口径（35.4 续作案例），不盲目重复执行。

## 第18章 多仓与提交纪律
### 18.1 分工
- 主仓：scripts/ + docs/（评测、执行器、文档）。
- yyc3-ai-agent-archive：生产 adapter（drama_stage_adapter.py），评测先行纪律下未达标不动。
### 18.2 提交规范
- 中文 feat/fix(Gx) 前缀 + 摘要 + 要点列表；单轮单提交；先 git status 核对再 add 具名文件。
### 18.3 红线
- 不 push；不提交密钥；负结果与纠错必须随轮入库。

## 第19章 证伪台账与决策待办
### 19.1 已证伪清单（禁止重复投入）
| 路线 | 证伪证据 |
| ---- | -------- |
| 构图约束后缀 | 三轴校准 -0.042 |
| 分辨率衰减假设 | 512 反比 1024 低 0.095 |
| IPA 高权重窗 | w0.15 单调最优 |
| combo 生产域 | 负交互（首镜 -0.18） |
| v3 数据集 | rank64/r32 全线未达标 |
| v2m777 泛化 | 777 种子反降（同分布巩固非泛化） |
| SD15 族内 0.85 冲顶 | FaceID PlusV2 最优 0.8248 仍不达 |
| SDXL 专属模型直上 | InstantID/PuLID 与 SD15 不兼容 |

### 19.2 决策待办台账
| 项 | 内容 | 状态 |
| -- | ---- | ---- |
| FaceID 组合接线 | min 备选（0.8036）是否入 drama_stage_adapter | 待用户决策 |
| HERO 参考系统一治理 | 三脚本 /tmp 硬编码迁移 | 36.4 TOP2 |
| 基模迁移预研 | SDXL 系破局 0.85 唯一路径 | 36.4 TOP3 |
| G5-002/005 反哺复算 | 反哺项全量启用后一键复跑 | 待夜间窗口 |

### 19.3 阻塞项落位
- G1-004 落位步骤：BLOCKED 留证，待 /mnt/nas 挂载实机复验。

---

# 附录

## 附录 A 快速恢复命令卡

```bash
# 1. 进入项目并读最新总结
cd "/Users/yanyu/YYC-Cube/YYC3 AI Family-Comic Drama"
ls -t docs/YYC3-AI-HANDOFF-*.md | head -1

# 2. 验证代码状态
git status && git log --oneline -5

# 3. ComfyUI 冒烟（守护拉起后）
curl -s http://localhost:41888/system_stats

# 4. G5 门禁复跑（落盘当日留证）
yyc3-ai-manju-studio/.venv/bin/python scripts/run_g5_gate.py \
  --out docs/attachments/G4-$(date +%Y%m%d)/tc-g5-gate-run-$(date +%Y%m%d).json
```

## 附录 B 全链路参数速查表

| 环节 | 关键参数 | 判定 |
| ---- | -------- | ---- |
| 静态镜 | 25 步 euler/normal cfg7.0 1024 IPA w0.15 | gen=ok + anchor_guard |
| 动态镜 | 720p 30 步 ref2va NF4 seed 42/43/44 | SyncNet conf >= 6.4 / dist < 9 |
| 合成 | concat-filter 等比覆盖裁切 | 1080p30 无变形 |
| 评测 | 4 漂移种子 512 历史参考系 | mean >= 0.85 |
| 训练 | dim32/alpha16 lr1e-4 540 步 | keys 792 校验 |
| 成本 | 电费 + Token-Console | 0.0168-0.0335 元/集 |

## 附录 C 脚本资产索引（scripts/ 全量 38 件）

| 类别 | 脚本 |
| ---- | ---- |
| 剧本分镜 | run_batch_shots.py |
| 静态镜 | run_comfy_real.py / run_ipadapter_identity.py / comfyui_guardian.sh |
| 锚定校准 | run_anchor_domain_recal.py / run_m3_anchor.py / run_threshold_calibration.py |
| 风格守护 | run_style_keeper.py |
| LoRA | run_lora_dataset_v2.py / run_lora_dataset_v3.py / run_lora_pose_mining.py / run_kohya_lora.py / run_lora_train_eval.py / run_lora_plusface_combo.py / run_faceid_plusv2_eval.py / run_m3_av.py |
| 动态镜 | run_hardware_day.sh / run_dynamic_clip.sh |
| 音频合成 | tts_service.py / run_episode_build.sh / run_episode_concat.sh / run_clip_compose.sh |
| 质量 | syncnet_service.py / run_syncnet_score.py / run_quality_review.py / run_cost_report.py |
| 门禁 | run_g2_cases.py / run_g2_final.py / run_g2_010_dual.py / run_g3_cases.py / run_m2_closure.py / run_g5_gate.py |
| 底座 | stub_upstream.py / run_gateway_local.py / upstreams.tsv / sync-upstreams.sh |

## 附录 D 留证文件索引

| 目录 | 内容 |
| ---- | ---- |
| docs/attachments/G4-20260928/ | 首验批产 + SyncNet |
| docs/attachments/G4-20260929/ | 扩产/成本/回归/LoRA 全谱 + G5 首轮（24 件） |
| docs/attachments/G4-20261002/ | 参考系漂移 + FaceID PlusV2 + v2m777 + G5 复跑（8 件） |

## 附录 E 轮次进度索引
- HANDOFF 第二十六轮（2026-10-02）36.1-36.4 为当前断点；下轮起点以 36.4 TOP3 为准。
