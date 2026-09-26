---
file: MiniMax-H3-DiffSynth本地版-提示词模板.md
description: MiniMax-H3 提示词模板源文档（已归档，被 prompts/README 取代）
author: YanYuCloudCube Team <admin@0379.email>
version: v1.0.0
created: 2026-09-02
updated: 2026-09-03
status: deprecated
tags: [legacy],[archive]
category: general
language: zh-CN
---

# 🎤 MiniMax-H3（DiffSynth本地版）提示词模板

>
> 区分两套：**Ref2VA（图参考数字人，优先用这套，适合你前面Ref2VA脚本，锁人脸+口型同步）**、**FL2VA（纯文生音视频）**
> ✅ 核心原则：H3本地开源版**不支持单独negative prompt输入**，负面约束直接写进提示词里；优先固定景别、固定光线、禁止大幅度头部转动，减少人物漂移
> ✅ Ref2VA最重要：开头明确锁定【人物特征保持不变】，写明图片用途：`图片1用来锁定人物面部特征、服装、肤色，不锁定背景`

## 一、Ref2VA｜数字人口播模板（推荐！搭配你的`h3_m4_ref2va.py`脚本）

>
> 适用：传入人像参考图，生成稳定人物+口型对齐语音，适合知识口播、短视频数字人

### 模板1｜中文口播（半身、固定机位，最稳）

```
主体定义：<Subject1>是图中年轻亚洲女性，面部五官、发型、服装全程保持不变，不换脸，五官不扭曲。
视频概要：固定机位半身人像，人物缓慢自然眨眼，嘴唇随对白精准同步，轻微头部微动，无大幅度转头。
保留分析：保留参考图人物五官、脸型、发型、服装，背景保持稳定不变，光影不变。
详细画面描述：柔和室内柔光，浅景深，干净简约白色墙面背景，24fps，写实照片质感，高清皮肤细节，自然面部微表情，无手部大幅度动作，画面无闪烁。
音频描述：<Subject1>自然清晰中文人声，语速平稳，说话内容：“大家好，今天我们一起来了解本地部署MiniMax H3视频模型，M4 Max跑这个模型体验非常优秀。”，环境音安静，轻微室内底噪，无背景音乐。
禁止：面部扭曲、五官变形、人物换脸、肢体穿模、画面闪烁、镜头推拉、画风突变
```

### 模板2｜英文口播（适合英文对白，你前面测试脚本用）

```
主体定义：<Subject1>是图中的年轻女生，面部五官、发型、服装全程保持不变，脸型稳定，不会变脸。
视频概要：固定机位半身人像，自然眨眼，嘴唇和对白精准同步，微小自然头部微动，不剧烈转头。
保留分析：锁定参考图人物五官、肤色、发型、衣服，场景和光照全程保持不变。
详细画面描述：柔和自然光，窗边环境，浅景深，写实人像，高清皮肤质感，稳定构图，画面不抖动。
音频描述：<Subject1>清晰英文人声，自然语气，台词：“I enjoy working with DiffSynth-Studio, it's a perfect framework.”，安静环境，轻微环境底噪，无配乐。
禁止：五官崩坏、手部畸形、画面闪烁、人物身份漂移、镜头移动
```

### 模板3｜产品讲解数字人（广告短视频）

```
主体定义：<Subject1>参考图里的女生，五官、服装全程不变。
视频概要：半身人像，面向镜头说话，口型跟随台词同步，轻微点头动作。
保留分析：锁定人物形象，桌面产品位置保持不变。
详细画面描述：简约桌面，柔和暖光，480P高清，写实摄影，画面稳定，无镜头晃动。
音频描述：清晰中文人声：“这款AI视频模型可以本地生成音画同步视频，不需要云端API。”，轻微环境白噪音。
禁止：人脸变形、产品移位、画面闪烁、肢体穿模
```

## 二、FL2VA｜纯文生音视频模板（无参考图，`h3_m4_fl2va.py`脚本）

### 模板A｜人像口播（纯文本生成人物+语音）

```
画面：固定机位半身年轻亚洲女性，柔和室内柔光，白色背景，写实摄影，皮肤质感真实，缓慢眨眼，嘴唇与台词同步，微小头部微动，构图稳定，画面无闪烁。
音频：清晰中文女声，语速适中，台词：“本地部署MiniMax H3，可以一次性生成同步语音与视频。”，安静室内环境底噪，无背景音乐。
禁止：五官扭曲、手部畸形、换脸、镜头推拉、剧烈动作
```

### 模板B｜场景短片（非人物，产品/风景，音画同步音效）

```
画面：木质桌面，一杯咖啡，阳光缓慢移动，蒸汽缓缓升起，静态镜头，写实摄影，光影柔和，画面稳定。
音频：轻柔白噪音，杯子轻微环境声，安静氛围音。
禁止：物体变形、画面闪烁、扭曲纹理
```

## 三、🎧 Ref2VA【音频音色参考模板】（H3王牌能力：参考一段音频音色，人物用该音色说话）

>
> 如果你同时传入参考图片+参考音频，提示词要写明音频作用

```
主体定义：<Subject1>是参考图片中的男生，五官发型服装全程锁定，不变脸。
视频概要：半身人像，固定机位，口型跟随台词同步，微小自然面部动作。
保留分析：图片锁定人物形象，<Audio1>锁定说话人音色，只复用音色，不复制原始音频内容。
详细画面描述：柔和办公室冷光，简约背景，写实高清人像，稳定镜头。
音频描述：使用<Audio1>的音色，中文台词：“我们可以使用参考音频来复刻人声，生成新对白”，环境安静。
禁止：五官崩坏、人物漂移、画面闪烁、手部畸形
```

## ✅ 提示词最佳实践（M4 Max本地DiffSynth必看）

1. **景别优先半身**：半身人像 > 特写 > 全身。全身人像极易出现手部崩坏、肢体穿模
2. **动作幅度一定要小**：只允许眨眼、轻微点头；不要写转头、抬手、大幅度肢体动作，大幅度动作会造成人脸漂移
3. **光线固定**：全程写明「光照不变」，光影变化太大，人物容易变脸
4. **台词尽量简短**：124帧（15s）控制台词长度，一句话不要太长，否则口型对齐变差
5. **参考图选择**：正面平视、光线均匀、干净背景的半身照，不要侧脸、强逆光图片
6. **不要叠加太多形容词**：不要堆砌大量电影级、8k、史诗级这类词，会增加画面不稳定

## ❌ 常见坑（不要写这些）

- ❌ 禁止：镜头缓慢推拉运镜、镜头环绕、人物站起来、大幅度挥手、转头看旁边
- ❌ 禁止：画面风格多次切换，一会二次元一会写实
- ❌ 不要同时写多个人物，单段视频优先只保留1个人物，多人物极易身份混乱

## 四、快速替换公式（你直接套，一句话改）

```
主体定义：<Subject1>【描述人物，锁定五官发型服装不变】
视频概要：【景别】，口型跟随台词同步，微小自然微动，禁止大幅度动作
保留分析：锁定参考图人物形象，光影不变
详细画面描述：【光线、场景、画质】
音频描述：【音色+台词+环境音】
禁止：五官扭曲、换脸、画面闪烁、肢体穿模
```

---

# 批量Seed循环脚本 Ref2VA版本（适配M4 Max，基于你之前 `h3_m4_ref2va.py` 修改）

>
> 功能：循环多个seed，自动生成不同版本视频，输出到独立文件夹，每个视频文件名带上seed，方便挑选最优版本
> 核心改动：增加seed列表循环、自动创建输出目录、每个seed独立保存视频，模型只加载一次（**关键！避免重复加载巨大模型浪费内存/时间**）

```
import torch
import os
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

# --------------------------
# 【只加载一次模型，在循环外！极大节省时间】
# --------------------------
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

# --------------------------
# 批量配置区，自行修改这里
# --------------------------
# 需要测试的seed列表，你可以自由增删
seed_list = [42, 10, 24, 66, 88, 123]
prompt = """
主体定义：<Subject1>是图中的年轻女生，面部五官、发型、服装全程保持不变，脸型稳定，不会变脸。
视频概要：固定机位半身人像，自然眨眼，嘴唇和对白精准同步，微小自然头部微动，不剧烈转头。
保留分析：锁定参考图人物五官、肤色、发型、衣服，场景和光照全程保持不变。
详细画面描述：柔和自然光，窗边环境，浅景深，写实人像，高清皮肤质感，稳定构图，画面不抖动。
音频描述：<Subject1>清晰英文人声，自然语气，台词："I enjoy working with DiffSynth-Studio, it's a perfect framework."，安静环境，轻微环境底噪，无配乐。
禁止：五官崩坏、手部畸形、画面闪烁、人物身份漂移、镜头移动
"""
height = 480
width = 832
num_frames = 124
num_inference_steps = 50

# 创建输出文件夹
output_dir = "batch_output_ref2va"
os.makedirs(output_dir, exist_ok=True)

# --------------------------
# 循环批量推理
# --------------------------
for seed in seed_list:
    print(f"\n========== 当前 Seed: {seed} ==========")
    video, audio = pipe(
        prompt=prompt,
        height=height,
        width=width,
        num_frames=num_frames,
        num_inference_steps=num_inference_steps,
        seed=seed,
        references=[{"type": "image", "image": ref_image}]
    )
    output_file = os.path.join(output_dir, f"h3_seed_{seed}.mp4")
    write_video_audio(
        video=video, audio=audio,
        output_path=output_file, fps=24, audio_sample_rate=32000,
    )
    print(f"✅ Seed {seed} 生成完成 -> {output_file}")

print("\n🎉 全部seed批量推理完成！视频保存在 batch_output_ref2va 文件夹")
```

## FL2VA版本（纯文生音视频批量脚本，h3_m4_fl2va_batch.py）

```
import torch
import os
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

# 模型仅加载一次
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
    vram_limit=96,
)

# 批量配置
seed_list = [0, 1, 5, 16, 42, 99]
prompt = """
画面：固定机位半身年轻亚洲女性，柔和室内柔光，白色背景，写实摄影，皮肤质感真实，缓慢眨眼，嘴唇与台词同步，微小头部微动，构图稳定，画面无闪烁。
音频：清晰中文女声，语速适中，台词："本地部署MiniMax H3，可以一次性生成同步语音与视频。"，安静室内环境底噪，无背景音乐。
禁止：五官扭曲、手部畸形、换脸、镜头推拉、剧烈动作
"""
height = 480
width = 832
num_frames = 124
num_inference_steps = 50

output_dir = "batch_output_fl2va"
os.makedirs(output_dir, exist_ok=True)

# 循环推理
for seed in seed_list:
    print(f"\n========== 当前 Seed: {seed} ==========")
    video, audio = pipe(
        prompt=prompt,
        height=height, width=width, num_frames=num_frames, num_inference_steps=num_inference_steps, seed=seed,
    )
    output_file = os.path.join(output_dir, f"h3_fl2va_seed_{seed}.mp4")
    write_video_audio(
        video=video, audio=audio,
        output_path=output_file, fps=24, audio_sample_rate=32000,
    )
    print(f"✅ Seed {seed} 生成完成 -> {output_file}")

print("\n🎉 FL2VA批量任务全部完成！")
```

## 使用说明

1. 直接新建`.py`文件，粘贴代码，修改`seed_list`、`prompt`
2. 运行：`python h3_m4_ref2va_batch.py`
3. 模型**只会在脚本启动加载1次**，之后循环不同seed，不用重复下载/加载模型，大幅节省时间
4. 输出视频全部放在单独文件夹，文件名自带seed号，方便对比挑选最优版本

### 可选增强功能（二选一，你想要哪个我直接加上）

A. 自动生成`seed对比清单txt`，把提示词、每个seed记录保存到文件夹，方便后续回溯
B. 自动跳过已经生成好的视频（断点续跑，如果中途中断，不会重复跑已经生成成功的seed）

---

# Ref2VA 完整版【断点续跑 + 自动生成seed日志】批量脚本（M4 Max）

特性：
✅ 模型仅加载一次
✅ 断点续跑：检测对应seed视频已存在，自动跳过，不重复推理
✅ 自动写入日志 `batch_log.txt`：记录prompt、参数、每个seed的生成状态、时间，方便后续挑选回溯
✅ 输出目录：`batch_output_ref2va`

```
import torch
import os
from datetime import datetime
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

# --------------------------
# 【只加载一次模型，在循环外！极大节省时间】
# --------------------------
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

# --------------------------
# 批量配置区，自行修改这里
# --------------------------
seed_list = [42, 10, 24, 66, 88, 123]
prompt = """
主体定义：<Subject1>是图中的年轻女生，面部五官、发型、服装全程保持不变，脸型稳定，不会变脸。
视频概要：固定机位半身人像，自然眨眼，嘴唇和对白精准同步，微小自然头部微动，不剧烈转头。
保留分析：锁定参考图人物五官、肤色、发型、衣服，场景和光照全程保持不变。
详细画面描述：柔和自然光，窗边环境，浅景深，写实人像，高清皮肤质感，稳定构图，画面不抖动。
音频描述：<Subject1>清晰英文人声，自然语气，台词："I enjoy working with DiffSynth-Studio, it's a perfect framework."，安静环境，轻微环境底噪，无配乐。
禁止：五官崩坏、手部畸形、画面闪烁、人物身份漂移、镜头移动
"""
height = 480
width = 832
num_frames = 124
num_inference_steps = 50

output_dir = "batch_output_ref2va"
os.makedirs(output_dir, exist_ok=True)
log_path = os.path.join(output_dir, "batch_log.txt")

# 写入头部日志（首次运行写入，追加模式不会覆盖旧日志）
with open(log_path, "a", encoding="utf-8") as f:
    f.write("="*60 + "\n")
    f.write(f"任务启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"分辨率：{width}x{height} | 帧数：{num_frames} | 推理步数：{num_inference_steps}\n")
    f.write(f"Prompt:\n{prompt}\n")
    f.write("="*60 + "\n")

# --------------------------
# 循环批量推理 + 断点续跑
# --------------------------
for seed in seed_list:
    output_file = os.path.join(output_dir, f"h3_seed_{seed}.mp4")
    if os.path.exists(output_file):
        info = f"\n⏭️ Seed {seed} 文件已存在，跳过该任务: {output_file}"
        print(info)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] Seed {seed} | SKIPPED（文件已存在）\n")
        continue

    print(f"\n========== 当前 Seed: {seed} ==========")
    try:
        video, audio = pipe(
            prompt=prompt,
            height=height,
            width=width,
            num_frames=num_frames,
            num_inference_steps=num_inference_steps,
            seed=seed,
            references=[{"type": "image", "image": ref_image}]
        )
        write_video_audio(
            video=video, audio=audio,
            output_path=output_file, fps=24, audio_sample_rate=32000,
        )
        info = f"✅ Seed {seed} 生成完成 -> {output_file}"
        print(info)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] Seed {seed} | SUCCESS | {output_file}\n")
    except Exception as e:
        err_msg = f"❌ Seed {seed} 失败，错误信息：{str(e)}"
        print(err_msg)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] Seed {seed} | FAILED | {str(e)}\n")

print("\n🎉 Ref2VA批量任务全部完成！视频保存在 batch_output_ref2va")
print(f"📝 日志文件：{log_path}")
```

# FL2VA完整版【断点续跑 + seed日志】批量脚本

```
import torch
import os
from datetime import datetime
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

# 模型仅加载一次
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
    vram_limit=96,
)

# 批量配置
seed_list = [0, 1, 5, 16, 42, 99]
prompt = """
画面：固定机位半身年轻亚洲女性，柔和室内柔光，白色背景，写实摄影，皮肤质感真实，缓慢眨眼，嘴唇与台词同步，微小头部微动，构图稳定，画面无闪烁。
音频：清晰中文女声，语速适中，台词："本地部署MiniMax H3，可以一次性生成同步语音与视频。"，安静室内环境底噪，无背景音乐。
禁止：五官扭曲、手部畸形、换脸、镜头推拉、剧烈动作
"""
height = 480
width = 832
num_frames = 124
num_inference_steps = 50

output_dir = "batch_output_fl2va"
os.makedirs(output_dir, exist_ok=True)
log_path = os.path.join(output_dir, "batch_log.txt")

# 写入任务头部信息
with open(log_path, "a", encoding="utf-8") as f:
    f.write("="*60 + "\n")
    f.write(f"任务启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"分辨率：{width}x{height} | 帧数：{num_frames} | 推理步数：{num_inference_steps}\n")
    f.write(f"Prompt:\n{prompt}\n")
    f.write("="*60 + "\n")

# 循环推理 + 断点续跑 + 异常捕获
for seed in seed_list:
    output_file = os.path.join(output_dir, f"h3_fl2va_seed_{seed}.mp4")
    if os.path.exists(output_file):
        info = f"\n⏭️ Seed {seed} 文件已存在，跳过该任务: {output_file}"
        print(info)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] Seed {seed} | SKIPPED（文件已存在）\n")
        continue

    print(f"\n========== 当前 Seed: {seed} ==========")
    try:
        video, audio = pipe(
            prompt=prompt,
            height=height, width=width, num_frames=num_frames, num_inference_steps=num_inference_steps, seed=seed,
        )
        write_video_audio(
            video=video, audio=audio,
            output_path=output_file, fps=24, audio_sample_rate=32000,
        )
        info = f"✅ Seed {seed} 生成完成 -> {output_file}"
        print(info)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] Seed {seed} | SUCCESS | {output_file}\n")
    except Exception as e:
        err_msg = f"❌ Seed {seed} 失败，错误信息：{str(e)}"
        print(err_msg)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] Seed {seed} | FAILED | {str(e)}\n")

print("\n🎉 FL2VA批量任务全部完成！")
print(f"📝 日志文件：{log_path}")
```

## ✨ 新增功能说明

1. **断点续跑**：脚本重启时会检测目标mp4文件是否存在，如果存在直接跳过，不会重复跑
2. **日志记录 batch_log.txt**
   - 任务开始时间、分辨率、帧数、推理步数、完整prompt
   - 每条seed状态：SUCCESS / SKIPPED / FAILED，附带时间戳
   - 报错时自动记录异常信息，方便定位崩溃seed
3. **异常捕获 try-except**：单个seed推理崩溃不会终止整个批量任务，会记录错误继续跑下一个seed

## 使用建议

- 修改`seed_list`、`prompt`直接在脚本上方【批量配置区】修改，不用改动下面推理循环
- 日志是追加写入，多次运行同一个脚本会继续追加记录，不会覆盖旧日志
- 如果你想清空日志重新开始，直接删除文件夹内的`batch_log.txt`

## **Pruned精简版批量脚本（同样带断点续跑+日志）**

# Pruned 精简版 Ref2VA 批量脚本（断点续跑 + 日志，适配M4 Max）

>
> Pruned = 剪枝版模型，显存占用更低，速度更快；保留全部批量能力：**模型仅加载一次、断点续跑、日志记录、异常捕获**
> 适用：MiniMax-H3 Ref2VA pruned 权重，适合M4 Max降低内存压力

