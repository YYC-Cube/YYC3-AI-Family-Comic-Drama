---
file: Mac-M4-Max-128GB-MiniMax-H3-NF4完整部署脚本.md
description: MiniMax-H3 部署源文档（已归档，被 docs/01 取代）
author: YanYuCloudCube Team <admin@0379.email>
version: v1.0.0
created: 2026-09-02
updated: 2026-09-03
status: deprecated
tags: [legacy],[archive]
category: general
language: zh-CN
---

# Mac M4 Max 128GB｜MiniMax-H3-NF4 完整部署脚本（macOS Tahoe）
>
> 针对你的机器优化：128GB统一内存，**不需要磁盘offload**，vram_config简化，全部`cuda`替换为`mps`，环境用Miniforge（Apple Silicon首选）
> 全程终端执行，推荐外接电源，关闭PR/AE/大型浏览器，预留内存。

## 前置准备（一次性执行）

### 1. 安装Xcode命令行工具

```bash
xcode-select --install
```

弹出窗口点安装，如已装会提示，忽略即可。

### 2. 安装Miniforge（M系列芯片conda，不要用原版Anaconda）

下载地址：<https://github.com/conda-forge/miniforge/releases>
选择：`Miniforge3-MacOSX-arm64.sh`

```bash
# 安装
bash Miniforge3-MacOSX-arm64.sh
# 重启终端，然后创建独立环境
conda create -n h3-m4 python=3.11
conda activate h3-m4
```

### 3. 安装PyTorch（带原生MPS支持，mac官方稳定版）

```bash
pip3 install torch torchvision torchaudio
# 验证MPS是否生效，执行下面这条，返回True即为成功
python -c "import torch; print(torch.backends.mps.is_available())"
```

### 4. 拉取DiffSynth-Studio源码并安装全量依赖

```bash
git clone https://github.com/modelscope/DiffSynth-Studio.git
cd DiffSynth-Studio
pip install -e ".[all]"
```

> 这个命令会一次性装好 modelscope、bitsandbytes、ffmpeg、PIL、accelerate 全部依赖。

---

# ✅ M4 Max 优化版 FL2VA 推理脚本（文生音视频，推荐首选）
>
> 你的128G内存不需要磁盘卸载，我修改了vram_config，去掉disk offload，直接MPS加载，速度更快
新建文件 `h3_m4_fl2va.py`，复制下面全部代码：

```python
import torch
from diffsynth.pipelines.minimax_h3_audio_video import MiniMaxH3Pipeline, ModelConfig
from diffsynth.utils.data.audio_video import write_video_audio
from PIL import Image

# ========= M4 Max 128GB 优化配置 =========
vram_config = {
    "offload_dtype": "cpu",
    "offload_device": "cpu",
    "onload_dtype": torch.bfloat16,
    "onload_device": "mps",
    "preparing_dtype": torch.bfloat16,
    "preparing_device": "mps",
    "computation_dtype": torch.bfloat16,
    "computation_device": "mps",
}

pipe = MiniMaxH3Pipeline.from_pretrained(
    torch_dtype=torch.bfloat16,
    device="mps",
    model_configs=[
        ModelConfig(model_id="DiffSynth-Studio/MiniMax-H3-NF4", origin_file_pattern="minimax-h3-fl2va-nf4.safetensors", **vram_config),
        ModelConfig(model_id="DiffSynth-Studio/MiniMax-H3-NF4", origin_file_pattern="minimax-h3-text-encoder-nf4.safetensors", **vram_config),
        ModelConfig(model_id="DiffSynth-Studio/MiniMax-H3-NF4", origin_file_pattern="video_vae_nf4.safetensors", **vram_config),
        ModelConfig(model_id="DiffSynth-Studio/MiniMax-H3-NF4", origin_file_pattern="audio_vae_nf4.safetensors", **vram_config),
    ],
    processor_config=ModelConfig(model_id="MiniMax/MiniMax-H3", origin_file_pattern="FL2VA/processor/"),
    vram_limit=96, # 统一内存预留，128G设置96，留出系统内存
)

# 修改你的提示词
prompt = "A girl is very happy, she is speaking in english: “I enjoy working with Diffsynth-Studio, it's a perfect framework.”"
video, audio = pipe(
    prompt=prompt,
    height=480, width=832, num_frames=124, num_inference_steps=50, seed=0,
)
write_video_audio(
    video=video, audio=audio,
    output_path="h3_m4_output.mp4", fps=24, audio_sample_rate=32000,
)
print("✅ 视频生成完成，输出文件：h3_m4_output.mp4")
```

## 运行命令

```bash
python h3_m4_fl2va.py
```

> 第一次运行会自动从Modelscope下载全部模型文件（约72.5GB），耐心等待；后续运行直接读取本地缓存，不再重复下载。

---

# 📌 Ref2VA 版本脚本（图/视频/音频参考模式，数字人口型、素材编辑）

如果你要做**参考图+提示词生成带口型说话视频**，使用这个脚本：新建 `h3_m4_ref2va.py`

