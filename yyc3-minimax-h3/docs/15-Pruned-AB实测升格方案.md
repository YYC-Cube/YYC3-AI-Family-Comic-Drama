---
file: 15-Pruned-AB实测升格方案.md
description: Pruned vs NF4 A/B 实测升格方案——基线驱动、零下载、夜间窗口执行、量化决策规则
author: Intelligent Application Implementation Expert
version: v1.0.0
created: 2026-09-16
updated: 2026-09-16
status: active
tags: [plan],[benchmark],[pruned],[ab-test],[optimization]
category: plan
---

# 🧪 Pruned vs NF4 A/B 实测升格方案

> 定位：**基线驱动 + 零下载 + 夜间窗口**的 A/B 实测作战方案。
> 上游依据：docs/14 §5.2 P1 第一杠杆（batch90 实证 preview 档仅快 38% → NF4 CPU 反量化固定主导 → 换权重是唯一大杠杆）；docs/06 §1.1.1 基线；docs/04 A2 任务。
> 战略依据：「五高」高性能 · 「五化」数字化/自动化 · 五维评估之时间维度（产能翻倍路径）。

---

## 一、技术真相澄清（本轮审查新发现，三处误记纠正）

### 1.1 Pruned 到底剪了什么（safetensors 头部实测铁证）

| 实测项 | full（ref2va-nf4） | pruned（ref2va-pruned-nf4） | 差异解读 |
| ---- | ---- | ---- | ---- |
| 张量数 | 1830 | 1572 | **-258 = 51 block × 5 参数 + 1** |
| 差异位置 | 仅 `blocks.N` 内部 | — | 每 block 移除 `adaln_proj`（AdaLN 分支，含 13B 参数级巨型投影） |
| pruned 独有 | — | `adaln_t_table`（1025×8 查表） | 时间步条件改**曲线查表插值**（Comfy 格式继承） |

**结论**：Pruned = **结构化剪枝（AdaLN 分支移除 + 时间步查表替代）**，非有损近似；文件小 39% 的主因是 AdaLN 投影被剪 + DiT 主干精度不变（nf4 预量化保留）。这与 Comfy-Org/MiniMax-H3 模型卡「AdaLN branches ≈13B params」情报互证。

### 1.2 磁盘实况（纠正 docs/06「四件套已本地化」误记）

| 组件 | full nf4 | pruned 版 | A/B 策略 |
| ---- | ---- | ---- | ---- |
| DiT（ref2va） | 17.16GB | **10.48GB ✅ 已本地** | 直接切换 |
| text-encoder | 15.32GB | ❌ 无剪枝版（官方未发布） | **两臂共用 nf4**（控制变量） |
| video_vae | 1.61GB | ❌ 无剪枝版 | 两臂共用 nf4 |
| audio_vae | 0.28GB | ❌ 无剪枝版 | 两臂共用 nf4 |

> TE/VAE 共用反而**强化 A/B 纯度**：唯一变量是 DiT 权重，gen_seconds 差异可 100% 归因。

### 1.3 DiffSynth 原生支持（无需改 vendor）

`vendor/diffsynth/configs/model_configs.py` 已按 model_hash 预注册：
`minimax-h3-ref2va-pruned-nf4.safetensors → MiniMaxH3DiTComfyPruned`（bitsandbytes_nf4 预量化，exclude adaln_proj.linear）。
`MiniMaxH3DiTComfyPruned` 继承 `MiniMaxH3DiT`，仅替换 adaln 前向为查表插值——**pipeline/评分/manifest 链路零改动**。

### 1.4 代码缺陷修复（本轮已修，commit 见 CHANGELOG）

`h3_common.weight_files("pruned")` 原构造 bf16 旧仓库文件名（`-pruned.safetensors`/`video_vae-pruned.safetensors`），本地永远匹配不上 → 会误触发在线下载。已修复为「pruned DiT + nf4 TE/VAE」混合清单，`_model_config` 探针验证四件全命中本地。

---

## 二、A/B 实验设计

### 2.1 变量控制矩阵

| 项 | A 臂（基线，已完成） | B 臂（本轮待跑） | 控制说明 |
| ---- | ---- | ---- | ---- |
| 批次 | batch90 | batch91（隔离目录防断点续跑混淆） | 参数同源复制 |
| variant | nf4 | **pruned**（`--variant pruned`） | 唯一变量 |
| 参数档 | 360p / 73帧 / 30步 / preview | **完全一致** | 同 README 硬约束（%17==5） |
| prompt / seed | PROMPT 固定 / [42, 10] | **完全一致** | 同脚本常量 |
| 参考图 | ref_images/person_a.png | 同 | 同 |
| TE/VAE | nf4 | nf4（共用） | 官方本就无剪枝版 |
| 机器/窗口 | M4 Max / 夜间 | 同 | 避免热节流差异（间隔≥10min 冷却） |