```
import torch
import os
from datetime import datetime
from PIL import Image
from diffsynth.pipelines.minimax_h3_audio_video import MiniMaxH3Pipeline, ModelConfig
from diffsynth.utils.data.audio_video import write_video_audio
from modelscope import dataset_snapshot_download

# ========= M4 Max Pruned 剪枝模型 显存配置 =========
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

# --------------------------
# 加载 Pruned Ref2VA 模型（只加载一次）
# --------------------------
pipe = MiniMaxH3Pipeline.from_pretrained(
    torch_dtype=torch.bfloat16,
    device="mps",
    model_configs=[
        ModelConfig(model_id="DiffSynth-Studio/MiniMax-H3-Pruned", origin_file_pattern="minimax-h3-ref2va-pruned.safetensors", **vram_config),
        ModelConfig(model_id="DiffSynth-Studio/MiniMax-H3-Pruned", origin_file_pattern="minimax-h3-text-encoder-pruned.safetensors", **vram_config),
        ModelConfig(model_id="DiffSynth-Studio/MiniMax-H3-Pruned", origin_file_pattern="video_vae-pruned.safetensors", **vram_config),
        ModelConfig(model_id="DiffSynth-Studio/MiniMax-H3-Pruned", origin_file_pattern="audio_vae-pruned.safetensors", **vram_config),
    ],
    processor_config=ModelConfig(model_id="MiniMax/MiniMax-H3", origin_file_pattern="Ref2VA/processor/"),
    vram_limit=96,
)

# 下载示例参考人像图
dataset_snapshot_download(dataset_id="DiffSynth-Studio/diffsynth_example_dataset", local_dir="data/diffsynth_example_dataset", allow_file_pattern="minimax_h3/MiniMax-H3-Ref2VA/*")
ref_image = Image.open("data/diffsynth_example_dataset/minimax_h3/MiniMax-H3-Ref2VA/0.png").convert("RGB")

# --------------------------
# 【批量参数配置区｜直接在这里修改】
# --------------------------
seed_list = [42, 10, 24, 66, 88, 123]
prompt = """
主体定义：<Subject1>是图中的年轻女生，面部五官、发型、服装全程保持不变，脸型稳定，不会变脸。
视频概要：固定机位半身人像，自然眨眼，嘴唇和对白精准同步，微小自然头部微动，不剧烈转头。
保留分析：锁定参考图人物五官、肤色、发型、衣服，场景和光照全程保持不变。
详细画面描述：柔和自然光，窗边环境，浅景深，写实人像，高清皮肤质感，稳定构图，画面不抖动。
音频描述：<Subject1>清晰英文人声，自然语气，台词："I enjoy working with DiffSynth-Studio, it's a perfect framework."，安静环境，轻微环境底噪，无配乐。
禁止：五官崩坏、手部畸形、画面闪烁、人物身份漂移、镜头移动
"""
height = 480
width = 832
num_frames = 124
num_inference_steps = 50

output_dir = "batch_output_ref2va_pruned"
os.makedirs(output_dir, exist_ok=True)
log_path = os.path.join(output_dir, "batch_log.txt")

# 写入任务头部日志（追加模式，不覆盖旧日志）
with open(log_path, "a", encoding="utf-8") as f:
    f.write("="*60 + "\n")
    f.write(f"【Pruned Ref2VA】任务启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"分辨率：{width}x{height} | 帧数：{num_frames} | 推理步数：{num_inference_steps}\n")
    f.write(f"Prompt:\n{prompt}\n")
    f.write("="*60 + "\n")

# --------------------------
# Seed循环｜断点续跑 + 异常捕获
# --------------------------
for seed in seed_list:
    output_file = os.path.join(output_dir, f"h3_pruned_seed_{seed}.mp4")
    # 断点续跑：文件存在直接跳过
    if os.path.exists(output_file):
        info = f"\n⏭️ Seed {seed} 文件已存在，跳过任务: {output_file}"
        print(info)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] Seed {seed} | SKIPPED 文件已存在\n")
        continue

    print(f"\n========== 当前 Seed: {seed} ==========")
    try:
        video, audio = pipe(
            prompt=prompt,
            height=height,
            width=width,
            num_frames=num_frames,
            num_inference_steps=num_inference_steps,
            seed=seed,
            references=[{"type": "image", "image": ref_image}]
        )
        write_video_audio(
            video=video, audio=audio,
            output_path=output_file, fps=24, audio_sample_rate=32000,
        )
        info = f"✅ Seed {seed} 生成完成 -> {output_file}"
        print(info)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] Seed {seed} | SUCCESS | {output_file}\n")
    except Exception as e:
        err_msg = f"❌ Seed {seed} 失败，错误：{str(e)}"
        print(err_msg)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] Seed {seed} | FAILED | {str(e)}\n")

print("\n🎉 Pruned Ref2VA批量任务全部完成！")
print(f"📝 日志路径：{log_path}")
```

---

# Pruned 精简版 FL2VA 批量脚本（断点续跑 + 日志）

>
> Pruned FL2VA：纯文本生成音视频，剪枝权重，内存占用更低

```
import torch
import os
from datetime import datetime
from diffsynth.pipelines.minimax_h3_audio_video import MiniMaxH3Pipeline, ModelConfig
from diffsynth.utils.data.audio_video import write_video_audio
from PIL import Image

# ========= M4 Max Pruned FL2VA 显存配置 =========
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

# --------------------------
# 加载 Pruned FL2VA 模型（仅加载一次）
# --------------------------
pipe = MiniMaxH3Pipeline.from_pretrained(
    torch_dtype=torch.bfloat16,
    device="mps",
    model_configs=[
        ModelConfig(model_id="DiffSynth-Studio/MiniMax-H3-Pruned", origin_file_pattern="minimax-h3-fl2va-pruned.safetensors", **vram_config),
        ModelConfig(model_id="DiffSynth-Studio/MiniMax-H3-Pruned", origin_file_pattern="minimax-h3-text-encoder-pruned.safetensors", **vram_config),
        ModelConfig(model_id="DiffSynth-Studio/MiniMax-H3-Pruned", origin_file_pattern="video_vae-pruned.safetensors", **vram_config),
        ModelConfig(model_id="DiffSynth-Studio/MiniMax-H3-Pruned", origin_file_pattern="audio_vae-pruned.safetensors", **vram_config),
    ],
    processor_config=ModelConfig(model_id="MiniMax/MiniMax-H3", origin_file_pattern="FL2VA/processor/"),
    vram_limit=96,
)

# --------------------------
# 批量参数配置区
# --------------------------
seed_list = [0, 1, 5, 16, 42, 99]
prompt = """
画面：固定机位半身年轻亚洲女性，柔和室内柔光，白色背景，写实摄影，皮肤质感真实，缓慢眨眼，嘴唇与台词同步，微小头部微动，构图稳定，画面无闪烁。
音频：清晰中文女声，语速适中，台词："本地部署MiniMax H3，可以一次性生成同步语音与视频。"，安静室内环境底噪，无背景音乐。
禁止：五官扭曲、手部畸形、换脸、镜头推拉、剧烈动作
"""
height = 480
width = 832
num_frames = 124
num_inference_steps = 50

output_dir = "batch_output_fl2va_pruned"
os.makedirs(output_dir, exist_ok=True)
log_path = os.path.join(output_dir, "batch_log.txt")

# 写入任务头部日志
with open(log_path, "a", encoding="utf-8") as f:
    f.write("="*60 + "\n")
    f.write(f"【Pruned FL2VA】任务启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"分辨率：{width}x{height} | 帧数：{num_frames} | 推理步数：{num_inference_steps}\n")
    f.write(f"Prompt:\n{prompt}\n")
    f.write("="*60 + "\n")

# --------------------------
# Seed循环｜断点续跑 + 异常捕获
# --------------------------
for seed in seed_list:
    output_file = os.path.join(output_dir, f"h3_fl2va_pruned_seed_{seed}.mp4")
    if os.path.exists(output_file):
        info = f"\n⏭️ Seed {seed} 文件已存在，跳过任务: {output_file}"
        print(info)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] Seed {seed} | SKIPPED 文件已存在\n")
        continue

    print(f"\n========== 当前 Seed: {seed} ==========")
    try:
        video, audio = pipe(
            prompt=prompt,
            height=height, width=width, num_frames=num_frames, num_inference_steps=num_inference_steps, seed=seed,
        )
        write_video_audio(
            video=video, audio=audio,
            output_path=output_file, fps=24, audio_sample_rate=32000,
        )
        info = f"✅ Seed {seed} 生成完成 -> {output_file}"
        print(info)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] Seed {seed} | SUCCESS | {output_file}\n")
    except Exception as e:
        err_msg = f"❌ Seed {seed} 失败，错误：{str(e)}"
        print(err_msg)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] Seed {seed} | FAILED | {str(e)}\n")

print("\n🎉 Pruned FL2VA批量任务全部完成！")
print(f"📝 日志路径：{log_path}")
```

## 4套脚本汇总清单（现在全部齐全）

1. Ref2VA NF4原版批量脚本（断点+日志）
2. FL2VA NF4原版批量脚本（断点+日志）
3. Ref2VA Pruned剪枝版批量脚本（断点+日志）
4. FL2VA Pruned剪枝版批量脚本（断点+日志）

## Pruned版本使用提示

- Pruned 优势：推理更快、MPS显存占用更低；微小画质损失，适合快速迭代试seed
- 权重ID改成了`DiffSynth-Studio/MiniMax-H3-Pruned`，会自动拉取pruned剪枝权重
- 输出文件夹独立：`batch_output_ref2va_pruned` / `batch_output_fl2va_pruned`，不和NF4版本视频混在一起

---

## 增加自定义参考图片路径（不用固定示例图，可以直接指定任意本地人像图片）

# Pruned Ref2VA 脚本【升级：自定义本地参考图 + 断点续跑 + 日志】

改动点：

1. 移除自动下载示例数据集，改为**手动填写本地图片路径**
2. 增加图片存在性校验，图片不存在直接抛出提示终止脚本，避免空引用报错
3. 保留原有全部能力：模型只加载一次、断点续跑、日志、异常捕获>

> 适用：Pruned Ref2VA，M4 Max

```
import torch
import os
from datetime import datetime
from PIL import Image
from diffsynth.pipelines.minimax_h3_audio_video import MiniMaxH3Pipeline, ModelConfig
from diffsynth.utils.data.audio_video import write_video_audio

# ========= M4 Max Pruned Ref2VA 显存配置 =========
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

# --------------------------
# 【配置区：自定义本地参考图片路径，在这里修改】
# --------------------------
ref_img_path = "./ref_face.jpg"   # <- 修改这里！支持jpg/png
# 校验参考图是否存在
if not os.path.exists(ref_img_path):
    raise FileNotFoundError(f"参考图片不存在！路径：{ref_img_path}\n请检查文件路径是否正确")
ref_image = Image.open(ref_img_path).convert("RGB")

# --------------------------
# 加载 Pruned Ref2VA 模型（只加载一次）
# --------------------------
pipe = MiniMaxH3Pipeline.from_pretrained(
    torch_dtype=torch.bfloat16,
    device="mps",
    model_configs=[
        ModelConfig(model_id="DiffSynth-Studio/MiniMax-H3-Pruned", origin_file_pattern="minimax-h3-ref2va-pruned.safetensors", **vram_config),
        ModelConfig(model_id="DiffSynth-Studio/MiniMax-H3-Pruned", origin_file_pattern="minimax-h3-text-encoder-pruned.safetensors", **vram_config),
        ModelConfig(model_id="DiffSynth-Studio/MiniMax-H3-Pruned", origin_file_pattern="video_vae-pruned.safetensors", **vram_config),
        ModelConfig(model_id="DiffSynth-Studio/MiniMax-H3-Pruned", origin_file_pattern="audio_vae-pruned.safetensors", **vram_config),
    ],
    processor_config=ModelConfig(model_id="MiniMax/MiniMax-H3", origin_file_pattern="Ref2VA/processor/"),
    vram_limit=96,
)

# --------------------------
# 【批量参数配置区｜直接在这里修改】
# --------------------------
seed_list = [42, 10, 24, 66, 88, 123]
prompt = """
主体定义：<Subject1>是图中的年轻女生，面部五官、发型、服装全程保持不变，脸型稳定，不会变脸。
视频概要：固定机位半身人像，自然眨眼，嘴唇和对白精准同步，微小自然头部微动，不剧烈转头。
保留分析：锁定参考图人物五官、肤色、发型、衣服，场景和光照全程保持不变。
详细画面描述：柔和自然光，窗边环境，浅景深，写实人像，高清皮肤质感，稳定构图，画面不抖动。
音频描述：<Subject1>清晰英文人声，自然语气，台词："I enjoy working with DiffSynth-Studio, it's a perfect framework."，安静环境，轻微环境底噪，无配乐。
禁止：五官崩坏、手部畸形、画面闪烁、人物身份漂移、镜头移动
"""
height = 480
width = 832
num_frames = 124
num_inference_steps = 50

output_dir = "batch_output_ref2va_pruned"
os.makedirs(output_dir, exist_ok=True)
log_path = os.path.join(output_dir, "batch_log.txt")

# 写入任务头部日志（追加模式，不覆盖旧日志）
with open(log_path, "a", encoding="utf-8") as f:
    f.write("="*60 + "\n")
    f.write(f"【Pruned Ref2VA】任务启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"参考图片路径：{ref_img_path}\n")
    f.write(f"分辨率：{width}x{height} | 帧数：{num_frames} | 推理步数：{num_inference_steps}\n")
    f.write(f"Prompt:\n{prompt}\n")
    f.write("="*60 + "\n")

# --------------------------
# Seed循环｜断点续跑 + 异常捕获
# --------------------------
for seed in seed_list:
    output_file = os.path.join(output_dir, f"h3_pruned_seed_{seed}.mp4")
    # 断点续跑：文件存在直接跳过
    if os.path.exists(output_file):
        info = f"\n⏭️ Seed {seed} 文件已存在，跳过任务: {output_file}"
        print(info)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] Seed {seed} | SKIPPED 文件已存在\n")
        continue

    print(f"\n========== 当前 Seed: {seed} ==========")
    try:
        video, audio = pipe(
            prompt=prompt,
            height=height,
            width=width,
            num_frames=num_frames,
            num_inference_steps=num_inference_steps,
            seed=seed,
            references=[{"type": "image", "image": ref_image}]
        )
        write_video_audio(
            video=video, audio=audio,
            output_path=output_file, fps=24, audio_sample_rate=32000,
        )
        info = f"✅ Seed {seed} 生成完成 -> {output_file}"
        print(info)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] Seed {seed} | SUCCESS | {output_file}\n")
    except Exception as e:
        err_msg = f"❌ Seed {seed} 失败，错误：{str(e)}"
        print(err_msg)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] Seed {seed} | FAILED | {str(e)}\n")

print("\n🎉 Pruned Ref2VA批量任务全部完成！")
print(f"📝 日志路径：{log_path}")
```

# Ref2VA NF4原版脚本【同步升级自定义参考图】

```
import torch
import os
from datetime import datetime
from PIL import Image
from diffsynth.pipelines.minimax_h3_audio_video import MiniMaxH3Pipeline, ModelConfig
from diffsynth.utils.data.audio_video import write_video_audio

# ========= M4 Max NF4 Ref2VA 显存配置 =========
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

# --------------------------
# 【配置区：自定义本地参考图片路径，在这里修改】
# --------------------------
ref_img_path = "./ref_face.jpg"
if not os.path.exists(ref_img_path):
    raise FileNotFoundError(f"参考图片不存在！路径：{ref_img_path}\n请检查文件路径是否正确")
ref_image = Image.open(ref_img_path).convert("RGB")

# --------------------------
# 加载 NF4 Ref2VA 模型（只加载一次）
# --------------------------
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

# --------------------------
# 【批量参数配置区｜直接在这里修改】
# --------------------------
seed_list = [42, 10, 24, 66, 88, 123]
prompt = """
主体定义：<Subject1>是图中的年轻女生，面部五官、发型、服装全程保持不变，脸型稳定，不会变脸。
视频概要：固定机位半身人像，自然眨眼，嘴唇和对白精准同步，微小自然头部微动，不剧烈转头。
保留分析：锁定参考图人物五官、肤色、发型、衣服，场景和光照全程保持不变。
详细画面描述：柔和自然光，窗边环境，浅景深，写实人像，高清皮肤质感，稳定构图，画面不抖动。
音频描述：<Subject1>清晰英文人声，自然语气，台词："I enjoy working with DiffSynth-Studio, it's a perfect framework."，安静环境，轻微环境底噪，无配乐。
禁止：五官崩坏、手部畸形、画面闪烁、人物身份漂移、镜头移动
"""
height = 480
width = 832
num_frames = 124
num_inference_steps = 50

output_dir = "batch_output_ref2va"
os.makedirs(output_dir, exist_ok=True)
log_path = os.path.join(output_dir, "batch_log.txt")

# 写入任务头部日志
with open(log_path, "a", encoding="utf-8") as f:
    f.write("="*60 + "\n")
    f.write(f"【NF4 Ref2VA】任务启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"参考图片路径：{ref_img_path}\n")
    f.write(f"分辨率：{width}x{height} | 帧数：{num_frames} | 推理步数：{num_inference_steps}\n")
    f.write(f"Prompt:\n{prompt}\n")
    f.write("="*60 + "\n")

# --------------------------
# Seed循环｜断点续跑 + 异常捕获
# --------------------------
for seed in seed_list:
    output_file = os.path.join(output_dir, f"h3_seed_{seed}.mp4")
    if os.path.exists(output_file):
        info = f"\n⏭️ Seed {seed} 文件已存在，跳过任务: {output_file}"
        print(info)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] Seed {seed} | SKIPPED 文件已存在\n")
        continue

    print(f"\n========== 当前 Seed: {seed} ==========")
    try:
        video, audio = pipe(
            prompt=prompt,
            height=height,
            width=width,
            num_frames=num_frames,
            num_inference_steps=num_inference_steps,
            seed=seed,
            references=[{"type": "image", "image": ref_image}]
        )
        write_video_audio(
            video=video, audio=audio,
            output_path=output_file, fps=24, audio_sample_rate=32000,
        )
        info = f"✅ Seed {seed} 生成完成 -> {output_file}"
        print(info)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] Seed {seed} | SUCCESS | {output_file}\n")
    except Exception as e:
        err_msg = f"❌ Seed {seed} 失败，错误：{str(e)}"
        print(err_msg)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] Seed {seed} | FAILED | {str(e)}\n")

print("\n🎉 NF4 Ref2VA批量任务全部完成！")
print(f"📝 日志路径：{log_path}")
```

## 使用说明

1. 修改 `ref_img_path`，可以填写相对路径 `./ref_face.png` 或者绝对路径 `/Users/xxx/pics/ref.jpg`
2. 脚本启动会**预先校验图片是否存在**，找不到图片直接报错退出，防止后续推理报错
3. 日志里自动记录本次使用的参考图路径，后续回看日志能知道当时用哪张参考人像
4. FL2VA本身不需要参考图，所以FL2VA两个脚本保持原样不动

---

## 支持批量多张参考图循环（遍历一批人像，每一张图跑一组seed）

可以，这个功能建议做成：**遍历一个目录里的多张参考图，每张图独立跑一组 seed**，并按图片子目录归档，避免不同人像结果混在一起。