```python
import torch
from PIL import Image
from diffsynth.pipelines.minimax_h3_audio_video import MiniMaxH3Pipeline, ModelConfig
from diffsynth.utils.data.audio_video import write_video_audio
from modelscope import dataset_snapshot_download

def align_frame_count(frame_count):
    current = max(int(frame_count), 1)
    while current % 17 != 5:
        current += 1
    return current

# ========= M4 Max 128GB 优化配置 =========
vram_config = {
    "offload_dtype": "cpu",
    "offload_device": "cpu",
    "onload_dtype": torch.bfloat16,
    "onload_device": "mps",
    "preparing_dtype": torch.bfloat16,
    "preparing_device": "mps",
    "computation_dtype": torch.bfloat16,
    "computation_device": "mps",
}

pipe = MiniMaxH3Pipeline.from_pretrained(
    torch_dtype=torch.bfloat16,
    device="mps",
    model_configs=[
        ModelConfig(model_id="DiffSynth-Studio/MiniMax-H3-NF4", origin_file_pattern="minimax-h3-ref2va-nf4.safetensors", **vram_config),
        ModelConfig(model_id="DiffSynth-Studio/MiniMax-H3-NF4", origin_file_pattern="minimax-h3-text-encoder-nf4.safetensors", **vram_config),
        ModelConfig(model_id="DiffSynth-Studio/MiniMax-H3-NF4", origin_file_pattern="video_vae_nf4.safetensors", **vram_config),
        ModelConfig(model_id="DiffSynth-Studio/MiniMax-H3-NF4", origin_file_pattern="audio_vae_nf4.safetensors", **vram_config),
    ],
    processor_config=ModelConfig(model_id="MiniMax/MiniMax-H3", origin_file_pattern="Ref2VA/processor/"),
    vram_limit=96,
)

# 下载示例参考素材
dataset_snapshot_download(dataset_id="DiffSynth-Studio/diffsynth_example_dataset", local_dir="data/diffsynth_example_dataset", allow_file_pattern="minimax_h3/MiniMax-H3-Ref2VA/*")
ref_image = Image.open("data/diffsynth_example_dataset/minimax_h3/MiniMax-H3-Ref2VA/0.png").convert("RGB")

prompt = "写实人像，年轻女性，自然口型同步说话，柔和自然光，稳定镜头"
video, audio = pipe(
    prompt=prompt,
    height=480, width=832, num_frames=124, num_inference_steps=50, seed=42,
    references=[{"type": "image", "image": ref_image}]
)
write_video_audio(
    video=video, audio=audio,
    output_path="ref2va_m4_output.mp4", fps=24, audio_sample_rate=32000,
)
print("✅ Ref2VA 视频生成完成 ref2va_m4_output.mp4")
```

运行：

```bash
python h3_m4_ref2va.py
```

---

# ⚙️ Pruned精简版（20B，推理更快，画质略降）

只需要修改model_configs里这一行：
`minimax-h3-fl2va-nf4.safetensors` → `minimax-h3-fl2va-pruned-nf4.safetensors`
其余代码完全不变，适合快速迭代测试。

# ⚠️ Mac M4 重要避坑清单

1. **内存管理**：mac统一内存共享，生成视频时尽量关闭Chrome、Final Cut等大内存软件
2. **散热**：M4 Max长时间推理风扇会满载，垫高底部，不要放在床上/软垫上
3. **bitsandbytes**：M系列新版macOS原生支持NF4量化，如果报bitsandbytes错误，执行：

```bash
conda install -c conda-forge bitsandbytes
```

1. **模型缓存位置**：默认在`~/.modelscope/`，72GB，确保硬盘剩余空间>100GB
2. 帧限制：Ref2VA模式帧数必须满足 `num_frames %17 ==5`，推荐124帧（官方默认）

# 🚀 进阶：LoRA微调脚本（你的128G可以直接跑，不需要两阶段拆分）

如果你后续想训练人物/风格LoRA，我可以单独给你M4 Max优化后的accelerate训练脚本。

---

# 常见报错快速排查

1. MPS not available：检查PyTorch版本，必须>=2.4，重装torch
2. safetensors读取失败：网络中断导致模型下载不全，删除`~/.modelscope`文件夹，重新运行脚本自动重下
3. ffmpeg相关报错：`conda install ffmpeg`

需要我再补充一份**提示词模板（适合H3口型同步数字人）**，直接复制进prompt就能用吗？
---

## 变更历史

| 版本   | 日期       | 变更内容 | 作者 |
| ------ | ---------- | -------- | ---- |
| v1.0.1 | 2026-09-03 | 补齐 YYC3 品牌标尾与变更历史（文档规范审计） | Impl Expert |
| v1.0.0 | 2026-09-02 | 初始版本 | YanYuCloudCube Team |

---

<div align="center">

> 「***YanYuCloudCube***」
> 「***<admin@0379.email>***」
> 「***Words Initiate Quadrants, Language Serves as Core for the Future***」
> 「***All things converge in cloud pivot; Deep stacks ignite a new era of intelligence***」

**© 2025-2026 YanYuCloudCube™. All Rights Reserved.**

</div>
