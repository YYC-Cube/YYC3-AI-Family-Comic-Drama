/**
 * 演示数据（mock）：后端 API 不可达时的降级数据源
 * 数据形状与后端协议保持一致，保证前端可独立开发与演示
 * 运营 / 成本 / 角色资产类数据见 mock-operations.ts
 */
import type { Project } from "@/types/project";
import type { Shot, StoryboardV1 } from "@/types/storyboard";
import type { ProductionTask, TaskStatus } from "@/types/task";

/* ------------------------------ 项目 ------------------------------ */

export const mockProjects: Project[] = [
  {
    project_id: "proj-001",
    title: "万古神帝",
    novice_source: "万古神帝_原著精编.txt",
    episode_target: 100,
    status: "producing",
    cost: 128.4,
    created_at: "2026-08-12T09:00:00+08:00",
  },
  {
    project_id: "proj-002",
    title: "凡人修仙传·外传",
    novice_source: "凡人外传_小说.json",
    episode_target: 60,
    status: "producing",
    cost: 86.2,
    created_at: "2026-09-01T14:30:00+08:00",
  },
  {
    project_id: "proj-003",
    title: "都市赘婿逆袭",
    novice_source: "都市赘婿_精校版.txt",
    episode_target: 80,
    status: "draft",
    cost: 0,
    created_at: "2026-09-20T11:00:00+08:00",
  },
];

/* ------------------------------ 分镜 ------------------------------ */

function buildMockShots(): Shot[] {
  const base: Omit<Shot, "shot_id">[] = [
    {
      scene_id: "scene-01",
      description: "雨夜天台，主角背对城市霓虹独立，风衣猎猎",
      shot_type: "远",
      camera_move: "推",
      dialogue: "",
      duration_sec: 3,
      image_prompt:
        "cinematic wide shot, rainy rooftop at night, neon city bokeh, lone hero in trench coat, back view",
      sfx: "雨声、远处雷鸣",
      bgm: "低沉弦乐渐入",
      hook_flag: true,
      consistency_anchor: "char-hero",
    },
    {
      scene_id: "scene-01",
      description: "特写主角侧脸，雨水顺着下颌滑落，眼神冷峻",
      shot_type: "特",
      camera_move: "固定",
      dialogue: "十年了，这笔账该算了。",
      duration_sec: 2.5,
      image_prompt:
        "extreme close-up, male face profile, rain dripping, cold determined eyes, cinematic lighting",
      sfx: "雨滴近景",
      bgm: "弦乐持续",
      hook_flag: true,
      consistency_anchor: "char-hero",
    },
    {
      scene_id: "scene-01",
      description: "反派从天台门口走出，西装革履，身后跟班持伞",
      shot_type: "中",
      camera_move: "摇",
      dialogue: "",
      duration_sec: 3,
      image_prompt:
        "medium shot, villain in black suit walking out, bodyguards with umbrellas, night rooftop",
      sfx: "皮鞋踩水",
      bgm: "弦乐转急",
      hook_flag: false,
      consistency_anchor: "char-villain",
    },
    {
      scene_id: "scene-01",
      description: "两人对峙，闪电照亮天台，雨幕中剑拔弩张",
      shot_type: "全",
      camera_move: "移",
      dialogue: "你以为躲了十年，就能一笔勾销？",
      duration_sec: 3.5,
      image_prompt:
        "full shot, two men confronting, lightning flash, heavy rain, rooftop edge, dramatic",
      sfx: "惊雷",
      bgm: "鼓点切入",
      hook_flag: false,
      consistency_anchor: "char-hero",
    },
    {
      scene_id: "scene-02",
      description: "回忆闪回：十年前工厂大火，少年拼命冲进火场",
      shot_type: "中",
      camera_move: "跟",
      dialogue: "",
      duration_sec: 4,
      image_prompt:
        "flashback scene, factory on fire, young man rushing into flames, orange glow, smoke",
      sfx: "火焰轰鸣",
      bgm: "悲怆钢琴",
      hook_flag: false,
      consistency_anchor: "char-hero-young",
    },
    {
      scene_id: "scene-02",
      description: "回忆闪回：少女被困火场伸出手，泪眼朦胧",
      shot_type: "近",
      camera_move: "推",
      dialogue: "救救我……",
      duration_sec: 2,
      image_prompt:
        "close-up, young girl trapped in fire, reaching out hand, teary eyes, warm fire light",
      sfx: "木梁断裂",
      bgm: "悲怆钢琴",
      hook_flag: false,
      consistency_anchor: "char-heroine-young",
    },
    {
      scene_id: "scene-03",
      description: "回到现实，主角缓缓握紧拳，指节发白",
      shot_type: "特",
      camera_move: "固定",
      dialogue: "",
      duration_sec: 1.5,
      image_prompt:
        "extreme close-up, clenched fist, white knuckles, rain, dramatic tension",
      sfx: "骨骼轻响",
      bgm: "静默",
      hook_flag: false,
      consistency_anchor: "char-hero",
    },
    {
      scene_id: "scene-03",
      description: "反派狞笑抬手，跟班将一份文件丢在积水里",
      shot_type: "近",
      camera_move: "拉",
      dialogue: "签字吧，废物的最后一点用处。",
      duration_sec: 3,
      image_prompt:
        "close shot, villain smirking, henchman dropping document into puddle, night",
      sfx: "纸张落水",
      bgm: "低音铺底",
      hook_flag: true,
      consistency_anchor: "char-villain",
    },
    {
      scene_id: "scene-03",
      description: "主角抬眸，眸中寒光一闪，雨幕骤然定格",
      shot_type: "特",
      camera_move: "推",
      dialogue: "那就……一起下地狱吧。",
      duration_sec: 2.5,
      image_prompt:
        "extreme close-up, hero raising eyes, cold glint in eyes, frozen rain drops, epic moment",
      sfx: "音爆瞬寂",
      bgm: "全曲高潮前静默",
      hook_flag: true,
      consistency_anchor: "char-hero",
    },
  ];

  return base.map((s, i) => ({
    ...s,
    shot_id: `shot-ep01-${String(i + 1).padStart(3, "0")}`,
  }));
}