下面给你两版：

1. **NF4 Ref2VA 批量多图版**
2. **Pruned Ref2VA 批量多图版**

FL2VA 不需要参考图，所以不涉及这个改动。

---

# 1. NF4 Ref2VA｜批量多张参考图循环脚本

```
import torch
import os
from datetime import datetime
from PIL import Image
from diffsynth.pipelines.minimax_h3_audio_video import MiniMaxH3Pipeline, ModelConfig
from diffsynth.utils.data.audio_video import write_video_audio

# ========= M4 Max 128GB NF4 Ref2VA 配置 =========
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

# --------------------------
# 【配置区】
# --------------------------
# 参考图片目录：放多张 jpg / png 人像
ref_images_dir = "./ref_images"

# 支持的图片后缀
supported_exts = [".jpg", ".jpeg", ".png", ".webp"]

# 输出根目录
output_root_dir = "./batch_output_ref2va"

# 要跑的 seed 列表
seed_list = [42, 10, 24, 66, 88, 123]

# 生成参数
prompt = """
主体定义：<Subject1>是参考图中的人物，面部五官、发型、服装全程保持不变，脸型稳定，不会变脸。
视频概要：固定机位半身人像，自然眨眼，嘴唇和对白精准同步，微小自然头部微动，不剧烈转头。
保留分析：锁定参考图人物五官、肤色、发型、服装，场景和光照全程保持不变。
详细画面描述：柔和自然光，浅景深，写实人像，高清皮肤质感，稳定构图，画面不抖动。
音频描述：<Subject1>清晰自然人声，语气平稳，台词："本地部署MiniMax H3，可以一次性生成同步语音与视频。"，安静环境，轻微底噪，无背景音乐。
禁止：五官崩坏、手部畸形、画面闪烁、人物身份漂移、镜头移动、剧烈转头
"""

height = 480
width = 832
num_frames = 124
num_inference_steps = 50

# --------------------------
# 加载模型：只加载一次
# --------------------------
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

# --------------------------
# 遍历多张参考图
# --------------------------
if not os.path.exists(ref_images_dir):
    raise FileNotFoundError(f"参考图片目录不存在：{ref_images_dir}\n请先创建目录并放入人像图片。")

image_files = [
    f for f in os.listdir(ref_images_dir)
    if os.path.splitext(f)[1].lower() in supported_exts
]

if not image_files:
    raise FileNotFoundError(f"在目录 {ref_images_dir} 中未找到支持的图片文件。支持格式：{', '.join(supported_exts)}")

os.makedirs(output_root_dir, exist_ok=True)
log_path = os.path.join(output_root_dir, "batch_log.txt")

# 写入总日志头部
with open(log_path, "a", encoding="utf-8") as f:
    f.write("=" * 70 + "\n")
    f.write(f"【NF4 Ref2VA】批量多图任务启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"参考图片目录：{ref_images_dir}\n")
    f.write(f"输出根目录：{output_root_dir}\n")
    f.write(f"分辨率：{width}x{height} | 帧数：{num_frames} | 推理步数：{num_inference_steps}\n")
    f.write(f"Seed列表：{', '.join(map(str, seed_list))}\n")
    f.write(f"Prompt:\n{prompt}\n")
    f.write("=" * 70 + "\n")

for img_file in image_files:
    img_stem = os.path.splitext(img_file)[0]
    img_path = os.path.join(ref_images_dir, img_file)

    # 每张图一个独立输出目录
    output_dir = os.path.join(output_root_dir, img_stem)
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n==========================")
    print(f"处理参考图：{img_file}")
    print(f"输出目录：{output_dir}")
    print(f"==========================")

    # 写入单张图任务日志
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"\n[{datetime.now()}] 开始处理图片：{img_file}\n")
        f.write(f"图片路径：{img_path}\n")
        f.write(f"输出目录：{output_dir}\n")

    try:
        ref_image = Image.open(img_path).convert("RGB")
    except Exception as e:
        print(f"❌ 无法打开图片：{img_file}，错误：{str(e)}")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] 图片读取失败：{img_file} | {str(e)}\n")
        continue

    # 每张图跑一组 seed
    for seed in seed_list:
        output_file = os.path.join(output_dir, f"h3_seed_{seed}.mp4")

        # 断点续跑
        if os.path.exists(output_file):
            info = f"⏭️ {img_file} | Seed {seed} 已存在，跳过"
            print(info)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] {img_file} | Seed {seed} | SKIPPED | 文件已存在\n")
            continue

        print(f"---------- 当前 Seed: {seed} ----------")
        try:
            video, audio = pipe(
                prompt=prompt,
                height=height,
                width=width,
                num_frames=num_frames,
                num_inference_steps=num_inference_steps,
                seed=seed,
                references=[{"type": "image", "image": ref_image}]
            )
            write_video_audio(
                video=video,
                audio=audio,
                output_path=output_file,
                fps=24,
                audio_sample_rate=32000,
            )
            info = f"✅ {img_file} | Seed {seed} 完成 -> {output_file}"
            print(info)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] {img_file} | Seed {seed} | SUCCESS | {output_file}\n")
        except Exception as e:
            err_msg = f"❌ {img_file} | Seed {seed} 失败：{str(e)}"
            print(err_msg)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] {img_file} | Seed {seed} | FAILED | {str(e)}\n")

print("\n🎉 全部参考图批量任务完成！")
print(f"📝 日志文件：{log_path}")
```

---

# 2. Pruned Ref2VA｜批量多张参考图循环脚本

```
import torch
import os
from datetime import datetime
from PIL import Image
from diffsynth.pipelines.minimax_h3_audio_video import MiniMaxH3Pipeline, ModelConfig
from diffsynth.utils.data.audio_video import write_video_audio

# ========= M4 Max Pruned Ref2VA 配置 =========
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

# --------------------------
# 【配置区】
# --------------------------
ref_images_dir = "./ref_images"
supported_exts = [".jpg", ".jpeg", ".png", ".webp"]
output_root_dir = "./batch_output_ref2va_pruned"
seed_list = [42, 10, 24, 66, 88, 123]

prompt = """
主体定义：<Subject1>是参考图中的人物，面部五官、发型、服装全程保持不变，脸型稳定，不会变脸。
视频概要：固定机位半身人像，自然眨眼，嘴唇和对白精准同步，微小自然头部微动，不剧烈转头。
保留分析：锁定参考图人物五官、肤色、发型、服装，场景和光照全程保持不变。
详细画面描述：柔和自然光，浅景深，写实人像，高清皮肤质感，稳定构图，画面不抖动。
音频描述：<Subject1>清晰自然人声，语气平稳，台词："本地部署MiniMax H3，可以一次性生成同步语音与视频。"，安静环境，轻微底噪，无背景音乐。
禁止：五官崩坏、手部畸形、画面闪烁、人物身份漂移、镜头移动、剧烈转头
"""

height = 480
width = 832
num_frames = 124
num_inference_steps = 50

# --------------------------
# 加载 Pruned 模型：只加载一次
# --------------------------
pipe = MiniMaxH3Pipeline.from_pretrained(
    torch_dtype=torch.bfloat16,
    device="mps",
    model_configs=[
        ModelConfig(model_id="DiffSynth-Studio/MiniMax-H3-Pruned", origin_file_pattern="minimax-h3-ref2va-pruned.safetensors", **vram_config),
        ModelConfig(model_id="DiffSynth-Studio/MiniMax-H3-Pruned", origin_file_pattern="minimax-h3-text-encoder-pruned.safetensors", **vram_config),
        ModelConfig(model_id="DiffSynth-Studio/MiniMax-H3-Pruned", origin_file_pattern="video_vae-pruned.safetensors", **vram_config),
        ModelConfig(model_id="DiffSynth-Studio/MiniMax-H3-Pruned", origin_file_pattern="audio_vae-pruned.safetensors", **vram_config),
    ],
    processor_config=ModelConfig(model_id="MiniMax/MiniMax-H3", origin_file_pattern="Ref2VA/processor/"),
    vram_limit=96,
)

# --------------------------
# 遍历多张参考图
# --------------------------
if not os.path.exists(ref_images_dir):
    raise FileNotFoundError(f"参考图片目录不存在：{ref_images_dir}\n请先创建目录并放入人像图片。")

image_files = [
    f for f in os.listdir(ref_images_dir)
    if os.path.splitext(f)[1].lower() in supported_exts
]

if not image_files:
    raise FileNotFoundError(f"在目录 {ref_images_dir} 中未找到支持的图片文件。支持格式：{', '.join(supported_exts)}")

os.makedirs(output_root_dir, exist_ok=True)
log_path = os.path.join(output_root_dir, "batch_log.txt")

with open(log_path, "a", encoding="utf-8") as f:
    f.write("=" * 70 + "\n")
    f.write(f"【Pruned Ref2VA】批量多图任务启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"参考图片目录：{ref_images_dir}\n")
    f.write(f"输出根目录：{output_root_dir}\n")
    f.write(f"分辨率：{width}x{height} | 帧数：{num_frames} | 推理步数：{num_inference_steps}\n")
    f.write(f"Seed列表：{', '.join(map(str, seed_list))}\n")
    f.write(f"Prompt:\n{prompt}\n")
    f.write("=" * 70 + "\n")

for img_file in image_files:
    img_stem = os.path.splitext(img_file)[0]
    img_path = os.path.join(ref_images_dir, img_file)
    output_dir = os.path.join(output_root_dir, img_stem)
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n==========================")
    print(f"处理参考图：{img_file}")
    print(f"输出目录：{output_dir}")
    print(f"==========================")

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"\n[{datetime.now()}] 开始处理图片：{img_file}\n")
        f.write(f"图片路径：{img_path}\n")
        f.write(f"输出目录：{output_dir}\n")

    try:
        ref_image = Image.open(img_path).convert("RGB")
    except Exception as e:
        print(f"❌ 无法打开图片：{img_file}，错误：{str(e)}")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] 图片读取失败：{img_file} | {str(e)}\n")
        continue

    for seed in seed_list:
        output_file = os.path.join(output_dir, f"h3_pruned_seed_{seed}.mp4")

        if os.path.exists(output_file):
            info = f"⏭️ {img_file} | Seed {seed} 已存在，跳过"
            print(info)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] {img_file} | Seed {seed} | SKIPPED | 文件已存在\n")
            continue

        print(f"---------- 当前 Seed: {seed} ----------")
        try:
            video, audio = pipe(
                prompt=prompt,
                height=height,
                width=width,
                num_frames=num_frames,
                num_inference_steps=num_inference_steps,
                seed=seed,
                references=[{"type": "image", "image": ref_image}]
            )
            write_video_audio(
                video=video,
                audio=audio,
                output_path=output_file,
                fps=24,
                audio_sample_rate=32000,
            )
            info = f"✅ {img_file} | Seed {seed} 完成 -> {output_file}"
            print(info)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] {img_file} | Seed {seed} | SUCCESS | {output_file}\n")
        except Exception as e:
            err_msg = f"❌ {img_file} | Seed {seed} 失败：{str(e)}"
            print(err_msg)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] {img_file} | Seed {seed} | FAILED | {str(e)}\n")

print("\n🎉 Pruned 批量多图任务完成！")
print(f"📝 日志文件：{log_path}")
```

---

# 目录结构建议

你这样放文件：

```
your_project/
├── ref_images/
│   ├── person_a.jpg
│   ├── person_b.png
│   └── person_c.webp
├── h3_ref2va_batch_multi.py
└── h3_ref2va_pruned_batch_multi.py
```

运行后会自动生成：

```
batch_output_ref2va/
├── batch_log.txt
├── person_a/
│   ├── h3_seed_42.mp4
│   ├── h3_seed_10.mp4
│   └── ...
├── person_b/
│   └── ...
```

Pruned 版本会输出到：

```
batch_output_ref2va_pruned/
├── batch_log.txt
├── person_a/
└── ...
```

---

# 这版增强点

1. **支持批量人像目录**
   - 自动扫描 `ref_images/`
   - 支持 `.jpg / .jpeg / .png / .webp`
2. **每张图独立结果目录**
   - 不会把不同人物的视频混在一起
   - 方便后期按人物筛选
3. **断点续跑仍然有效**
   - 某个 seed 已生成就跳过
   - 中途停止后重新运行不会重复已完成视频
4. **日志更完整**
   - 记录每张图、每个 seed、每个输出路径
   - 失败时记录错误原因
   - 方便回溯哪个人物哪一版效果最好
5. **模型只加载一次**
   - 不会每张图重新加载模型
   - 适合 M4 Max 128GB 批量处理

---

## **自动生成 Markdown 结果报告**，把每张图、每个 seed、成败状态、文件路径整理成一张表

# 升级说明

在上面两套【多参考图批量Ref2VA脚本】中新增：
✅ 自动生成 `report.md`，表格字段：参考图名称、Seed、状态、视频路径、时间
✅ 每次成功/失败/跳过都会实时追加写入markdown，中途中断也不会丢失已有记录
✅ 同时保留原有 `batch_log.txt`，双日志（txt纯文本 + Markdown可视化报告）
✅ 断点续跑兼容，重复运行不会重复添加旧条目

## 1. NF4 Ref2VA｜批量多图 + Markdown报告完整版

```
import torch
import os
from datetime import datetime
from PIL import Image
from diffsynth.pipelines.minimax_h3_audio_video import MiniMaxH3Pipeline, ModelConfig
from diffsynth.utils.data.audio_video import write_video_audio

# ========= M4 Max 128GB NF4 Ref2VA 配置 =========
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

# --------------------------
# 【配置区】
# --------------------------
ref_images_dir = "./ref_images"
supported_exts = [".jpg", ".jpeg", ".png", ".webp"]
output_root_dir = "./batch_output_ref2va"
seed_list = [42, 10, 24, 66, 88, 123]

prompt = """
主体定义：<Subject1>是参考图中的人物，面部五官、发型、服装全程保持不变，脸型稳定，不会变脸。
视频概要：固定机位半身人像，自然眨眼，嘴唇和对白精准同步，微小自然头部微动，不剧烈转头。
保留分析：锁定参考图人物五官、肤色、发型、服装，场景和光照全程保持不变。
详细画面描述：柔和自然光，浅景深，写实人像，高清皮肤质感，稳定构图，画面不抖动。
音频描述：<Subject1>清晰自然人声，语气平稳，台词："本地部署MiniMax H3，可以一次性生成同步语音与视频。"，安静环境，轻微底噪，无背景音乐。
禁止：五官崩坏、手部畸形、画面闪烁、人物身份漂移、镜头移动、剧烈转头
"""

height = 480
width = 832
num_frames = 124
num_inference_steps = 50

# --------------------------
# 初始化日志 & Markdown报告
# --------------------------
os.makedirs(output_root_dir, exist_ok=True)
log_path = os.path.join(output_root_dir, "batch_log.txt")
md_report_path = os.path.join(output_root_dir, "report.md")

# 如果md文件不存在，写入表头
if not os.path.exists(md_report_path):
    with open(md_report_path, "w", encoding="utf-8") as f:
        f.write("# NF4 Ref2VA 批量生成结果报告\n\n")
        f.write(f"任务启动：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"参考图目录：`{ref_images_dir}`\n")
        f.write(f"Seed列表：{seed_list}\n\n")
        f.write("| 参考图 | Seed | 状态 | 文件路径 | 时间 |\n")
        f.write("|--------|------|------|----------|------|\n")

# 写入txt总日志头部
with open(log_path, "a", encoding="utf-8") as f:
    f.write("=" * 70 + "\n")
    f.write(f"【NF4 Ref2VA】批量多图任务启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"参考图片目录：{ref_images_dir}\n")
    f.write(f"输出根目录：{output_root_dir}\n")
    f.write(f"分辨率：{width}x{height} | 帧数：{num_frames} | 推理步数：{num_inference_steps}\n")
    f.write(f"Seed列表：{', '.join(map(str, seed_list))}\n")
    f.write(f"Prompt:\n{prompt}\n")
    f.write("=" * 70 + "\n")

# --------------------------
# 加载模型：只加载一次
# --------------------------
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

# --------------------------
# 遍历多张参考图
# --------------------------
if not os.path.exists(ref_images_dir):
    raise FileNotFoundError(f"参考图片目录不存在：{ref_images_dir}\n请先创建目录并放入人像图片。")

image_files = [
    f for f in os.listdir(ref_images_dir)
    if os.path.splitext(f)[1].lower() in supported_exts
]

if not image_files:
    raise FileNotFoundError(f"在目录 {ref_images_dir} 中未找到支持的图片文件。支持格式：{', '.join(supported_exts)}")

for img_file in image_files:
    img_stem = os.path.splitext(img_file)[0]
    img_path = os.path.join(ref_images_dir, img_file)

    # 每张图一个独立输出目录
    output_dir = os.path.join(output_root_dir, img_stem)
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n==========================")
    print(f"处理参考图：{img_file}")
    print(f"输出目录：{output_dir}")
    print(f"==========================")

    # 写入单张图任务日志
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"\n[{datetime.now()}] 开始处理图片：{img_file}\n")
        f.write(f"图片路径：{img_path}\n")
        f.write(f"输出目录：{output_dir}\n")

    try:
        ref_image = Image.open(img_path).convert("RGB")
    except Exception as e:
        print(f"❌ 无法打开图片：{img_file}，错误：{str(e)}")
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] 图片读取失败：{img_file} | {str(e)}\n")
        # 写入markdown
        with open(md_report_path, "a", encoding="utf-8") as f:
            f.write(f"| {img_file} | - | READ_FAILED | - | {now_str} |\n")
        continue

    # 每张图跑一组 seed
    for seed in seed_list:
        output_file = os.path.join(output_dir, f"h3_seed_{seed}.mp4")
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 断点续跑
        if os.path.exists(output_file):
            info = f"⏭️ {img_file} | Seed {seed} 已存在，跳过"
            print(info)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] {img_file} | Seed {seed} | SKIPPED | 文件已存在\n")
            with open(md_report_path, "a", encoding="utf-8") as f:
                f.write(f"| {img_file} | {seed} | SKIPPED | `{output_file}` | {now_str} |\n")
            continue

        print(f"---------- 当前 Seed: {seed} ----------")
        try:
            video, audio = pipe(
                prompt=prompt,
                height=height,
                width=width,
                num_frames=num_frames,
                num_inference_steps=num_inference_steps,
                seed=seed,
                references=[{"type": "image", "image": ref_image}]
            )
            write_video_audio(
                video=video,
                audio=audio,
                output_path=output_file,
                fps=24,
                audio_sample_rate=32000,
            )
            info = f"✅ {img_file} | Seed {seed} 完成 -> {output_file}"
            print(info)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] {img_file} | Seed {seed} | SUCCESS | {output_file}\n")
            with open(md_report_path, "a", encoding="utf-8") as f:
                f.write(f"| {img_file} | {seed} | SUCCESS | `{output_file}` | {now_str} |\n")
        except Exception as e:
            err_msg = f"❌ {img_file} | Seed {seed} 失败：{str(e)}"
            print(err_msg)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] {img_file} | Seed {seed} | FAILED | {str(e)}\n")
            with open(md_report_path, "a", encoding="utf-8") as f:
                f.write(f"| {img_file} | {seed} | FAILED | - | {now_str} |\n")

print("\n🎉 NF4 全部参考图批量任务完成！")
print(f"📝 文本日志：{log_path}")
print(f"📋 Markdown报告：{md_report_path}")
```