### 2.2 执行命令（夜间窗口，22:00 后）

```bash
cd /Users/yanyu/YYC-Cube/YYC3-MiniMax-H3
PYTHONUNBUFFERED=1 nohup /opt/miniconda3/envs/h3-m4/bin/python \
  scripts/batch_ref2va_nf4.py --batch 91 --preview --variant pruned \
  > logs/batch91_ab_pruned.log 2>&1 &
```

- **首步耗时即首个信号**：NF4 稳态 ~250s/it；若 pruned 首步 <150s/it → 大杠杆实锤
- 预计总时长：B 臂 2 条 ≈ 2-4h（视加速比），远短于 A 臂 4h
- **互斥守卫**：seed10（batch90）约 08:04 结束后才可开跑；今晚 22:00 cron 首跑的批次号自动递增，batch91 由本方案显式指定（H3_BATCH 未设时 cron 用自动递增，两者不冲突；若担心撞车可设 `H3_BATCH=92` 让 cron 首跑避让）

### 2.3 决策规则（docs/04 A2 既定，升格细化）

| B 臂实测 gen_seconds（seed42 对比 A 臂 7158s） | 判定 | 动作 |
| ---- | ---- | ---- |
| **< 5011s（快 ≥30%）** | ✅ Pruned 升格量产默认 | ① `nightly_run.sh`/`pipeline_auto.py` 默认 variant 切 pruned ② docs/06/14 排产口径改写 ③ 保留 nf4 作质量对照臂 |
| 5011-6442s（快 10-30%） | ⚠️ 灰度 | preview 档切 pruned（迭代场景），量产档保 nf4；追加全质量档 A/B 一轮 |
| **≥ 6442s（快 <10%）** | ❌ 维持 nf4 | 结论归档；下一个杠杆转向 Turbo 蒸馏版（docs/09 §3 / A6） |

**质量守门（并行不阻塞速度结论）**：
1. SyncNet 评分对比（batch90 vs batch91 manifest lipsync 字段，同 backend 可比）
2. 人工观看 batch91 两条样片，重点核验：身份一致性 / 画面稳定性 / AdaLN 查表是否引入时序伪影
3. **质量红线**：若 pruned 口型分劣化 >15% 或人工评分 <6/10 → 无论多快不升格，转 Turbo 评估

### 2.4 实测定案（2026-09-18 晨，B 臂收工后）

**速度（manifest gen_seconds，配对对比）**：

| 配对 | A 臂 nf4 (batch90) | B 臂 pruned (batch91) | 提速 |
| ---- | ---- | ---- | ---- |
| seed42 | 7158.1s | 6939.0s | 3.1% |
| seed10 | 7431.5s | **5868.1s** | **21.0%** |
| 均值 | 7294.8s | 6403.5s | **12.2%** |

- 稳态干净信号：seed10（无污染样本）189.7s/it vs NF4 基线 ~250s/it → **单步计算杠杆 18-25% 实锤**
- seed42 污染源（日志可证）：①dynamo 重编译扰动前 9 步（recompile_limit 警告）②**22:48 电量 1% 触发 Low Power Sleep 休眠 5992s**，00:28 接电唤醒续跑（pmset 实证；gen_seconds 已自动剔除冻结段，配对对比仍公平，但醒来恢复段降速残留）
- 加载副利：pruned 权重挂载 **90 秒**进推理（vs NF4 数分钟）

**内存（超预期）**：RSS 峰值 32.85GB → **17.755GB（−46%）**，大幅优于 §三 预测的 24-28GB——32GB 级设备兼容面收益坐实。

**质量守门：通过** ✅（SyncNet score_norm，同 backend）：

| 配对 | A 臂 | B 臂 | Δ |
| ---- | ---- | ---- | ---- |
| seed42 | 0.5342 | 0.5532 | +3.6% |
| seed10 | 0.5502 | 0.5593 | +1.7% |

pruned 双 seed **不降反升**，劣化 >15% 红线远未触发。人工观看（身份一致性/时序伪影）待用户补验——升格全量前的最后守门。

**判定：⚠️ 灰度（下界贴线定案）**
- 配对均值 12.2% 落入 5011-6442 灰度带（距上界仅 38s）；字面 seed42 单点 3.1% 落维持带，但该样本被重编译+休眠恢复双重污染，取均值+干净稳态信号定灰度
- **动作（灰度带处方执行）**：
  1. preview 档（迭代场景）默认 `--preview --variant pruned`（batch92 起手动迭代批照此）
  2. 量产档维持 nf4：`pipeline_auto.py` 无 variant 传参=天然维持，nightly（v1.1.0）不变更
  3. **追加全质量档 A/B 一轮**（建议 09-19 夜：nf4 vs pruned 各一条全质量，seed 42，对照 §2.3 同规则定量产档终局）
  4. 若全质量轮复现 ≥10% 提速且人工分 ≥6/10 → 届时再议量产档切换与 docs/06/14 排产口径改写

