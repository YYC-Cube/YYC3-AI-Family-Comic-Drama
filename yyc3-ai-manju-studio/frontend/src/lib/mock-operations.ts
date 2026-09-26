/**
 * 运营与资产类演示数据：成本报表、日播放量、角色资产库
 * 与 mock-data.ts（项目/分镜/任务）配合，共同支撑页面 mock 降级
 */

/* ------------------------------ 成本 ------------------------------ */

export interface CostItem {
  key: string;
  name: string;
  /** 目标成本（元/集） */
  target: number;
  /** 实际累计成本（元/集） */
  actual: number;
}

export interface CostReport {
  items: CostItem[];
}

export const mockCostReport: CostReport = {
  items: [
    { key: "t2i", name: "文生图", target: 0.5, actual: 0.42 },
    { key: "i2v", name: "图生视频", target: 0.8, actual: 0.86 },
    { key: "tts", name: "TTS 配音", target: 0.3, actual: 0.24 },
    { key: "compose", name: "合成渲染", target: 0.4, actual: 0.28 },
  ],
};

/* ------------------------------ 运营 ------------------------------ */

export interface DailyPlayItem {
  date: string;
  plays: number;
}

export const mockDailyPlays: DailyPlayItem[] = [
  { date: "09-20", plays: 128400 },
  { date: "09-21", plays: 152300 },
  { date: "09-22", plays: 141900 },
  { date: "09-23", plays: 187500 },
  { date: "09-24", plays: 226800 },
  { date: "09-25", plays: 312400 },
  { date: "09-26", plays: 289700 },
];

/* ------------------------------ 角色资产 ------------------------------ */

export interface CharacterAsset {
  anchor_id: string;
  name: string;
  source: string;
  /** 特征向量维度 */
  vector_dim: number;
  /** 是否已建库 */
  indexed: boolean;
  usage_count: number;
  /** 渐变背景色（头像用） */
  gradient: string;
}

export const mockCharacters: CharacterAsset[] = [
  {
    anchor_id: "char-hero",
    name: "林彻（主角）",
    source: "第 1 集 · 天台定妆",
    vector_dim: 512,
    indexed: true,
    usage_count: 326,
    gradient: "from-violet-500 to-indigo-600",
  },
  {
    anchor_id: "char-villain",
    name: "沈万川（反派）",
    source: "第 1 集 · 天台定妆",
    vector_dim: 512,
    indexed: true,
    usage_count: 184,
    gradient: "from-rose-500 to-red-700",
  },
  {
    anchor_id: "char-heroine-young",
    name: "苏念（少年期）",
    source: "第 2 集 · 火场回忆",
    vector_dim: 512,
    indexed: true,
    usage_count: 97,
    gradient: "from-cyan-500 to-sky-600",
  },
  {
    anchor_id: "char-hero-young",
    name: "林彻（少年期）",
    source: "第 2 集 · 火场回忆",
    vector_dim: 512,
    indexed: true,
    usage_count: 88,
    gradient: "from-emerald-500 to-teal-600",
  },
  {
    anchor_id: "char-elder",
    name: "老管家",
    source: "第 3 集 · 宅门初现",
    vector_dim: 512,
    indexed: false,
    usage_count: 12,
    gradient: "from-amber-500 to-orange-600",
  },
  {
    anchor_id: "char-bodyguard",
    name: "黑衣跟班 A",
    source: "第 1 集 · 群演复用",
    vector_dim: 512,
    indexed: false,
    usage_count: 6,
    gradient: "from-slate-500 to-zinc-700",
  },
];