## 2. Pruned Ref2VA｜批量多图 + Markdown报告完整版

```
import torch
import os
from datetime import datetime
from PIL import Image
from diffsynth.pipelines.minimax_h3_audio_video import MiniMaxH3Pipeline, ModelConfig
from diffsynth.utils.data.audio_video import write_video_audio

# ========= M4 Max Pruned Ref2VA 配置 =========
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

# --------------------------
# 【配置区】
# --------------------------
ref_images_dir = "./ref_images"
supported_exts = [".jpg", ".jpeg", ".png", ".webp"]
output_root_dir = "./batch_output_ref2va_pruned"
seed_list = [42, 10, 24, 66, 88, 123]

prompt = """
主体定义：<Subject1>是参考图中的人物，面部五官、发型、服装全程保持不变，脸型稳定，不会变脸。
视频概要：固定机位半身人像，自然眨眼，嘴唇和对白精准同步，微小自然头部微动，不剧烈转头。
保留分析：锁定参考图人物五官、肤色、发型、服装，场景和光照全程保持不变。
详细画面描述：柔和自然光，浅景深，写实人像，高清皮肤质感，稳定构图，画面不抖动。
音频描述：<Subject1>清晰自然人声，语气平稳，台词："本地部署MiniMax H3，可以一次性生成同步语音与视频。"，安静环境，轻微底噪，无背景音乐。
禁止：五官崩坏、手部畸形、画面闪烁、人物身份漂移、镜头移动、剧烈转头
"""

height = 480
width = 832
num_frames = 124
num_inference_steps = 50

# --------------------------
# 初始化日志 & Markdown报告
# --------------------------
os.makedirs(output_root_dir, exist_ok=True)
log_path = os.path.join(output_root_dir, "batch_log.txt")
md_report_path = os.path.join(output_root_dir, "report.md")

# 如果md文件不存在，写入表头
if not os.path.exists(md_report_path):
    with open(md_report_path, "w", encoding="utf-8") as f:
        f.write("# Pruned Ref2VA 批量生成结果报告\n\n")
        f.write(f"任务启动：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"参考图目录：`{ref_images_dir}`\n")
        f.write(f"Seed列表：{seed_list}\n\n")
        f.write("| 参考图 | Seed | 状态 | 文件路径 | 时间 |\n")
        f.write("|--------|------|------|----------|------|\n")

# 写入txt总日志头部
with open(log_path, "a", encoding="utf-8") as f:
    f.write("=" * 70 + "\n")
    f.write(f"【Pruned Ref2VA】批量多图任务启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"参考图片目录：{ref_images_dir}\n")
    f.write(f"输出根目录：{output_root_dir}\n")
    f.write(f"分辨率：{width}x{height} | 帧数：{num_frames} | 推理步数：{num_inference_steps}\n")
    f.write(f"Seed列表：{', '.join(map(str, seed_list))}\n")
    f.write(f"Prompt:\n{prompt}\n")
    f.write("=" * 70 + "\n")

# --------------------------
# 加载 Pruned 模型：只加载一次
# --------------------------
pipe = MiniMaxH3Pipeline.from_pretrained(
    torch_dtype=torch.bfloat16,
    device="mps",
    model_configs=[
        ModelConfig(model_id="DiffSynth-Studio/MiniMax-H3-Pruned", origin_file_pattern="minimax-h3-ref2va-pruned.safetensors", **vram_config),
        ModelConfig(model_id="DiffSynth-Studio/MiniMax-H3-Pruned", origin_file_pattern="minimax-h3-text-encoder-pruned.safetensors", **vram_config),
        ModelConfig(model_id="DiffSynth-Studio/MiniMax-H3-Pruned", origin_file_pattern="video_vae-pruned.safetensors", **vram_config),
        ModelConfig(model_id="DiffSynth-Studio/MiniMax-H3-Pruned", origin_file_pattern="audio_vae-pruned.safetensors", **vram_config),
    ],
    processor_config=ModelConfig(model_id="MiniMax/MiniMax-H3", origin_file_pattern="Ref2VA/processor/"),
    vram_limit=96,
)

# --------------------------
# 遍历多张参考图
# --------------------------
if not os.path.exists(ref_images_dir):
    raise FileNotFoundError(f"参考图片目录不存在：{ref_images_dir}\n请先创建目录并放入人像图片。")

image_files = [
    f for f in os.listdir(ref_images_dir)
    if os.path.splitext(f)[1].lower() in supported_exts
]

if not image_files:
    raise FileNotFoundError(f"在目录 {ref_images_dir} 中未找到支持的图片文件。支持格式：{', '.join(supported_exts)}")

for img_file in image_files:
    img_stem = os.path.splitext(img_file)[0]
    img_path = os.path.join(ref_images_dir, img_file)
    output_dir = os.path.join(output_root_dir, img_stem)
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n==========================")
    print(f"处理参考图：{img_file}")
    print(f"输出目录：{output_dir}")
    print(f"==========================")

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"\n[{datetime.now()}] 开始处理图片：{img_file}\n")
        f.write(f"图片路径：{img_path}\n")
        f.write(f"输出目录：{output_dir}\n")

    try:
        ref_image = Image.open(img_path).convert("RGB")
    except Exception as e:
        print(f"❌ 无法打开图片：{img_file}，错误：{str(e)}")
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] 图片读取失败：{img_file} | {str(e)}\n")
        with open(md_report_path, "a", encoding="utf-8") as f:
            f.write(f"| {img_file} | - | READ_FAILED | - | {now_str} |\n")
        continue

    for seed in seed_list:
        output_file = os.path.join(output_dir, f"h3_pruned_seed_{seed}.mp4")
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if os.path.exists(output_file):
            info = f"⏭️ {img_file} | Seed {seed} 已存在，跳过"
            print(info)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] {img_file} | Seed {seed} | SKIPPED | 文件已存在\n")
            with open(md_report_path, "a", encoding="utf-8") as f:
                f.write(f"| {img_file} | {seed} | SKIPPED | `{output_file}` | {now_str} |\n")
            continue

        print(f"---------- 当前 Seed: {seed} ----------")
        try:
            video, audio = pipe(
                prompt=prompt,
                height=height,
                width=width,
                num_frames=num_frames,
                num_inference_steps=num_inference_steps,
                seed=seed,
                references=[{"type": "image", "image": ref_image}]
            )
            write_video_audio(
                video=video,
                audio=audio,
                output_path=output_file,
                fps=24,
                audio_sample_rate=32000,
            )
            info = f"✅ {img_file} | Seed {seed} 完成 -> {output_file}"
            print(info)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] {img_file} | Seed {seed} | SUCCESS | {output_file}\n")
            with open(md_report_path, "a", encoding="utf-8") as f:
                f.write(f"| {img_file} | {seed} | SUCCESS | `{output_file}` | {now_str} |\n")
        except Exception as e:
            err_msg = f"❌ {img_file} | Seed {seed} 失败：{str(e)}"
            print(err_msg)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] {img_file} | Seed {seed} | FAILED | {str(e)}\n")
            with open(md_report_path, "a", encoding="utf-8") as f:
                f.write(f"| {img_file} | {seed} | FAILED | - | {now_str} |\n")

print("\n🎉 Pruned 批量多图任务完成！")
print(f"📝 文本日志：{log_path}")
print(f"📋 Markdown报告：{md_report_path}")
```

## Markdown报告示例（report.md）

```
# Pruned Ref2VA 批量生成结果报告

任务启动：2026-09-02 16:30:00
参考图目录：`./ref_images`
Seed列表：[42, 10, 24, 66, 88, 123]

| 参考图 | Seed | 状态 | 文件路径 | 时间 |
|--------|------|------|----------|------|
| person_a.jpg | 42 | SUCCESS | `./batch_output_ref2va_pruned/person_a/h3_pruned_seed_42.mp4` | 2026-09-02 16:32:10 |
| person_a.jpg | 10 | SKIPPED | `./batch_output_ref2va_pruned/person_a/h3_pruned_seed_10.mp4` | 2026-09-02 16:32:15 |
| person_b.png | 42 | FAILED | - | 2026-09-02 16:35:20 |
```

## 状态说明

- `SUCCESS`：生成成功
- `SKIPPED`：文件已存在，断点跳过
- `FAILED`：推理过程报错
- `READ_FAILED`：图片读取失败

---

## 增加评分栏，可手动填写打分到Markdown表格，方便筛选最优视频

# 升级说明

本次更新2处核心改动：

1. **Markdown表格新增「评分」列**
   - 默认空单元格，**手动填写分数**（推荐1~10分，越高效果越好）
   - 保留原有全部字段：参考图 / Seed / 状态 / 文件路径 / 时间，新增「评分」
2. **闭环评估指导框架**（放在report.md末尾）>

> 完整闭环：批量生成 → 人工打分 → 数据分析 → 参数迭代 → 再次批量生成
> 框架自带筛选规则、常见失败原因、调参建议，每次跑完直接在报告里查看优化方向。

>
> 兼容原有断点续跑、双日志、多参考图循环，不会破坏已有记录。
> ⚠️ 注意：脚本不会自动覆盖你**手动填入的评分**；只要不删除`report.md`，再次运行只会追加新行，原有行的手动打分保留。

## 1. NF4 Ref2VA｜批量多图 + Markdown报告（含评分栏+闭环框架）

```
import torch
import os
from datetime import datetime
from PIL import Image
from diffsynth.pipelines.minimax_h3_audio_video import MiniMaxH3Pipeline, ModelConfig
from diffsynth.utils.data.audio_video import write_video_audio

# ========= M4 Max 128GB NF4 Ref2VA 配置 =========
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

# --------------------------
# 【配置区】
# --------------------------
ref_images_dir = "./ref_images"
supported_exts = [".jpg", ".jpeg", ".png", ".webp"]
output_root_dir = "./batch_output_ref2va"
seed_list = [42, 10, 24, 66, 88, 123]

prompt = """
主体定义：<Subject1>是参考图中的人物，面部五官、发型、服装全程保持不变，脸型稳定，不会变脸。
视频概要：固定机位半身人像，自然眨眼，嘴唇和对白精准同步，微小自然头部微动，不剧烈转头。
保留分析：锁定参考图人物五官、肤色、发型、服装，场景和光照全程保持不变。
详细画面描述：柔和自然光，浅景深，写实人像，高清皮肤质感，稳定构图，画面不抖动。
音频描述：<Subject1>清晰自然人声，语气平稳，台词："本地部署MiniMax H3，可以一次性生成同步语音与视频。"，安静环境，轻微底噪，无背景音乐。
禁止：五官崩坏、手部畸形、画面闪烁、人物身份漂移、镜头移动、剧烈转头
"""

height = 480
width = 832
num_frames = 124
num_inference_steps = 50

# --------------------------
# 初始化日志 & Markdown报告
# --------------------------
os.makedirs(output_root_dir, exist_ok=True)
log_path = os.path.join(output_root_dir, "batch_log.txt")
md_report_path = os.path.join(output_root_dir, "report.md")

# 如果md文件不存在，写入表头 + 闭环评估框架模板
if not os.path.exists(md_report_path):
    with open(md_report_path, "w", encoding="utf-8") as f:
        f.write("# NF4 Ref2VA 批量生成结果报告\n\n")
        f.write(f"任务启动：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"参考图目录：`{ref_images_dir}`\n")
        f.write(f"Seed列表：{seed_list}\n\n")
        # 新增【评分】列
        f.write("| 参考图 | Seed | 状态 | 文件路径 | 时间 | 评分(1~10) |\n")
        f.write("|--------|------|------|----------|------|------------|\n")

# 写入txt总日志头部
with open(log_path, "a", encoding="utf-8") as f:
    f.write("=" * 70 + "\n")
    f.write(f"【NF4 Ref2VA】批量多图任务启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"参考图片目录：{ref_images_dir}\n")
    f.write(f"输出根目录：{output_root_dir}\n")
    f.write(f"分辨率：{width}x{height} | 帧数：{num_frames} | 推理步数：{num_inference_steps}\n")
    f.write(f"Seed列表：{', '.join(map(str, seed_list))}\n")
    f.write(f"Prompt:\n{prompt}\n")
    f.write("=" * 70 + "\n")

# --------------------------
# 加载模型：只加载一次
# --------------------------
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

# --------------------------
# 遍历多张参考图
# --------------------------
if not os.path.exists(ref_images_dir):
    raise FileNotFoundError(f"参考图片目录不存在：{ref_images_dir}\n请先创建目录并放入人像图片。")

image_files = [
    f for f in os.listdir(ref_images_dir)
    if os.path.splitext(f)[1].lower() in supported_exts
]

if not image_files:
    raise FileNotFoundError(f"在目录 {ref_images_dir} 中未找到支持的图片文件。支持格式：{', '.join(supported_exts)}")

for img_file in image_files:
    img_stem = os.path.splitext(img_file)[0]
    img_path = os.path.join(ref_images_dir, img_file)

    # 每张图一个独立输出目录
    output_dir = os.path.join(output_root_dir, img_stem)
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n==========================")
    print(f"处理参考图：{img_file}")
    print(f"输出目录：{output_dir}")
    print(f"==========================")

    # 写入单张图任务日志
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"\n[{datetime.now()}] 开始处理图片：{img_file}\n")
        f.write(f"图片路径：{img_path}\n")
        f.write(f"输出目录：{output_dir}\n")

    try:
        ref_image = Image.open(img_path).convert("RGB")
    except Exception as e:
        print(f"❌ 无法打开图片：{img_file}，错误：{str(e)}")
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] 图片读取失败：{img_file} | {str(e)}\n")
        # 评分单元格为空，手动填写
        with open(md_report_path, "a", encoding="utf-8") as f:
            f.write(f"| {img_file} | - | READ_FAILED | - | {now_str} |  |\n")
        continue

    # 每张图跑一组 seed
    for seed in seed_list:
        output_file = os.path.join(output_dir, f"h3_seed_{seed}.mp4")
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 断点续跑
        if os.path.exists(output_file):
            info = f"⏭️ {img_file} | Seed {seed} 已存在，跳过"
            print(info)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] {img_file} | Seed {seed} | SKIPPED | 文件已存在\n")
            with open(md_report_path, "a", encoding="utf-8") as f:
                f.write(f"| {img_file} | {seed} | SKIPPED | `{output_file}` | {now_str} |  |\n")
            continue

        print(f"---------- 当前 Seed: {seed} ----------")
        try:
            video, audio = pipe(
                prompt=prompt,
                height=height,
                width=width,
                num_frames=num_frames,
                num_inference_steps=num_inference_steps,
                seed=seed,
                references=[{"type": "image", "image": ref_image}]
            )
            write_video_audio(
                video=video,
                audio=audio,
                output_path=output_file,
                fps=24,
                audio_sample_rate=32000,
            )
            info = f"✅ {img_file} | Seed {seed} 完成 -> {output_file}"
            print(info)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] {img_file} | Seed {seed} | SUCCESS | {output_file}\n")
            with open(md_report_path, "a", encoding="utf-8") as f:
                f.write(f"| {img_file} | {seed} | SUCCESS | `{output_file}` | {now_str} |  |\n")
        except Exception as e:
            err_msg = f"❌ {img_file} | Seed {seed} 失败：{str(e)}"
            print(err_msg)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] {img_file} | Seed {seed} | FAILED | {str(e)}\n")
            with open(md_report_path, "a", encoding="utf-8") as f:
                f.write(f"| {img_file} | {seed} | FAILED | - | {now_str} |  |\n")

# ===================== 在报告末尾追加【闭环评估指导框架】=====================
framework_text = """
---
# 📊 闭环评估与迭代指导框架
> 工作闭环：批量生成视频 → 人工打分(1~10) → 筛选高分样本 → 参数复盘 → 更新Prompt/参数 → 新一轮批量测试

## 1. 打分标准（参考）
| 分数区间 | 评估标准 |
| ---- | ---- |
| 9~10 | 完美：人脸高度一致、口型对齐、无畸形、画面稳定，可直接交付 |
| 7~8 | 良好：人脸基本一致，轻微瑕疵，微调prompt即可优化 |
| 5~6 | 一般：人脸漂移/轻微手部崩坏，需要调整参考图或步数 |
| 3~4 | 较差：明显变脸、肢体崩坏，不推荐使用 |
| 1~2 | 失败：完全失真、画面闪烁，弃用 |

## 2. 筛选规则
1. 优先提取**每张参考图最高分Seed**，作为基准seed
2. 同一人物多个高分seed：对比口型同步、人脸一致性、动作自然度
3. 低分样本：归类问题类型，定位根因

## 3. 常见问题 & 调参方向
| 现象 | 优化建议 |
| ---- | ---- |
| 人脸漂移、变脸 | 更换高清正面参考图；强化prompt里人物锁定描述；提高推理步数 |
| 手部畸形 | prompt增加手部约束；使用更高质量参考图；减少大幅度动作描述 |
| 画面抖动闪烁 | 增加「稳定构图，画面不抖动」权重；减少头部旋转描述 |
| 口型不同步 | 检查台词；减少长句子；保持台词语速平稳 |
| 显存溢出推理失败 | 降低分辨率/减少总帧数；开启更多模型offload |

## 4. 迭代流程
1. 打分完成后，筛选Top3高分样本，记录对应Seed、Prompt、参数
2. 分析低分样本共性，修改Prompt、参考图、推理步数
3. 更新脚本配置，使用优选seed范围，开启新一轮批量生成
4. 对比新旧批次平均分，评估优化效果

## 5. 本次任务统计（手动更新）
- 总任务数：
- SUCCESS成功数量：
- FAILED失败数量：
- SKIPPED跳过数量：
- 平均评分：
- 最优样本（高分）清单：
"""
with open(md_report_path, "a", encoding="utf-8") as f:
    f.write(framework_text)

print("\n🎉 NF4 全部参考图批量任务完成！")
print(f"📝 文本日志：{log_path}")
print(f"📋 Markdown报告（含评分栏+闭环框架）：{md_report_path}")
```

## 2. Pruned Ref2VA｜批量多图 + Markdown报告（含评分栏+闭环框架）