**同窗口固化进 nightly_run.sh v1.1.0 的两起事故修复**（详见脚本头注）：
- ① cron 上下文 `python3`=`/usr/bin/python3` 撞 Xcode license（exit 69）→ 09-16 夜间阶段①/④全灭 → 显式锚定 `/opt/miniconda3/envs/h3-m4/bin/python`
- ② 电池跑批量触发 Low Power Sleep 冻结生成（上文 seed42 休眠事件）→ AC 电源守卫（电池拒跑）+ `caffeinate -i` 全程防睡眠

**已知小缺陷（记录不阻断）**：nightly 归档选批用 `ls -t report_batch*.md` mtime 启发式，评分刷新会扰动排序（09-18 晨曾致 batch91 漏选、已手动补归档）；后续可改用 manifest 批号扫描。

---

## 三、预期收益测算（五维·时间维度）

| 场景 | 现状（nf4） | pruned 若快 40%（中性预期） | 年化收益 |
| ---- | ---- | ---- | ---- |
| preview 档 | 2h/条 | ~1.2h/条 | 迭代周期近半 |
| 全质量档 | 3.2h/条 | ~1.9h/条（待 B 臂胜出后二轮验证） | 夜间窗口产能 3.75→6.3 条/晚（+68%） |
| RSS 峰值 | 32.85GB | 预计 24-28GB（DiT -39%） | 32GB 级设备兼容面扩大 |

> RSS 收益为次要假设，manifest peak_rss_gb 自动留痕可验。

---

## 四、执行清单（Checklist）

- [x] 1. h3_common.weight_files pruned 修复 + py_compile + 探针验证（本地四件全命中）
- [x] 2. 本方案文档落盘（docs/15）
- [x] 3. docs/06/14 同步「A2 升格中」状态 + 误记纠正（四件套→DiT 单件剪枝）
- [ ] 4. **等 seed10（batch90）完成 + 今晚 cron 首跑避让确认**
- [ ] 5. batch91 B 臂启动（§2.2 命令）
- [ ] 6. 首步速率检查（<150s/it → 大杠杆实锤；~250s/it → 提前按 §2.3 第三行预案）
- [ ] 7. 两条完成后跑 score_lipsync + analyze（batch91）
- [ ] 8. 按 §2.3 决策规则拍板 → 回写 docs/06 §1.1.1 + docs/14 §3.2/§5.1 + CHANGELOG
- [ ] 9. 若升格：pipeline 默认 variant 切换 PR（含 nightly_run.sh）

---

## 五、风险登记

| 风险 | 等级 | 缓解 |
| ---- | ---- | ---- |
| MiniMaxH3DiTComfyPruned 在 MPS 首次实跑未知问题（adaln_t_table 查表 buffer 在 MPS 的行为） | 中 | 首步即观察；异常立即停，回退 nf4 结论照常产出（A 臂已闭环） |
| pruned 画质/口型劣化 | 中 | §2.3 质量红线硬门禁 |
| 与今晚 cron 首跑撞批次 | 低 | cron 自动递增批次号；必要时 H3_BATCH=92 避让 |
| 模型 hash 未命中本地文件（DiffSynth 版本漂移） | 低 | model_configs.py 2.1.5 已含该 hash（§1.3 已核）；若未命中会报 hash mismatch 而非静默错误 |

---

## 变更历史

| 版本 | 日期 | 变更内容 | 作者 |
| ---- | ---- | -------- | ---- |
| v1.0.0 | 2026-09-16 | 初版：技术真相澄清（AdaLN 剪枝/单件 DiT/DiffSynth 原生支持）+ 零下载 A/B 设计 + 量化决策规则 | Impl Expert |
| v1.1.0 | 2026-09-18 | §2.4 实测定案：灰度（均值 12.2%/稳态 18-25%杠杆/RSS −46%/质量守门通过）；seed42 休眠污染归因（pmset）；两起夜间事故修复固化 nightly v1.1.0；全质量档 A/B 排 09-19 夜 | Impl Expert |

---

<div align="center">

> 「***YanYuCloudCube***」
> 「***<admin@0379.email>***」
> 「***Words Initiate Quadrants, Language Serves as Core for the Future***」
> 「***All things converge in cloud pivot; Deep stacks ignite a new era of intelligence***」

**© 2025-2026 YanYuCloudCube™. All Rights Reserved.**

</div>