export const mockStoryboard: StoryboardV1 = {
  version: "1.0",
  project_id: "proj-001",
  episode_id: "ep01",
  episode_title: "第 1 集：雨夜归人",
  style_ref: "style/guoman-cinematic-v3",
  character_refs: ["char-hero", "char-villain", "char-heroine-young"],
  total_shots: 9,
  hook_shots: ["shot-ep01-001", "shot-ep01-002", "shot-ep01-008", "shot-ep01-009"],
  shots: buildMockShots(),
  created_at: "2026-09-25T10:00:00+08:00",
  updated_at: "2026-09-26T08:30:00+08:00",
  trace_id: "trace-sb-9f31c2",
};

/* ------------------------------ 任务 ------------------------------ */

const TASK_SEEDS: Array<[string, ProductionTask["stage"], TaskStatus, number, string]> = [
  ["task-101", "creative", "success", 100, "agent-idea-miner"],
  ["task-102", "script", "success", 100, "agent-script-writer"],
  ["task-103", "script", "running", 62, "agent-storyboard-splitter"],
  ["task-104", "visual", "running", 45, "agent-t2i-worker"],
  ["task-105", "visual", "running", 78, "agent-i2v-worker"],
  ["task-106", "visual", "pending", 0, "agent-i2v-worker"],
  ["task-107", "audio", "running", 30, "agent-tts-voice"],
  ["task-108", "audio", "failed", 55, "agent-sync-checker"],
  ["task-109", "compose", "pending", 0, "agent-compositor"],
  ["task-110", "compose", "success", 100, "agent-compositor"],
  ["task-111", "ops", "success", 100, "agent-ops-feedback"],
  ["task-112", "visual", "rework", 40, "agent-consistency-guard"],
];

export const mockTasks: ProductionTask[] = TASK_SEEDS.map(
  ([task_id, stage, status, progress, agent], i) => ({
    task_id,
    project_id: i % 3 === 2 ? "proj-002" : "proj-001",
    stage,
    status,
    progress,
    agent,
    trace_id: `trace-${task_id}-${(i + 17).toString(16)}a4`,
    created_at: "2026-09-26T07:00:00+08:00",
    updated_at: "2026-09-26T09:20:00+08:00",
    error:
      status === "failed"
        ? "音画同步校验未达标：sync_score=0.61 < 0.75"
        : status === "rework"
          ? "角色一致性漂移：face_sim=0.72 < 0.80，触发自动返工"
          : null,
  })
);