```
import torch
import os
from datetime import datetime
from PIL import Image
from diffsynth.pipelines.minimax_h3_audio_video import MiniMaxH3Pipeline, ModelConfig
from diffsynth.utils.data.audio_video import write_video_audio

# ========= M4 Max Pruned Ref2VA 配置 =========
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

# --------------------------
# 【配置区】
# --------------------------
ref_images_dir = "./ref_images"
supported_exts = [".jpg", ".jpeg", ".png", ".webp"]
output_root_dir = "./batch_output_ref2va_pruned"
seed_list = [42, 10, 24, 66, 88, 123]

prompt = """
主体定义：<Subject1>是参考图中的人物，面部五官、发型、服装全程保持不变，脸型稳定，不会变脸。
视频概要：固定机位半身人像，自然眨眼，嘴唇和对白精准同步，微小自然头部微动，不剧烈转头。
保留分析：锁定参考图人物五官、肤色、发型、服装，场景和光照全程保持不变。
详细画面描述：柔和自然光，浅景深，写实人像，高清皮肤质感，稳定构图，画面不抖动。
音频描述：<Subject1>清晰自然人声，语气平稳，台词："本地部署MiniMax H3，可以一次性生成同步语音与视频。"，安静环境，轻微底噪，无背景音乐。
禁止：五官崩坏、手部畸形、画面闪烁、人物身份漂移、镜头移动、剧烈转头
"""

height = 480
width = 832
num_frames = 124
num_inference_steps = 50

# --------------------------
# 初始化日志 & Markdown报告
# --------------------------
os.makedirs(output_root_dir, exist_ok=True)
log_path = os.path.join(output_root_dir, "batch_log.txt")
md_report_path = os.path.join(output_root_dir, "report.md")

# 如果md文件不存在，写入表头 + 闭环评估框架模板
if not os.path.exists(md_report_path):
    with open(md_report_path, "w", encoding="utf-8") as f:
        f.write("# Pruned Ref2VA 批量生成结果报告\n\n")
        f.write(f"任务启动：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"参考图目录：`{ref_images_dir}`\n")
        f.write(f"Seed列表：{seed_list}\n\n")
        f.write("| 参考图 | Seed | 状态 | 文件路径 | 时间 | 评分(1~10) |\n")
        f.write("|--------|------|------|----------|------|------------|\n")

# 写入txt总日志头部
with open(log_path, "a", encoding="utf-8") as f:
    f.write("=" * 70 + "\n")
    f.write(f"【Pruned Ref2VA】批量多图任务启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"参考图片目录：{ref_images_dir}\n")
    f.write(f"输出根目录：{output_root_dir}\n")
    f.write(f"分辨率：{width}x{height} | 帧数：{num_frames} | 推理步数：{num_inference_steps}\n")
    f.write(f"Seed列表：{', '.join(map(str, seed_list))}\n")
    f.write(f"Prompt:\n{prompt}\n")
    f.write("=" * 70 + "\n")

# --------------------------
# 加载 Pruned 模型：只加载一次
# --------------------------
pipe = MiniMaxH3Pipeline.from_pretrained(
    torch_dtype=torch.bfloat16,
    device="mps",
    model_configs=[
        ModelConfig(model_id="DiffSynth-Studio/MiniMax-H3-Pruned", origin_file_pattern="minimax-h3-ref2va-pruned.safetensors", **vram_config),
        ModelConfig(model_id="DiffSynth-Studio/MiniMax-H3-Pruned", origin_file_pattern="minimax-h3-text-encoder-pruned.safetensors", **vram_config),
        ModelConfig(model_id="DiffSynth-Studio/MiniMax-H3-Pruned", origin_file_pattern="video_vae-pruned.safetensors", **vram_config),
        ModelConfig(model_id="DiffSynth-Studio/MiniMax-H3-Pruned", origin_file_pattern="audio_vae-pruned.safetensors", **vram_config),
    ],
    processor_config=ModelConfig(model_id="MiniMax/MiniMax-H3", origin_file_pattern="Ref2VA/processor/"),
    vram_limit=96,
)

# --------------------------
# 遍历多张参考图
# --------------------------
if not os.path.exists(ref_images_dir):
    raise FileNotFoundError(f"参考图片目录不存在：{ref_images_dir}\n请先创建目录并放入人像图片。")

image_files = [
    f for f in os.listdir(ref_images_dir)
    if os.path.splitext(f)[1].lower() in supported_exts
]

if not image_files:
    raise FileNotFoundError(f"在目录 {ref_images_dir} 中未找到支持的图片文件。支持格式：{', '.join(supported_exts)}")

for img_file in image_files:
    img_stem = os.path.splitext(img_file)[0]
    img_path = os.path.join(ref_images_dir, img_file)
    output_dir = os.path.join(output_root_dir, img_stem)
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n==========================")
    print(f"处理参考图：{img_file}")
    print(f"输出目录：{output_dir}")
    print(f"==========================")

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"\n[{datetime.now()}] 开始处理图片：{img_file}\n")
        f.write(f"图片路径：{img_path}\n")
        f.write(f"输出目录：{output_dir}\n")

    try:
        ref_image = Image.open(img_path).convert("RGB")
    except Exception as e:
        print(f"❌ 无法打开图片：{img_file}，错误：{str(e)}")
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] 图片读取失败：{img_file} | {str(e)}\n")
        with open(md_report_path, "a", encoding="utf-8") as f:
            f.write(f"| {img_file} | - | READ_FAILED | - | {now_str} |  |\n")
        continue

    for seed in seed_list:
        output_file = os.path.join(output_dir, f"h3_pruned_seed_{seed}.mp4")
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if os.path.exists(output_file):
            info = f"⏭️ {img_file} | Seed {seed} 已存在，跳过"
            print(info)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] {img_file} | Seed {seed} | SKIPPED | 文件已存在\n")
            with open(md_report_path, "a", encoding="utf-8") as f:
                f.write(f"| {img_file} | {seed} | SKIPPED | `{output_file}` | {now_str} |  |\n")
            continue

        print(f"---------- 当前 Seed: {seed} ----------")
        try:
            video, audio = pipe(
                prompt=prompt,
                height=height,
                width=width,
                num_frames=num_frames,
                num_inference_steps=num_inference_steps,
                seed=seed,
                references=[{"type": "image", "image": ref_image}]
            )
            write_video_audio(
                video=video,
                audio=audio,
                output_path=output_file,
                fps=24,
                audio_sample_rate=32000,
            )
            info = f"✅ {img_file} | Seed {seed} 完成 -> {output_file}"
            print(info)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] {img_file} | Seed {seed} | SUCCESS | {output_file}\n")
            with open(md_report_path, "a", encoding="utf-8") as f:
                f.write(f"| {img_file} | {seed} | SUCCESS | `{output_file}` | {now_str} |  |\n")
        except Exception as e:
            err_msg = f"❌ {img_file} | Seed {seed} 失败：{str(e)}"
            print(err_msg)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] {img_file} | Seed {seed} | FAILED | {str(e)}\n")
            with open(md_report_path, "a", encoding="utf-8") as f:
                f.write(f"| {img_file} | {seed} | FAILED | - | {now_str} |  |\n")

# ===================== 在报告末尾追加【闭环评估指导框架】=====================
framework_text = """
---
# 📊 闭环评估与迭代指导框架
> 工作闭环：批量生成视频 → 人工打分(1~10) → 筛选高分样本 → 参数复盘 → 更新Prompt/参数 → 新一轮批量测试

## 1. 打分标准（参考）
| 分数区间 | 评估标准 |
| ---- | ---- |
| 9~10 | 完美：人脸高度一致、口型对齐、无畸形、画面稳定，可直接交付 |
| 7~8 | 良好：人脸基本一致，轻微瑕疵，微调prompt即可优化 |
| 5~6 | 一般：人脸漂移/轻微手部崩坏，需要调整参考图或步数 |
| 3~4 | 较差：明显变脸、肢体崩坏，不推荐使用 |
| 1~2 | 失败：完全失真、画面闪烁，弃用 |

## 2. 筛选规则
1. 优先提取**每张参考图最高分Seed**，作为基准seed
2. 同一人物多个高分seed：对比口型同步、人脸一致性、动作自然度
3. 低分样本：归类问题类型，定位根因

## 3. 常见问题 & 调参方向
| 现象 | 优化建议 |
| ---- | ---- |
| 人脸漂移、变脸 | 更换高清正面参考图；强化prompt里人物锁定描述；提高推理步数 |
| 手部畸形 | prompt增加手部约束；使用更高质量参考图；减少大幅度动作描述 |
| 画面抖动闪烁 | 增加「稳定构图，画面不抖动」权重；减少头部旋转描述 |
| 口型不同步 | 检查台词；减少长句子；保持台词语速平稳 |
| 显存溢出推理失败 | 降低分辨率/减少总帧数；开启更多模型offload |

## 4. 迭代流程
1. 打分完成后，筛选Top3高分样本，记录对应Seed、Prompt、参数
2. 分析低分样本共性，修改Prompt、参考图、推理步数
3. 更新脚本配置，使用优选seed范围，开启新一轮批量生成
4. 对比新旧批次平均分，评估优化效果

## 5. 本次任务统计（手动更新）
- 总任务数：
- SUCCESS成功数量：
- FAILED失败数量：
- SKIPPED跳过数量：
- 平均评分：
- 最优样本（高分）清单：
"""
with open(md_report_path, "a", encoding="utf-8") as f:
    f.write(framework_text)

print("\n🎉 Pruned 批量多图任务完成！")
print(f"📝 文本日志：{log_path}")
print(f"📋 Markdown报告（含评分栏+闭环框架）：{md_report_path}")
```

## Markdown表格示例

```
| 参考图 | Seed | 状态 | 文件路径 | 时间 | 评分(1~10) |
|--------|------|------|----------|------|------------|
| person_a.jpg | 42 | SUCCESS | `./batch_output_ref2va_pruned/person_a/h3_pruned_seed_42.mp4` | 2026-09-02 16:32:10 | 8 |
| person_a.jpg | 10 | SKIPPED | `./batch_output_ref2va_pruned/person_a/h3_pruned_seed_10.mp4` | 2026-09-02 16:32:15 | 6 |
| person_b.png | 42 | FAILED | - | 2026-09-02 16:35:20 |  |
```

---

## 增加**自动统计脚本**：独立小python脚本，读取report.md自动计算平均分、topN高分样本，直接输出最优seed清单

# 独立统计脚本 `analyze_report.py`

功能说明：

1. 读取你上面生成的 `report.md`
2. 解析表格，提取：参考图、Seed、状态、评分
3. 过滤 `SUCCESS` 样本，自动计算平均分
4. 输出 TopN 高分样本（可配置top数量，默认Top5）
5. 汇总：成功/失败/跳过数量、最优Seed清单、按人物分组最高分
6. 支持打印到控制台，也可选输出 `analysis_result.md` 分析报告

> 使用方式：放在和report.md同一个文件夹，直接运行
>
> ```bash
> python analyze_report.py
> ```

```python
import re
from pathlib import Path
from dataclasses import dataclass
from typing import List

# ===================== 配置区 =====================
REPORT_MD_PATH = Path("report.md")
OUTPUT_ANALYSIS_MD = Path("analysis_result.md")
TOP_N = 5   # 取前N高分样本
# =================================================

@dataclass
class VideoRecord:
    ref_img: str
    seed: str
    status: str
    file_path: str
    time_str: str
    score: float | None

def parse_markdown_table(md_text: str) -> List[VideoRecord]:
    """解析report.md里的结果表格"""
    # 匹配markdown表格行，跳过表头分割行
    pattern = re.compile(
        r"\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|"
    )
    lines = md_text.splitlines()
    records: List[VideoRecord] = []

    for line in lines:
        line = line.strip()
        if not line.startswith("|"):
            continue
        if "----" in line:  # 跳过分隔线
            continue
        match = pattern.match(line)
        if not match:
            continue
        ref_img, seed, status, fp, ts, score_str = match.groups()
        ref_img = ref_img.strip()
        seed = seed.strip()
        status = status.strip()
        fp = fp.strip()
        ts = ts.strip()
        score_str = score_str.strip()

        score = None
        if score_str and score_str.replace(".", "").isdigit():
            score = float(score_str)

        rec = VideoRecord(
            ref_img=ref_img,
            seed=seed,
            status=status,
            file_path=fp,
            time_str=ts,
            score=score
        )
        records.append(rec)
    return records


def main():
    if not REPORT_MD_PATH.exists():
        print(f"❌ 文件不存在：{REPORT_MD_PATH}")
        return

    md_content = REPORT_MD_PATH.read_text(encoding="utf-8")
    records = parse_markdown_table(md_content)
    if not records:
        print("⚠️ 没有解析到任何表格记录，请检查report.md表格格式")
        return

    # 统计各类状态
    stat_success = [r for r in records if r.status == "SUCCESS"]
    stat_failed = [r for r in records if r.status == "FAILED"]
    stat_skipped = [r for r in records if r.status == "SKIPPED"]
    stat_read_fail = [r for r in records if r.status == "READ_FAILED"]

    # 有效打分样本：SUCCESS 并且有填写分数
    scored_samples = [r for r in stat_success if r.score is not None]
    scored_samples_sorted = sorted(scored_samples, key=lambda x: x.score, reverse=True)
    top_samples = scored_samples_sorted[:TOP_N]

    # 计算平均分
    avg_score = sum(r.score for r in scored_samples) / len(scored_samples) if scored_samples else 0

    # 按参考图分组，取每个人最高分
    group_best = {}
    for rec in scored_samples:
        img = rec.ref_img
        if img not in group_best or rec.score > group_best[img].score:
            group_best[img] = rec

    # ========== 控制台输出 ==========
    print("="*70)
    print("📊 Ref2VA批量结果自动统计")
    print("="*70)
    print(f"总记录条数：{len(records)}")
    print(f"✅ SUCCESS：{len(stat_success)}")
    print(f"❌ FAILED：{len(stat_failed)}")
    print(f"⏭️ SKIPPED：{len(stat_skipped)}")
    print(f"🖼️ READ_FAILED：{len(stat_read_fail)}")
    print(f"📝 有效打分样本数量：{len(scored_samples)}")
    print(f"⭐ 全部有效样本平均分：{avg_score:.2f}")
    print("-"*70)
    print(f"🏆 Top {TOP_N} 高分样本：")
    for idx, item in enumerate(top_samples, 1):
        print(f"[{idx}] 参考图：{item.ref_img} | Seed：{item.seed} | 评分：{item.score}")

    print("-"*70)
    print("👤 每张参考图最优样本清单：")
    for img, rec in group_best.items():
        print(f"· {img} | Best Seed={rec.seed} | Score={rec.score}")

    all_best_seeds = sorted({rec.seed for rec in group_best.values()})
    print("\n✅ 全局最优Seed集合（各人物最高分去重）：")
    print(all_best_seeds)

    # ========== 输出独立分析markdown报告 analysis_result.md ==========
    md_out = []
    md_out.append("# Ref2VA 批量生成自动分析报告")
    md_out.append("")
    md_out.append(f"统计源文件：`{REPORT_MD_PATH.name}`")
    md_out.append(f"统计时间：{Path().cwd()}")
    md_out.append("")
    md_out.append("## 基础汇总")
    md_out.append(f"- 总记录：{len(records)}")
    md_out.append(f"- SUCCESS：{len(stat_success)}")
    md_out.append(f"- FAILED：{len(stat_failed)}")
    md_out.append(f"- SKIPPED：{len(stat_skipped)}")
    md_out.append(f"- READ_FAILED：{len(stat_read_fail)}")
    md_out.append(f"- 有效打分样本：{len(scored_samples)}")
    md_out.append(f"- 有效样本平均分：**{avg_score:.2f}**")
    md_out.append("")

    md_out.append(f"## Top{TOP_N} 高分样本")
    md_out.append("| 排名 | 参考图 | Seed | 评分 | 文件路径 |")
    md_out.append("|------|--------|------|------|----------|")
    for i, s in enumerate(top_samples, 1):
        md_out.append(f"| {i} | {s.ref_img} | {s.seed} | {s.score} | {s.file_path} |")
    md_out.append("")

    md_out.append("## 每张参考图最优样本")
    md_out.append("| 参考图 | Best Seed | 最高分 | 文件路径 |")
    md_out.append("|--------|-----------|--------|----------|")
    for img, rec in group_best.items():
        md_out.append(f"| {img} | {rec.seed} | {rec.score} | {rec.file_path} |")
    md_out.append("")

    md_out.append("## 推荐最优Seed清单（去重）")
    md_out.append(f"`{all_best_seeds}`")
    md_out.append("")
    md_out.append("> 使用建议：下一轮批量测试优先使用本清单内Seed，聚焦高分参数做迭代")

    OUTPUT_ANALYSIS_MD.write_text("\n".join(md_out), encoding="utf-8")
    print(f"\n📄 分析报告已保存到：{OUTPUT_ANALYSIS_MD}")


if __name__ == "__main__":
    main()
```

## 使用说明

1. 将 `analyze_report.py` 和 `report.md` 放在同一个文件夹
2. 人工在 `report.md` 的「评分(1~10)」列填好分数（空单元格会自动忽略）
3. 运行：`python analyze_report.py`
4. 控制台直接输出汇总 + TopN高分 + 每个人物最优seed；同时生成 `analysis_result.md`

## 示例控制台输出

```
======================================================================
📊 Ref2VA批量结果自动统计
======================================================================
总记录条数：12
✅ SUCCESS：8
❌ FAILED：2
⏭️ SKIPPED：2
🖼️ READ_FAILED：0
📝 有效打分样本数量：8
⭐ 全部有效样本平均分：7.12
----------------------------------------------------------------------
🏆 Top 5 高分样本：
[1] 参考图：person_a.jpg | Seed：42 | 评分：9.0
[2] 参考图：person_c.png | Seed：24 | 评分：8.5
[3] 参考图：person_a.jpg | Seed：10 | 评分：7.5
[4] 参考图：person_b.jpg | Seed：66 | 评分：7.0
[5] 参考图：person_c.png | Seed：88 | 评分：6.8
----------------------------------------------------------------------
👤 每张参考图最优样本清单：
· person_a.jpg | Best Seed=42 | Score=9.0
· person_b.jpg | Best Seed=66 | Score=7.0
· person_c.png | Best Seed=24 | Score=8.5

✅ 全局最优Seed集合（各人物最高分去重）：
['42', '24', '66']

📄 分析报告已保存到：analysis_result.md
```

---

## 增加**问题标签列**（变脸/手崩/抖动/口型错位），统计各类缺陷占比

# 升级方案分2部分

1. **主生成脚本升级**：Markdown表格新增「缺陷标签」列，空单元格，人工填写，支持多标签逗号分隔：`变脸,手崩`
2. **analyze_report.py 统计脚本升级**：解析缺陷标签，统计各类缺陷出现频次，新增缺陷汇总表格

>
> 标签约定（统一，方便统计）
> 可选标签：`变脸` / `手崩` / `抖动` / `口型错位`，无缺陷填空

## 第一部分：主脚本（以NF4版本举例，Pruned版本仅改标题和输出文件名）

>
> 修改点：表头增加`缺陷标签`，每一行追加缺陷标签单元格，原有逻辑完全保留

```
import torch
import os
from datetime import datetime
from PIL import Image
from diffsynth.pipelines.minimax_h3_audio_video import MiniMaxH3Pipeline, ModelConfig
from diffsynth.utils.data.audio_video import write_video_audio

# ========= M4 Max 128GB NF4 Ref2VA 配置 =========
vram_config = {
    "offload_dtype": "cpu",
    "offload_device": "cpu",
    "onload_dtype": torch.bfloat16,
    "onload_device": "mps",
    "preparing_dtype": torch.bfloat16,
    "preparing_device": "mps",
    "computation_dtype": torch.bfloat16,
}

# --------------------------
# 【配置区】
# --------------------------
ref_images_dir = "./ref_images"
supported_exts = [".jpg", ".jpeg", ".png", ".webp"]
output_root_dir = "./batch_output_ref2va"
seed_list = [42, 10, 24, 66, 88, 123]

prompt = """
主体定义：<Subject1>是参考图中的人物，面部五官、发型、服装全程保持不变，脸型稳定，不会变脸。
视频概要：固定机位半身人像，自然眨眼，嘴唇和对白精准同步，微小自然头部微动，不剧烈转头。
保留分析：锁定参考图人物五官、肤色、发型、服装，场景和光照全程保持不变。
详细画面描述：柔和自然光，浅景深，写实人像，高清皮肤质感，稳定构图，画面不抖动。
音频描述：<Subject1>清晰自然人声，语气平稳，台词："本地部署MiniMax H3，可以一次性生成同步语音与视频。"，安静环境，轻微底噪，无背景音乐。
禁止：五官崩坏、手部畸形、画面闪烁、人物身份漂移、镜头移动、剧烈转头
"""

height = 480
width = 832
num_frames = 124
num_inference_steps = 50

# --------------------------
# 初始化日志 & Markdown报告
# --------------------------
os.makedirs(output_root_dir, exist_ok=True)
log_path = os.path.join(output_root_dir, "batch_log.txt")
md_report_path = os.path.join(output_root_dir, "report.md")

# 如果md文件不存在，写入表头，新增缺陷标签列
if not os.path.exists(md_report_path):
    with open(md_report_path, "w", encoding="utf-8") as f:
        f.write("# NF4 Ref2VA 批量生成结果报告\n\n")
        f.write(f"任务启动：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"参考图目录：`{ref_images_dir}`\n")
        f.write(f"Seed列表：{seed_list}\n\n")
        # ========= 新增【缺陷标签】列 =========
        f.write("| 参考图 | Seed | 状态 | 文件路径 | 时间 | 评分(1~10) | 缺陷标签 |\n")
        f.write("|--------|------|------|----------|------|------------|----------|\n")

# 写入txt总日志头部
with open(log_path, "a", encoding="utf-8") as f:
    f.write("=" * 70 + "\n")
    f.write(f"【NF4 Ref2VA】批量多图任务启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"参考图片目录：{ref_images_dir}\n")
    f.write(f"输出根目录：{output_root_dir}\n")
    f.write(f"分辨率：{width}x{height} | 帧数：{num_frames} | 推理步数：{num_inference_steps}\n")
    f.write(f"Seed列表：{', '.join(map(str, seed_list))}\n")
    f.write(f"Prompt:\n{prompt}\n")
    f.write("=" * 70 + "\n")

# --------------------------
# 加载模型：只加载一次
# --------------------------
pipe = MiniMaxH3Pipeline.from_pretrained(
    torch_dtype=torch.bfloat16,
    device="mps",
    model_configs=[
        ModelConfig(model_id="DiffSynth-Studio/MiniMax-H3-NF4", origin_file_pattern="minimax-h3-ref2va-nf4.safetensors",** vram_config),
        ModelConfig(model_id="DiffSynth-Studio/MiniMax-H3-NF4", origin_file_pattern="minimax-h3-text-encoder-nf4.safetensors", **vram_config),
        ModelConfig(model_id="DiffSynth-Studio/MiniMax-H3-NF4", origin_file_pattern="video_vae_nf4.safetensors",** vram_config),
        ModelConfig(model_id="DiffSynth-Studio/MiniMax-H3-NF4", origin_file_pattern="audio_vae_nf4.safetensors", **vram_config),
    ],
    processor_config=ModelConfig(model_id="MiniMax/MiniMax-H3", origin_file_pattern="Ref2VA/processor/"),
    vram_limit=96,
)

# --------------------------
# 遍历多张参考图
# --------------------------
if not os.path.exists(ref_images_dir):
    raise FileNotFoundError(f"参考图片目录不存在：{ref_images_dir}\n请先创建目录并放入人像图片。")

image_files = [
    f for f in os.listdir(ref_images_dir)
    if os.path.splitext(f)[1].lower() in supported_exts
]

if not image_files:
    raise FileNotFoundError(f"在目录 {ref_images_dir} 中未找到支持的图片文件。支持格式：{', '.join(supported_exts)}")

for img_file in image_files:
    img_stem = os.path.splitext(img_file)[0]
    img_path = os.path.join(ref_images_dir, img_file)

    # 每张图一个独立输出目录
    output_dir = os.path.join(output_root_dir, img_stem)
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n==========================")
    print(f"处理参考图：{img_file}")
    print(f"输出目录：{output_dir}")
    print(f"==========================")

    # 写入单张图任务日志
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"\n[{datetime.now()}] 开始处理图片：{img_file}\n")
        f.write(f"图片路径：{img_path}\n")
        f.write(f"输出目录：{output_dir}\n")

    try:
        ref_image = Image.open(img_path).convert("RGB")
    except Exception as e:
        print(f"❌ 无法打开图片：{img_file}，错误：{str(e)}")
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] 图片读取失败：{img_file} | {str(e)}\n")
        # 缺陷标签空单元格
        with open(md_report_path, "a", encoding="utf-8") as f:
            f.write(f"| {img_file} | - | READ_FAILED | - | {now_str} |  |  |\n")
        continue

    # 每张图跑一组 seed
    for seed in seed_list:
        output_file = os.path.join(output_dir, f"h3_seed_{seed}.mp4")
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 断点续跑
        if os.path.exists(output_file):
            info = f"⏭️ {img_file} | Seed {seed} 已存在，跳过"
            print(info)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] {img_file} | Seed {seed} | SKIPPED | 文件已存在\n")
            with open(md_report_path, "a", encoding="utf-8") as f:
                f.write(f"| {img_file} | {seed} | SKIPPED | `{output_file}` | {now_str} |  |  |\n")
            continue

        print(f"---------- 当前 Seed: {seed} ----------")
        try:
            video, audio = pipe(
                prompt=prompt,
                height=height,
                width=width,
                num_frames=num_frames,
                num_inference_steps=num_inference_steps,
                seed=seed,
                references=[{"type": "image", "image": ref_image}]
            )
            write_video_audio(
                video=video,
                audio=audio,
                output_path=output_file,
                fps=24,
                audio_sample_rate=32000,
            )
            info = f"✅ {img_file} | Seed {seed} 完成 -> {output_file}"
            print(info)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] {img_file} | Seed {seed} | SUCCESS | {output_file}\n")
            # 缺陷标签留空，人工填写
            with open(md_report_path, "a", encoding="utf-8") as f:
                f.write(f"| {img_file} | {seed} | SUCCESS | `{output_file}` | {now_str} |  |  |\n")
        except Exception as e:
            err_msg = f"❌ {img_file} | Seed {seed} 失败：{str(e)}"
            print(err_msg)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] {img_file} | Seed {seed} | FAILED | {str(e)}\n")
            with open(md_report_path, "a", encoding="utf-8") as f:
                f.write(f"| {img_file} | {seed} | FAILED | - | {now_str} |  |  |\n")

# ===================== 在报告末尾追加【闭环评估指导框架】=====================
framework_text = """
---
# 📊 闭环评估与迭代指导框架
> 工作闭环：批量生成视频 → 人工打分(1~10)+标记缺陷标签 → 筛选高分样本 → 参数复盘 → 更新Prompt/参数 → 新一轮批量测试

## 1. 打分标准（参考）
| 分数区间 | 评估标准 |
| ---- | ---- |
| 9~10 | 完美：人脸高度一致、口型对齐、无畸形、画面稳定，可直接交付 |
| 7~8 | 良好：人脸基本一致，轻微瑕疵，微调prompt即可优化 |
| 5~6 | 一般：人脸漂移/轻微手部崩坏，需要调整参考图或步数 |
| 3~4 | 较差：明显变脸、肢体崩坏，不推荐使用 |
| 1~2 | 失败：完全失真、画面闪烁，弃用 |

## 2. 缺陷标签说明（人工填写，多标签逗号分隔）
可选标签：`变脸`、`手崩`、`抖动`、`口型错位`
无缺陷：单元格留空

## 3. 筛选规则
1. 优先提取**每张参考图最高分Seed**，作为基准seed
2. 同一人物多个高分seed：对比口型同步、人脸一致性、动作自然度
3. 低分样本：归类缺陷标签，定位高频问题

## 4. 常见问题 & 调参方向
| 现象 | 优化建议 |
| ---- | ---- |
| 人脸漂移、变脸 | 更换高清正面参考图；强化prompt里人物锁定描述；提高推理步数 |
| 手部畸形(手崩) | prompt增加手部约束；使用更高质量参考图；减少大幅度动作描述 |
| 画面抖动闪烁 | 增加「稳定构图，画面不抖动」权重；减少头部旋转描述 |
| 口型不同步(口型错位) | 检查台词；减少长句子；保持台词语速平稳 |
| 显存溢出推理失败 | 降低分辨率/减少总帧数；开启更多模型offload |

## 5. 迭代流程
1. 打分完成+标记缺陷标签后，筛选Top3高分样本，记录对应Seed、Prompt、参数
2. 统计缺陷高频问题，修改Prompt、参考图、推理步数
3. 更新脚本配置，使用优选seed范围，开启新一轮批量生成
4. 对比新旧批次平均分+缺陷占比，评估优化效果

## 6. 本次任务统计（手动更新）
- 总任务数：
- SUCCESS成功数量：
- FAILED失败数量：
- SKIPPED跳过数量：
- 平均评分：
- 最优样本（高分）清单：
- 高频缺陷：
"""
with open(md_report_path, "a", encoding="utf-8") as f:
    f.write(framework_text)

print("\n🎉 NF4 全部参考图批量任务完成！")
print(f"📝 文本日志：{log_path}")
print(f"📋 Markdown报告（含评分栏+缺陷标签+闭环框架）：{md_report_path}")
```

>
> Pruned版本只需要修改：标题、output_root_dir、模型id，表格结构完全一致，不再重复贴完整代码

## 第二部分：升级 analyze_report.py（解析缺陷标签 + 缺陷统计）

```
import re
from collections import Counter
from pathlib import Path
from dataclasses import dataclass
from typing import List

# ===================== 配置区 =====================
REPORT_MD_PATH = Path("report.md")
OUTPUT_ANALYSIS_MD = Path("analysis_result.md")
TOP_N = 5
VALID_TAGS = {"变脸", "手崩", "抖动", "口型错位"}
# =================================================

@dataclass
class VideoRecord:
    ref_img: str
    seed: str
    status: str
    file_path: str
    time_str: str
    score: float | None
    tags: List[str] # 新增缺陷标签列表

def parse_markdown_table(md_text: str) -> List[VideoRecord]:
    """解析新增缺陷标签列的表格"""
    pattern = re.compile(
        r"\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|"
    )
    lines = md_text.splitlines()
    records: List[VideoRecord] = []

    for line in lines:
        line = line.strip()
        if not line.startswith("|"):
            continue
        if "----" in line:
            continue
        match = pattern.match(line)
        if not match:
            continue
        ref_img, seed, status, fp, ts, score_str, tag_str = match.groups()
        ref_img = ref_img.strip()
        seed = seed.strip()
        status = status.strip()
        fp = fp.strip()
        ts = ts.strip()
        score_str = score_str.strip()
        tag_str = tag_str.strip()

        score = None
        if score_str and score_str.replace(".", "").isdigit():
            score = float(score_str)

        # 拆分多标签
        tags = []
        if tag_str:
            raw_tags = [t.strip() for t in tag_str.split(",")]
            tags = [t for t in raw_tags if t in VALID_TAGS]

        rec = VideoRecord(
            ref_img=ref_img,
            seed=seed,
            status=status,
            file_path=fp,
            time_str=ts,
            score=score,
            tags=tags
        )
        records.append(rec)
    return records

def main():
    if not REPORT_MD_PATH.exists():
        print(f"❌ 文件不存在：{REPORT_MD_PATH}")
        return

    md_content = REPORT_MD_PATH.read_text(encoding="utf-8")
    records = parse_markdown_table(md_content)
    if not records:
        print("⚠️ 没有解析到任何表格记录，请检查report.md表格格式")
        return

    # 统计各类状态
    stat_success = [r for r in records if r.status == "SUCCESS"]
    stat_failed = [r for r in records if r.status == "FAILED"]
    stat_skipped = [r for r in records if r.status == "SKIPPED"]
    stat_read_fail = [r for r in records if r.status == "READ_FAILED"]

    # 有效打分样本：SUCCESS 并且有填写分数
    scored_samples = [r for r in stat_success if r.score is not None]
    scored_samples_sorted = sorted(scored_samples, key=lambda x: x.score, reverse=True)
    top_samples = scored_samples_sorted[:TOP_N]

    # 计算平均分
    avg_score = sum(r.score for r in scored_samples) / len(scored_samples) if scored_samples else 0

    # 按参考图分组，取每个人最高分
    group_best = {}
    for rec in scored_samples:
        img = rec.ref_img
        if img not in group_best or rec.score > group_best[img].score:
            group_best[img] = rec

    # 缺陷标签全局统计
    all_tags = []
    for rec in stat_success:
        all_tags.extend(rec.tags)
    tag_counter = Counter(all_tags)

    # ========== 控制台输出 ==========
    print("="*70)
    print("📊 Ref2VA批量结果自动统计（含缺陷标签）")
    print("="*70)
    print(f"总记录条数：{len(records)}")
    print(f"✅ SUCCESS：{len(stat_success)}")
    print(f"❌ FAILED：{len(stat_failed)}")
    print(f"⏭️ SKIPPED：{len(stat_skipped)}")
    print(f"🖼️ READ_FAILED：{len(stat_read_fail)}")
    print(f"📝 有效打分样本数量：{len(scored_samples)}")
    print(f"⭐ 全部有效样本平均分：{avg_score:.2f}")
    print("-"*70)
    print(f"🏆 Top {TOP_N} 高分样本：")
    for idx, item in enumerate(top_samples, 1):
        print(f"[{idx}] 参考图：{item.ref_img} | Seed：{item.seed} | 评分：{item.score} | 缺陷：{item.tags}")

    print("-"*70)
    print("👤 每张参考图最优样本清单：")
    for img, rec in group_best.items():
        print(f"· {img} | Best Seed={rec.seed} | Score={rec.score} | 缺陷：{rec.tags}")

    all_best_seeds = sorted({rec.seed for rec in group_best.values()})
    print("\n✅ 全局最优Seed集合（各人物最高分去重）：")
    print(all_best_seeds)

    print("-"*70)
    print("🔍 缺陷频次统计（SUCCESS样本）：")
    for tag, cnt in tag_counter.most_common():
        print(f"{tag}：{cnt}次")

    # ========== 输出独立分析markdown报告 analysis_result.md ==========
    md_out = []
    md_out.append("# Ref2VA 批量生成自动分析报告（含缺陷统计）")
    md_out.append("")
    md_out.append(f"统计源文件：`{REPORT_MD_PATH.name}`")
    md_out.append("")
    md_out.append("## 基础汇总")
    md_out.append(f"- 总记录：{len(records)}")
    md_out.append(f"- SUCCESS：{len(stat_success)}")
    md_out.append(f"- FAILED：{len(stat_failed)}")
    md_out.append(f"- SKIPPED：{len(stat_skipped)}")
    md_out.append(f"- READ_FAILED：{len(stat_read_fail)}")
    md_out.append(f"- 有效打分样本：{len(scored_samples)}")
    md_out.append(f"- 有效样本平均分：**{avg_score:.2f}**")
    md_out.append("")

    md_out.append("## 缺陷频次统计（成功样本）")
    md_out.append("| 缺陷类型 | 出现次数 |")
    md_out.append("|----------|----------|")
    for tag, cnt in tag_counter.most_common():
        md_out.append(f"| {tag} | {cnt} |")
    if not tag_counter:
        md_out.append("| 无 | 0 |")
    md_out.append("")

    md_out.append(f"## Top{TOP_N} 高分样本")
    md_out.append("| 排名 | 参考图 | Seed | 评分 | 缺陷标签 | 文件路径 |")
    md_out.append("|------|--------|------|------|----------|----------|")
    for i, s in enumerate(top_samples, 1):
        tag_txt = ",".join(s.tags) if s.tags else "无"
        md_out.append(f"| {i} | {s.ref_img} | {s.seed} | {s.score} | {tag_txt} | {s.file_path} |")
    md_out.append("")

    md_out.append("## 每张参考图最优样本")
    md_out.append("| 参考图 | Best Seed | 最高分 | 缺陷标签 | 文件路径 |")
    md_out.append("|--------|-----------|--------|----------|----------|")
    for img, rec in group_best.items():
        tag_txt = ",".join(rec.tags) if rec.tags else "无"
        md_out.append(f"| {img} | {rec.seed} | {rec.score} | {tag_txt} | {rec.file_path} |")
    md_out.append("")

    md_out.append("## 推荐最优Seed清单（去重）")
    md_out.append(f"`{all_best_seeds}`")
    md_out.append("")
    md_out.append("> 使用建议：下一轮批量测试优先使用本清单内Seed；优先针对高频缺陷优化Prompt/参考图")

    OUTPUT_ANALYSIS_MD.write_text("\n".join(md_out), encoding="utf-8")
    print(f"\n📄 分析报告已保存到：{OUTPUT_ANALYSIS_MD}")

if __name__ == "__main__":
    main()
```

## 使用示例 report.md 表格

```
| 参考图 | Seed | 状态 | 文件路径 | 时间 | 评分(1~10) | 缺陷标签 |
|--------|------|------|----------|------|------------|----------|
| person_a.jpg | 42 | SUCCESS | `./batch_output_ref2va/person_a/h3_seed_42.mp4` | 2026-09-02 16:32:10 | 9 |  |
| person_a.jpg | 10 | SUCCESS | `./batch_output_ref2va/person_a/h3_seed_10.mp4` | 2026-09-02 16:32:15 | 6 | 手崩,抖动 |
| person_b.png | 42 | FAILED | - | 2026-09-02 16:35:20 |  |  |
```

## 控制台新增输出示例

```
----------------------------------------------------------------------
🔍 缺陷频次统计（SUCCESS样本）：
手崩：3次
抖动：2次
变脸：1次
```

---

## 自动读取analysis_result.md，**自动更新主脚本seed_list**，一键把最优seed写入批量脚本

# 新增独立脚本 `update_seed_list.py`

功能：

1. 读取 `analysis_result.md`，提取【推荐最优Seed清单】
2. 自动找到主生成脚本（可配置脚本文件名）
3. 自动替换脚本里的 `seed_list = [xxx]`
4. 生成备份 `xxx.bak`，防止原脚本丢失

> ⚠️ 约束：主脚本里必须保留这一行原样写法：`seed_list = [数字,数字...]`，不能拆多行，方便正则匹配

## update_seed_list.py

```python
import re
from pathlib import Path

# ===================== 配置区 =====================
# 分析结果文件
ANALYSIS_MD = Path("analysis_result.md")
# 你的批量生成主脚本，按需改成 NF4 或者 Pruned 的py文件名
MAIN_SCRIPT = Path("batch_ref2va_nf4.py")
# MAIN_SCRIPT = Path("batch_ref2va_pruned.py")
# =================================================

def extract_best_seeds(md_path: Path):
    """从 analysis_result.md 提取最优seed列表"""
    if not md_path.exists():
        print(f"❌ {md_path} 不存在，请先运行 analyze_report.py")
        return None
    content = md_path.read_text(encoding="utf-8")
    # 匹配 `[42,24,66]` 格式
    pattern = re.compile(r"推荐最优Seed清单（去重）\n`(\[.*?\])`")
    match = pattern.search(content)
    if not match:
        print("❌ 未找到最优Seed清单，请确认analysis_result.md已正常生成")
        return None
    seed_str = match.group(1)
    try:
        seed_list = eval(seed_str)
        if not isinstance(seed_list, list):
            raise ValueError("不是列表")
        # 全部转为int，去重+排序
        seed_list = sorted(list({int(s) for s in seed_list}))
        return seed_list
    except Exception as e:
        print(f"❌ Seed解析失败：{e}")
        return None


def replace_seed_in_script(script_path: Path, new_seed_list):
    # 读取原脚本
    src = script_path.read_text(encoding="utf-8")
    # 正则匹配 seed_list = [xxx]
    pat = re.compile(r"(seed_list\s*=\s*)\[.*?\]")
    new_line = rf"\1{new_seed_list}"
    new_src = pat.sub(new_line, src)
    # 备份原脚本
    bak_file = script_path.with_suffix(".bak")
    script_path.write_text(src, encoding="utf-8")
    bak_file.write_text(src, encoding="utf-8")
    # 写入更新后脚本
    script_path.write_text(new_src, encoding="utf-8")
    return True


def main():
    best_seeds = extract_best_seeds(ANALYSIS_MD)
    if best_seeds is None:
        return
    print(f"✅ 提取到最优Seed列表：{best_seeds}")
    if not MAIN_SCRIPT.exists():
        print(f"❌ 主脚本文件 {MAIN_SCRIPT} 不存在！")
        return
    ok = replace_seed_in_script(MAIN_SCRIPT, best_seeds)
    if ok:
        print(f"\n🎉 成功更新 {MAIN_SCRIPT.name} 的 seed_list！")
        print(f"📌 原脚本已备份：{MAIN_SCRIPT.name}.bak")
        print(f"新seed_list = {best_seeds}")
    else:
        print("❌ 更新失败")


if __name__ == "__main__":
    main()
```

# 完整闭环工作流程（整套流水线）

```
1. 运行 batch_ref2va_nf4.py → 生成视频 + report.md
2. 人工观看视频，在 report.md 填写【评分】+【缺陷标签】
3. 运行 analyze_report.py → 读取report.md，输出analysis_result.md（含最优seed）
4. 运行 update_seed_list.py → 读取analysis_result.md，自动修改主脚本seed_list
5. 直接再次运行主脚本，只用最优seed做下一轮迭代测试
```

## 使用方法

1. 把 `update_seed_list.py` 放在和主脚本、analysis_result.md 同一个目录
2. 修改脚本配置区的 `MAIN_SCRIPT`，选择是NF4还是Pruned版本
3. 执行：

```bash
python update_seed_list.py
```

## 示例控制台输出

```
✅ 提取到最优Seed列表：[24,42,66]

🎉 成功更新 batch_ref2va_nf4.py 的 seed_list！
📌 原脚本已备份：batch_ref2va_nf4.py.bak
新seed_list = [24, 42, 66]
```

## ⚠️ 重要注意事项

1. 主脚本中 `seed_list = [xxx]` **不能拆分成多行**，必须一行写完
✅ 正确：

```python
seed_list = [42, 10, 24, 66, 88, 123]
```

❌ 错误（多行会匹配失败）

```python
seed_list = [
42,
10
]
```

1. 每次更新自动生成 `.bak` 备份，出问题直接把bak重命名回py即可恢复
2. 如果上一轮打分样本为空（没有评分），`analyze_report.py`不会产生有效seed，更新脚本会直接退出

---

## 一键打包全流程：单脚本一键依次执行生成→分析→更新seed

# `pipeline_auto.py` 一键全流程脚本

功能：**串行执行：批量生成视频 → 分析report → 自动更新seed_list**
> 注意：人工打分标记缺陷这一步无法自动化（必须人看视频填report.md），所以提供两种模式：
>
> 1. `auto_run=True`：完整流水线（生成视频 → 自动分析 → 更新seed），适合**已经提前填好上一轮report**的场景
> 2. `auto_run=False`：仅生成视频，暂停，等待你人工打开report.md填写评分、缺陷标签，再手动继续分析+更新seed（最常用）

```python
import subprocess
import sys
from pathlib import Path

# ====================== 配置区【按需修改】======================
# 主生成脚本（NF4 / Pruned 二选一）
MAIN_GENERATE_SCRIPT = Path("batch_ref2va_nf4.py")
# MAIN_GENERATE_SCRIPT = Path("batch_ref2va_pruned.py")
ANALYZE_SCRIPT = Path("analyze_report.py")
UPDATE_SEED_SCRIPT = Path("update_seed_list.py")

# 模式开关
AUTO_AFTER_GENERATE = False   # False = 生成完成后暂停，等待人工填写report；True = 生成完直接分析+更新seed
# ==============================================================

def run_script(script_path: Path, desc: str):
    """执行子脚本，捕获输出"""
    if not script_path.exists():
        print(f"\n❌ 【{desc}】文件不存在：{script_path}")
        sys.exit(1)
    print(f"\n===== 开始执行：{desc} 【{script_path.name}】 =====")
    ret = subprocess.run([sys.executable, str(script_path)], capture_output=False)
    if ret.returncode != 0:
        print(f"\n❌ 【{desc}】执行失败，退出码：{ret.returncode}")
        sys.exit(ret.returncode)
    print(f"✅ 【{desc}】执行完成\n")


def main():
    print("="*80)
    print("🚀 Ref2VA 一键迭代流水线")
    print("流程：生成视频 →（人工填写report）→ 分析报告 → 更新最优Seed")
    print("="*80)

    # Step1：运行批量生成脚本
    run_script(MAIN_GENERATE_SCRIPT, "批量视频生成")

    if not AUTO_AFTER_GENERATE:
        input("\n⏸️ 暂停！请打开 report.md，填写评分和缺陷标签，填写完成后按回车继续执行分析+更新Seed...")

    # Step2：运行分析脚本 analyze_report.py
    run_script(ANALYZE_SCRIPT, "报告分析 & 缺陷统计")

    # Step3：运行更新seed脚本 update_seed_list.py
    run_script(UPDATE_SEED_SCRIPT, "自动更新主脚本seed_list")

    print("\n🎉 流水线全部执行完毕！准备好进入下一轮迭代。")


if __name__ == "__main__":
    main()
```

## 文件目录结构（全部放在同一文件夹）

```
├─ pipeline_auto.py          # 一键流水线入口
├─ batch_ref2va_nf4.py       # 主生成脚本
├─ analyze_report.py         # 统计分析脚本
├─ update_seed_list.py       # seed自动更新脚本
├─ report.md                 # 生成后输出的评估表格
├─ analysis_result.md        # analyze输出的分析结果
```

## 使用方法

1. 修改 `pipeline_auto.py` 配置区，选择NF4或者Pruned生成脚本
2. 运行：

```bash
python pipeline_auto.py
```

### 推荐工作模式（AUTO_AFTER_GENERATE=False 默认）

1. 启动流水线，自动运行 `batch_ref2va_nf4.py`，生成视频+report.md
2. 脚本暂停，提示：**人工打开 report.md，填写评分和缺陷标签**
3. 填完后回车，自动执行 `analyze_report.py` 统计，再执行 `update_seed_list.py` 更新seed_list
4. 下一轮直接再次运行 `pipeline_auto.py`，使用新的最优seed生成

### 全自动模式（AUTO_AFTER_GENERATE=True）

适合场景：你已经预先填好了report.md，不需要人工介入，一键跑完整套迭代。
> ⚠️ 注意：如果新生成视频后没有人工打分，分析脚本会读空评分，无法算出有效最优seed。

## 约束提醒（整套流水线必须遵守）

1. 主脚本 `seed_list = [数字,...]` **必须单行书写**，不能换行（update_seed_list.py正则依赖）
2. 所有py文件放在同一目录
3. 每轮更新主脚本时会自动生成 `.bak` 备份，出错可以回滚

---
整套流水线完整链路：
`pipeline_auto.py` → batch_ref2va → report.md → 人工打分标记缺陷 → analyze_report → analysis_result.md → update_seed_list → 更新主脚本seed_list

## 在流水线中增加批次命名，自动生成`report_batch01.md`，多轮迭代分开保存，不会覆盖旧报告，方便对比多批次效果

# 改造方案说明

1. 增加批次号自动递增，文件命名：`report_batch01.md`、`report_batch02.md`、`analysis_result_batch01.md`
2. 修改主生成脚本，支持传入批次参数，输出带批次后缀的报告，不再固定`report.md`
3. 修改`analyze_report.py`，接收批次号读取对应批次报告、输出带批次的分析文件
4. 修改`pipeline_auto.py`自动检测下一个批次号，串联整套流程
5. 所有批次文件互不覆盖，历史迭代全部保留，方便横向对比

> 改动清单：
>
> - `pipeline_auto.py`：自动寻找最大批次号，生成下一批次编号，作为参数传给下游脚本
> - `batch_ref2va_nf4.py`：支持`--batch`入参，输出`report_batchXX.md`
> - `analyze_report.py`：支持`--batch`入参，读取`report_batchXX.md`，输出`analysis_result_batchXX.md`
> - `update_seed_list.py`：读取对应批次的`analysis_result_batchXX.md`

## ① pipeline_auto.py（流水线入口，自动批次号）

```python
import subprocess
import sys
import re
from pathlib import Path

# ====================== 配置区【按需修改】======================
MAIN_GENERATE_SCRIPT = Path("batch_ref2va_nf4.py")
# MAIN_GENERATE_SCRIPT = Path("batch_ref2va_pruned.py")
ANALYZE_SCRIPT = Path("analyze_report.py")
UPDATE_SEED_SCRIPT = Path("update_seed_list.py")
AUTO_AFTER_GENERATE = False
# ==============================================================

def get_next_batch_id() -> int:
    """扫描目录找到最大批次号，返回下一个批次编号"""
    p = Path(".")
    pattern = re.compile(r"report_batch(\d+)\.md")
    max_b = 0
    for f in p.glob("report_batch*.md"):
        m = pattern.match(f.name)
        if m:
            num = int(m.group(1))
            if num > max_b:
                max_b = num
    return max_b + 1

def run_script(script_path: Path, desc: str, batch_id:int=None):
    if not script_path.exists():
        print(f"\n❌ 【{desc}】文件不存在：{script_path}")
        sys.exit(1)
    cmd = [sys.executable, str(script_path)]
    if batch_id is not None:
        cmd += ["--batch", f"{batch_id:02d}"]
    print(f"\n===== 开始执行：{desc} 【{script_path.name}】 =====")
    ret = subprocess.run(cmd, capture_output=False)
    if ret.returncode != 0:
        print(f"\n❌ 【{desc}】执行失败，退出码：{ret.returncode}")
        sys.exit(ret.returncode)
    print(f"✅ 【{desc}】执行完成\n")

def main():
    print("="*80)
    print("🚀 Ref2VA 一键迭代流水线【批次隔离版】")
    print("流程：生成视频 →（人工填写report_batchXX.md）→ 分析报告 → 更新最优Seed")
    print("="*80)
    batch_id = get_next_batch_id()
    batch_str = f"{batch_id:02d}"
    print(f"👉 当前批次：batch{batch_str}")
    print(f"📄 本次报告文件：report_batch{batch_str}.md")

    run_script(MAIN_GENERATE_SCRIPT, "批量视频生成", batch_id)

    if not AUTO_AFTER_GENERATE:
        input(f"\n⏸️ 暂停！打开 report_batch{batch_str}.md，填写评分、缺陷标签。填写完毕按回车继续分析+更新Seed...")

    run_script(ANALYZE_SCRIPT, "报告分析 & 缺陷统计", batch_id)
    run_script(UPDATE_SEED_SCRIPT, "自动更新主脚本seed_list", batch_id)

    print(f"\n🎉 Batch{batch_str}流水线执行完毕！")
    print(f"📋 本次分析结果：analysis_result_batch{batch_str}.md")

if __name__ == "__main__":
    main()
```

## ② batch_ref2va_nf4.py（主生成脚本，增加--batch参数）

只贴新增/修改部分，其余原有代码不动

```python
import argparse
# 放在脚本顶部import区

# ========= 新增参数解析 =========
parser = argparse.ArgumentParser()
parser.add_argument("--batch", type=str, default="01")
args = parser.parse_args()
batch = args.batch
md_report_path = Path(f"report_batch{batch}.md")

# 下面原来这一行删掉：
# md_report_path = os.path.join(output_root_dir, "report.md")
# 替换为上面 md_report_path

# 写入md文件判断改为：
if not md_report_path.exists():
    with open(md_report_path, "w", encoding="utf-8") as f:
        f.write(f"# NF4 Ref2VA 批量生成结果报告【Batch{batch}】\n\n")
        f.write(f"任务启动：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"参考图目录：`{ref_images_dir}`\n")
        f.write(f"Seed列表：{seed_list}\n\n")
        f.write("| 参考图 | Seed | 状态 | 文件路径 | 时间 | 评分(1~10) | 缺陷标签 |\n")
        f.write("|--------|------|------|----------|------|------------|----------|\n")

# 后续追加行不变，仍然是f.write表格行
```

## ③ analyze_report.py（分析脚本，增加--batch参数）

```python
import argparse
# 在import区增加

# 原有配置区删除 REPORT_MD，改成由参数传入
parser = argparse.ArgumentParser()
parser.add_argument("--batch", type=str, default="01")
args = parser.parse_args()
batch = args.batch
REPORT_MD_PATH = Path(f"report_batch{batch}.md")
OUTPUT_MD = Path(f"analysis_result_batch{batch}.md")

# 其余原有逻辑不变，读取 REPORT_MD_PATH，写入 OUTPUT_MD
```

## ④ update_seed_list.py（seed更新脚本，增加--batch参数）

```python
import argparse
# import区增加

parser = argparse.ArgumentParser()
parser.add_argument("--batch", type=str, default="01")
args = parser.parse_args()
batch = args.batch
ANALYSIS_MD = Path(f"analysis_result_batch{batch}.md")

# MAIN_SCRIPT保持不变，其余提取seed逻辑不变
```

# 目录效果示例

```
├─ pipeline_auto.py
├─ batch_ref2va_nf4.py
├─ analyze_report.py
├─ update_seed_list.py
├─ report_batch01.md
├─ analysis_result_batch01.md
├─ report_batch02.md
├─ analysis_result_batch02.md
├─ report_batch03.md
├─ analysis_result_batch03.md
```

# 运行方式

```bash
python pipeline_auto.py
```

程序自动检测已有批次，自动使用下一个批次号，无需手动改文件名。

# 完整迭代流程

1. `pipeline_auto.py` 检测最大批次，生成batch01
2. 调用`batch_ref2va_nf4.py --batch 01`，生成视频 + `report_batch01.md`
3. 脚本暂停，人工打开`report_batch01.md`填写评分、缺陷标签
4. 回车，执行`analyze_report.py --batch 01`，输出`analysis_result_batch01.md`
5. 执行`update_seed_list.py --batch 01`读取该批次分析结果，更新主脚本seed_list
6. 再次运行`pipeline_auto.py`自动切换batch02，旧批次文件保留不覆盖

## **每批次独立视频输出目录**

# 新增特性说明

1. 自动创建批次独立输出文件夹 `output_batch01/`、`output_batch02/`，视频全部放在对应批次目录，不同迭代视频隔离，不会混在一起
2. `batch_ref2va_nf4.py` 接收 `--batch` 参数，自动设置输出根目录，同时report里写入视频相对路径，方便溯源
3. 其余脚本（pipeline_auto / analyze_report / update_seed_list）只需要传递batch参数，不用改动原有逻辑
4. 目录结构统一管理：报告md放在根目录，视频文件在批次output子文件夹

## ① pipeline_auto.py（无需改动，直接沿用）
>
> 这个脚本不需要修改，已经会自动传递`--batch`参数给子脚本

## ② batch_ref2va_nf4.py 【重点修改】

只贴新增/替换代码，原有推理逻辑不动

```python
import argparse
from pathlib import Path
from datetime import datetime

# ========= 参数解析 =========
parser = argparse.ArgumentParser()
parser.add_argument("--batch", type=str, default="01")
args = parser.parse_args()
batch = args.batch

# ✅ 批次独立输出目录
output_root_dir = Path(f"output_batch{batch}")
output_root_dir.mkdir(exist_ok=True, parents=True)

# 报告文件（放在项目根目录）
md_report_path = Path(f"report_batch{batch}.md")

# ====== MD报告写入逻辑（更新，写入相对视频路径）======
if not md_report_path.exists():
    with open(md_report_path, "w", encoding="utf-8") as f:
        f.write(f"# NF4 Ref2VA 批量生成结果报告【Batch{batch}】\n\n")
        f.write(f"任务启动：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"视频输出目录：`{output_root_dir}`\n")
        f.write(f"Seed列表：{seed_list}\n\n")
        f.write("| 参考图 | Seed | 状态 | 视频相对路径 | 时间 | 评分(1~10) | 缺陷标签 |\n")
        f.write("|--------|------|------|--------------|------|------------|----------|\n")

# ========= 生成视频时保存路径示例（你原有保存代码修改）=========
# 示例：视频文件名可以带上seed，例如 seed_42.mp4
video_save_path = output_root_dir / f"seed_{seed}.mp4"

# write_video_audio(..., output_path=str(video_save_path))

# 写入报告表格行，填入相对路径
rel_path = str(video_save_path)
f.write(f"| {ref_img_name} | {seed} | 成功 | {rel_path} | {datetime.now().strftime('%H:%M:%S')} |  |  |\n")
```

## ③ analyze_report.py 【无需改动】

只读取根目录下的 `report_batchXX.md`，视频路径是相对路径，读取md文本即可，不用操作output文件夹

## ④ update_seed_list.py 【无需改动】

读取根目录下 `analysis_result_batchXX.md`，逻辑不变

# 完整目录结构示例

```
├─ pipeline_auto.py
├─ batch_ref2va_nf4.py
├─ analyze_report.py
├─ update_seed_list.py
│
├─ report_batch01.md
├─ analysis_result_batch01.md
├─ output_batch01/          # batch01全部视频
│  ├─ seed_42.mp4
│  ├─ seed_24.mp4
│
├─ report_batch02.md
├─ analysis_result_batch02.md
├─ output_batch02/          # batch02全部视频
│  ├─ seed_10.mp4
│  ├─ seed_66.mp4
```

# 工作流程更新

1. `python pipeline_auto.py` → 自动识别下一个批次号
2. 调用 `batch_ref2va_nf4.py --batch 01`
   - 自动创建 `output_batch01/`
   - 视频保存到此文件夹
   - 生成 `report_batch01.md`，表格里自带视频相对路径
3. 暂停，人工打开`report_batch01.md`打分
4. 回车执行 `analyze_report.py --batch 01`，生成`analysis_result_batch01.md`
5. 执行 `update_seed_list.py --batch 01` 更新seed_list
6. 下一轮运行 pipeline_auto.py，自动进入 batch02，新建 output_batch02

## 增强方向

- 在报告里增加视频缩略图链接（markdown图片嵌入，在md里预览视频封面）
- 增加清理脚本，一键删除指定批次output文件夹（保留报告md，防止误删打分记录）

# 新增两大功能

1. **报告嵌入视频封面缩略图**：生成视频时自动提取首帧保存为jpg封面，report_batchXX.md 插入markdown图片链接，直接在Markdown编辑器预览视频封面，方便快速打分
2. **clean_batch.py 批次清理脚本**：只删除`output_batchXX`视频文件夹，**保留所有md报告**，防止打分记录丢失，支持清理单个批次 / 清理全部output目录

## 一、修改 batch_ref2va_nf4.py（增加提取视频首帧封面）
>
> 需要安装依赖：`pip install opencv-python`
仅新增/替换代码，原有推理逻辑不变

```python
import argparse
from pathlib import Path
from datetime import datetime
import cv2

# ========= 参数解析 =========
parser = argparse.ArgumentParser()
parser.add_argument("--batch", type=str, default="01")
args = parser.parse_args()
batch = args.batch

# ✅ 批次独立输出目录
output_root_dir = Path(f"output_batch{batch}")
output_root_dir.mkdir(exist_ok=True, parents=True)

# 封面子文件夹
cover_dir = output_root_dir / "covers"
cover_dir.mkdir(exist_ok=True, parents=True)

# 报告文件（放在项目根目录）
md_report_path = Path(f"report_batch{batch}.md")

def extract_first_frame(video_path: Path, cover_path: Path):
    """提取视频首帧保存为jpg封面"""
    cap = cv2.VideoCapture(str(video_path))
    ret, frame = cap.read()
    if ret:
        cv2.imwrite(str(cover_path), frame)
    cap.release()
    return ret

# ====== MD报告写入逻辑（更新，增加图片预览列）======
if not md_report_path.exists():
    with open(md_report_path, "w", encoding="utf-8") as f:
        f.write(f"# NF4 Ref2VA 批量生成结果报告【Batch{batch}】\n\n")
        f.write(f"任务启动：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"视频输出目录：`{output_root_dir}`\n")
        f.write(f"Seed列表：{seed_list}\n\n")
        # 新增【预览封面】列
        f.write("| 预览封面 | 参考图 | Seed | 状态 | 视频相对路径 | 时间 | 评分(1~10) | 缺陷标签 |\n")
        f.write("|----------|--------|------|------|--------------|------|------------|----------|\n")

# ========= 生成视频保存逻辑修改 =========
video_save_path = output_root_dir / f"seed_{seed}.mp4"
cover_save_path = cover_dir / f"seed_{seed}_cover.jpg"

# 原有视频写入：write_video_audio(..., output_path=str(video_save_path))

# 提取首帧封面
extract_first_frame(video_save_path, cover_save_path)

# 写入表格行，嵌入markdown图片
rel_cover = str(cover_save_path)
rel_video = str(video_save_path)
f.write(f"| ![封面]({rel_cover}) | {ref_img_name} | {seed} | 成功 | {rel_video} | {datetime.now().strftime('%H:%M:%S')} |  |  |\n")
```

> 表格效果预览：
>
> | 预览封面 | 参考图 | Seed | 状态 | 视频相对路径 | 时间 | 评分(1~10) | 缺陷标签 |
> |----------|--------|------|------|--------------|------|------------|----------|
> | ![封面](output_batch01/covers/seed_42_cover.jpg) | ref01.png | 42 | 成功 | output_batch01/seed_42.mp4 | 14:30:21 |  |  |

## 二、新增脚本 clean_batch.py 【清理批次脚本】

功能：只删除批次output视频文件夹，**不删除report和analysis_result的md打分文件**

```python
import argparse
from pathlib import Path
import shutil

def clean_batch(batch_id: str):
    folder = Path(f"output_batch{batch_id}")
    if not folder.exists():
        print(f"⚠️ 批次 {batch_id} 的output目录不存在：{folder}")
        return
    confirm = input(f"⚠️ 确认删除 {folder} 内所有视频与封面？md报告将保留！输入y确认：")
    if confirm.lower() == "y":
        shutil.rmtree(folder)
        print(f"✅ 已删除 {folder}，报告md文件保留")
    else:
        print("❌ 取消删除")

def clean_all():
    """一键清理全部output_batch文件夹，保留所有md"""
    confirm = input("⚠️ 确认删除所有 output_batchXX 文件夹？所有report/analysis md保留！输入y确认：")
    if confirm.lower() != "y":
        print("❌ 取消批量清理")
        return
    for folder in Path(".").glob("output_batch*"):
        if folder.is_dir():
            shutil.rmtree(folder)
            print(f"✅ 删除：{folder.name}")
    print("🎉 全部output目录清理完成，md报告保留")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="清理批次output视频文件夹，保留md打分报告")
    parser.add_argument("--batch", type=str, default=None, help="指定批次，例如 01；不填则触发清理全部output")
    args = parser.parse_args()
    if args.batch:
        clean_batch(args.batch)
    else:
        clean_all()
```

### clean_batch.py 使用示例

```bash
# 删除batch01视频（保留report_batch01.md）
python clean_batch.py --batch 01

# 删除所有批次output视频文件夹（全部md保留）
python clean_batch.py
```

# 更新后的完整目录

```
├─ pipeline_auto.py
├─ batch_ref2va_nf4.py
├─ analyze_report.py
├─ update_seed_list.py
├─ clean_batch.py          # 新增清理脚本
│
├─ report_batch01.md
├─ analysis_result_batch01.md
├─ output_batch01/
│  ├─ seed_42.mp4
│  ├─ seed_24.mp4
│  └─ covers/
│     ├─ seed_42_cover.jpg
│     └─ seed_24_cover.jpg
│
├─ report_batch02.md
├─ analysis_result_batch02.md
├─ output_batch02/
│  ├─ seed_10.mp4
│  ├─ seed_66.mp4
│  └─ covers/
```

# 依赖补充

```bash
pip install opencv-python
```

## 流水线整体新增效果

1. 每轮生成自动提取视频首帧作为封面
2. report里直接显示图片预览，打分不用打开视频
3. 清理脚本只删视频、不动打分记录，迭代测试硬盘空间可控

---

## 批量导出多批次打分汇总表，一次性对比batch01/batch02所有seed评分

# 新增脚本 `export_multi_batch_summary.py`

功能：扫描目录下所有 `report_batch*.md`，自动解析各批次评分，生成跨批次横向对比汇总表，一次性对比 batch01/batch02/... 所有 seed 的评分变化。

> 兼容设计：自动识别表头列位置，无论报告是否带「预览封面」列都能正确解析；只读取md，不修改任何已有脚本和报告。

```python
import re
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Optional

# ===================== 配置区 =====================
OUTPUT_SUMMARY_MD = Path("multi_batch_summary.md")
# ==================================================

@dataclass
class Record:
    batch: str
    ref_img: str
    seed: str
    status: str
    score: Optional[float]
    tags: List[str] = field(default_factory=list)

def parse_batch_report(md_path: Path) -> List[Record]:
    """解析单个 report_batchXX.md，自动定位列索引"""
    content = md_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    # 找表头行
    header_idx = None
    col_map = {}
    for i, line in enumerate(lines):
        if line.strip().startswith("|") and ("参考图" in line) and ("Seed" in line):
            header_idx = i
            headers = [h.strip() for h in line.strip().strip("|").split("|")]
            for idx, h in enumerate(headers):
                if "参考图" in h:
                    col_map["ref_img"] = idx
                elif h == "Seed":
                    col_map["seed"] = idx
                elif "状态" in h:
                    col_map["status"] = idx
                elif "评分" in h:
                    col_map["score"] = idx
                elif "缺陷" in h or "标签" in h:
                    col_map["tags"] = idx
            break

    if header_idx is None or "ref_img" not in col_map:
        print(f"⚠️ {md_path.name} 未找到有效表头，跳过")
        return []

    # 从批次文件名提取批次号
    batch_match = re.search(r"report_batch(\d+)\.md", md_path.name)
    batch = batch_match.group(1) if batch_match else "??"

    records: List[Record] = []
    for line in lines[header_idx + 1:]:
        line = line.strip()
        if not line.startswith("|"):
            continue
        if "----" in line:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) <= max(col_map.values()):
            continue

        ref_img = cells[col_map["ref_img"]]
        seed = cells[col_map["seed"]]
        status = cells[col_map["status"]]

        score_str = cells[col_map["score"]] if "score" in col_map else ""
        score = None
        if score_str and score_str.replace(".", "").isdigit():
            score = float(score_str)

        tags_str = cells[col_map["tags"]] if "tags" in col_map else ""
        tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []

        records.append(Record(
            batch=batch,
            ref_img=ref_img,
            seed=seed,
            status=status,
            score=score,
            tags=tags
        ))
    return records


def main():
    # 扫描所有批次报告
    batch_files = sorted(Path(".").glob("report_batch*.md"))
    if not batch_files:
        print("❌ 未找到任何 report_batch*.md 文件")
        return

    print(f"📂 发现 {len(batch_files)} 个批次报告：")
    for f in batch_files:
        print(f"  - {f.name}")

    all_records: List[Record] = []
    for f in batch_files:
        recs = parse_batch_report(f)
        all_records.extend(recs)
        print(f"  ✅ {f.name}: 解析到 {len(recs)} 条记录")

    if not all_records:
        print("⚠️ 没有解析到任何有效记录")
        return

    # 批次列表（排序）
    batches = sorted({r.batch for r in all_records})

    # ========== 统计1：各批次总览 ==========
    batch_stats = {}
    for b in batches:
        b_recs = [r for r in all_records if r.batch == b]
        success = [r for r in b_recs if r.status == "SUCCESS"]
        failed = [r for r in b_recs if r.status == "FAILED"]
        skipped = [r for r in b_recs if r.status == "SKIPPED"]
        scored = [r for r in success if r.score is not None]
        avg = sum(r.score for r in scored) / len(scored) if scored else 0
        max_score = max((r.score for r in scored), default=0)
        batch_stats[b] = {
            "total": len(b_recs),
            "success": len(success),
            "failed": len(failed),
            "skipped": len(skipped),
            "scored": len(scored),
            "avg": avg,
            "max": max_score,
        }

    # ========== 统计2：按 (参考图, Seed) 横向对比各批次评分 ==========
    # key: (ref_img, seed), value: {batch: score}
    cross_map: Dict[tuple, Dict[str, Optional[float]]] = defaultdict(dict)
    cross_status: Dict[tuple, Dict[str, str]] = defaultdict(dict)
    cross_tags: Dict[tuple, Dict[str, List[str]]] = defaultdict(dict)

    for r in all_records:
        key = (r.ref_img, r.seed)
        cross_map[key][r.batch] = r.score
        cross_status[key][r.batch] = r.status
        cross_tags[key][r.batch] = r.tags

    # 按参考图分组排序
    ref_imgs = sorted({r.ref_img for r in all_records})

    # ========== 统计3：每个参考图在各批次的最优Seed ==========
    best_per_batch: Dict[str, Dict[str, Record]] = defaultdict(dict)
    for b in batches:
        for img in ref_imgs:
            candidates = [r for r in all_records
                          if r.batch == b and r.ref_img == img
                          and r.status == "SUCCESS" and r.score is not None]
            if candidates:
                best = max(candidates, key=lambda x: x.score)
                best_per_batch[img][b] = best

    # ========== 生成汇总 Markdown ==========
    md = []
    md.append("# 多批次打分汇总对比表")
    md.append("")
    md.append(f"> 自动生成，覆盖批次：{', '.join(batches)}")
    md.append("")

    # 表1：各批次总览
    md.append("## 1. 各批次总览")
    md.append("")
    md.append("| 批次 | 总记录 | 成功 | 失败 | 跳过 | 有效打分 | 平均分 | 最高分 |")
    md.append("|------|--------|------|------|------|----------|--------|--------|")
    for b in batches:
        s = batch_stats[b]
        md.append(f"| batch{b} | {s['total']} | {s['success']} | {s['failed']} | {s['skipped']} | {s['scored']} | {s['avg']:.2f} | {s['max']:.1f} |")
    md.append("")

    # 表2：跨批次评分横向对比（按参考图分组）
    md.append("## 2. 跨批次 Seed 评分横向对比")
    md.append("")
    md.append("> 同一参考图 + 同一 Seed 在不同批次的评分变化，空值表示该批次无此样本")
    md.append("")

    for img in ref_imgs:
        md.append(f"### 参考图：{img}")
        md.append("")
        header = "| Seed |" + "|".join(f" batch{b} 评分 | batch{b} 状态 | batch{b} 缺陷" for b in batches) + "|"
        sep = "|------|" + "|".join("------|------|------" for _ in batches) + "|"
        md.append(header)
        md.append(sep)

        # 该参考图下所有seed
        seeds_for_img = sorted({r.seed for r in all_records if r.ref_img == img},
                               key=lambda x: int(x) if x.isdigit() else 9999)
        for seed in seeds_for_img:
            key = (img, seed)
            row = f"| {seed} |"
            for b in batches:
                score = cross_map[key].get(b)
                status = cross_status[key].get(b, "-")
                tags = ",".join(cross_tags[key].get(b, [])) or "-"
                score_str = f"{score:.1f}" if score is not None else "-"
                row += f" {score_str} | {status} | {tags} |"
            md.append(row)
        md.append("")

    # 表3：各参考图每批次最优Seed
    md.append("## 3. 各参考图每批次最优 Seed")
    md.append("")
    header3 = "| 参考图 |" + "|".join(f" batch{b} 最优Seed | batch{b} 最高分" for b in batches) + "|"
    sep3 = "|--------|" + "|".join("------|------" for _ in batches) + "|"
    md.append(header3)
    md.append(sep3)
    for img in ref_imgs:
        row = f"| {img} |"
        for b in batches:
            best = best_per_batch[img].get(b)
            if best:
                row += f" {best.seed} | {best.score:.1f} |"
            else:
                row += " - | - |"
        md.append(row)
    md.append("")

    # 表4：全局Top10高分样本（跨所有批次）
    md.append("## 4. 全局 Top 10 高分样本")
    md.append("")
    all_scored = [r for r in all_records if r.score is not None and r.status == "SUCCESS"]
    all_scored.sort(key=lambda x: x.score, reverse=True)
    md.append("| 排名 | 批次 | 参考图 | Seed | 评分 | 缺陷标签 |")
    md.append("|------|------|--------|------|------|----------|")
    for i, r in enumerate(all_scored[:10], 1):
        tags = ",".join(r.tags) if r.tags else "无"
        md.append(f"| {i} | batch{r.batch} | {r.ref_img} | {r.seed} | {r.score:.1f} | {tags} |")
    md.append("")

    # 表5：缺陷标签跨批次统计
    md.append("## 5. 缺陷标签跨批次统计")
    md.append("")
    all_tags_set = set()
    for r in all_records:
        all_tags_set.update(r.tags)
    all_tags_sorted = sorted(all_tags_set)
    header5 = "| 缺陷类型 |" + "|".join(f" batch{b}" for b in batches) + "| 合计 |"
    sep5 = "|----------|" + "|".join("------" for _ in batches) + "|------|"
    md.append(header5)
    md.append(sep5)
    for tag in all_tags_sorted:
        row = f"| {tag} |"
        total = 0
        for b in batches:
            cnt = sum(1 for r in all_records if r.batch == b and tag in r.tags)
            total += cnt
            row += f" {cnt} |"
        row += f" {total} |"
        md.append(row)
    md.append("")

    # 结论与建议
    md.append("## 6. 迭代结论与建议")
    md.append("")
    # 平均分趋势
    if len(batches) >= 2:
        first_avg = batch_stats[batches[0]]["avg"]
        last_avg = batch_stats[batches[-1]]["avg"]
        diff = last_avg - first_avg
        trend = "上升" if diff > 0 else ("下降" if diff < 0 else "持平")
        md.append(f"- **平均分趋势**：batch{batches[0]} → batch{batches[-1]}，从 {first_avg:.2f} → {last_avg:.2f}，{trend} {abs(diff):.2f} 分")
    # 高频缺陷
    if all_tags_sorted:
        tag_total = {t: sum(1 for r in all_records if t in r.tags) for t in all_tags_sorted}
        top_tag = max(tag_total, key=tag_total.get)
        md.append(f"- **最高频缺陷**：{top_tag}（共 {tag_total[top_tag]} 次），下一轮应重点针对该缺陷优化 Prompt / 参考图")
    # 最优seed集合
    global_best_seeds = sorted({r.seed for r in all_scored[:5]}, key=lambda x: int(x) if x.isdigit() else 9999)
    md.append(f"- **推荐下一轮优先 Seed**：{global_best_seeds}")
    md.append("")

    OUTPUT_SUMMARY_MD.write_text("\n".join(md), encoding="utf-8")
    print(f"\n🎉 多批次汇总表已生成：{OUTPUT_SUMMARY_MD}")
    print(f"   覆盖批次：{', '.join(batches)}")
    print(f"   总记录数：{len(all_records)}")


if __name__ == "__main__":
    main()
```

## 使用方法

```bash
# 确保目录下有 report_batch01.md、report_batch02.md 等
python export_multi_batch_summary.py
```

## 生成的汇总表包含6张表

1. **各批次总览**：每批次成功/失败/跳过数、平均分、最高分
2. **跨批次 Seed 评分横向对比**：按参考图分组，同一 Seed 在不同批次的评分、状态、缺陷并排展示
3. **各参考图每批次最优 Seed**：快速定位每个人物在每轮的最佳参数
4. **全局 Top 10 高分样本**：跨所有批次排名
5. **缺陷标签跨批次统计**：变脸/手崩/抖动/口型错位在各批次的出现次数
6. **迭代结论与建议**：自动计算平均分趋势、最高频缺陷、推荐下一轮 Seed

## 示例输出片段

```markdown
## 1. 各批次总览
| 批次 | 总记录 | 成功 | 失败 | 跳过 | 有效打分 | 平均分 | 最高分 |
|------|--------|------|------|------|----------|--------|--------|
| batch01 | 12 | 8 | 2 | 2 | 8 | 6.75 | 9.0 |
| batch02 | 6 | 6 | 0 | 0 | 6 | 7.83 | 9.5 |

## 2. 跨批次 Seed 评分横向对比
### 参考图：person_a.jpg
| Seed | batch01 评分 | batch01 状态 | batch01 缺陷 | batch02 评分 | batch02 状态 | batch02 缺陷 |
|------|------|------|------|------|------|------|
| 42 | 9.0 | SUCCESS | 无 | 9.5 | SUCCESS | 无 |
| 24 | 6.0 | SUCCESS | 手崩 | 8.0 | SUCCESS | 无 |
```

## 与现有流水线的衔接

- 该脚本**独立运行**，不修改任何已有脚本
- 可在多轮迭代后随时执行，汇总所有历史批次
- 建议放在 `pipeline_auto.py` 之后作为可选步骤，或在需要复盘时手动运行

至此整套迭代流水线完整闭环：
`pipeline_auto.py` → 批次生成 → 人工打分 → 分析 → 更新Seed → 多轮迭代 → `export_multi_batch_summary.py` 跨批次复盘

---
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
