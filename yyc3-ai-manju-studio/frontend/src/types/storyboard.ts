/**
 * 分镜剧本（StoryboardV1）类型定义与校验
 * 对齐后端协议：单集 80-120 镜头，钩子镜头必填
 */

/** 景别枚举：远景/全景/中景/近景/特写 */
export const SHOT_TYPES = ["远", "全", "中", "近", "特"] as const;
export type ShotType = (typeof SHOT_TYPES)[number];

/** 运镜枚举：推/拉/摇/移/跟/固定 */
export const CAMERA_MOVES = ["推", "拉", "摇", "移", "跟", "固定"] as const;
export type CameraMove = (typeof CAMERA_MOVES)[number];

/** 单个镜头（Shot 子结构，12 字段） */
export interface Shot {
  /** 镜头 ID，如 shot-ep01-001 */
  shot_id: string;
  /** 所属场景 ID */
  scene_id: string;
  /** 画面描述 */
  description: string;
  /** 景别 */
  shot_type: ShotType;
  /** 运镜方式 */
  camera_move: CameraMove;
  /** 台词（可为空） */
  dialogue: string;
  /** 时长（秒） */
  duration_sec: number;
  /** 文生图提示词 */
  image_prompt: string;
  /** 音效描述（可为空） */
  sfx: string;
  /** 背景音乐描述（可为空） */
  bgm: string;
  /** 是否钩子镜头（前 3 秒留人点） */
  hook_flag: boolean;
  /** 角色一致性锚定 ID（关联角色资产库） */
  consistency_anchor: string;
}

/** 分镜剧本顶层结构（StoryboardV1，12 字段） */
export interface StoryboardV1 {
  /** 协议版本，当前为 1.0 */
  version: string;
  /** 项目 ID */
  project_id: string;
  /** 单集 ID */
  episode_id: string;
  /** 单集标题 */
  episode_title: string;
  /** 风格参考（提示词或参考图 ID） */
  style_ref: string;
  /** 出场角色锚定 ID 列表 */
  character_refs: string[];
  /** 镜头总数（必须与 shots.length 一致） */
  total_shots: number;
  /** 钩子镜头 ID 列表（必须指向 hook_flag=true 的镜头） */
  hook_shots: string[];
  /** 镜头列表 */
  shots: Shot[];
  created_at: string;
  updated_at: string;
  /** 链路追踪 ID */
  trace_id: string;
}

const REQUIRED_TOP_FIELDS: Array<[keyof StoryboardV1, string]> = [
  ["version", "版本号"],
  ["project_id", "项目 ID"],
  ["episode_id", "单集 ID"],
  ["episode_title", "单集标题"],
  ["style_ref", "风格参考"],
  ["trace_id", "追踪 ID"],
];

/**
 * 本地校验分镜剧本，返回错误/警告列表（空数组表示通过）
 * 校验规则：
 * 1. 顶层必填字段与 shots 非空
 * 2. total_shots 必须等于 shots.length
 * 3. hook_shots 非空，且每一项必须对应 hook_flag=true 的 shot_id
 * 4. 单集镜头数应在 80-120 范围内（超范围输出警告）
 */
export function validateStoryboard(sb: StoryboardV1): string[] {
  const errors: string[] = [];

  // 1. 顶层必填字段
  for (const [key, label] of REQUIRED_TOP_FIELDS) {
    const value = sb[key];
    if (typeof value !== "string" || value.trim() === "") {
      errors.push(`缺少必填字段：${label}（${key}）`);
    }
  }

  // 2. 镜头列表非空且 total_shots 一致
  if (!Array.isArray(sb.shots) || sb.shots.length === 0) {
    errors.push("镜头列表（shots）不能为空");
  } else {
    if (typeof sb.total_shots !== "number" || Number.isNaN(sb.total_shots)) {
      errors.push("total_shots 必须为数字");
    } else if (sb.total_shots !== sb.shots.length) {
      errors.push(
        `total_shots（${sb.total_shots}）与 shots.length（${sb.shots.length}）不一致`
      );
    }
  }

  // 3. 钩子镜头校验
  if (!Array.isArray(sb.hook_shots) || sb.hook_shots.length === 0) {
    errors.push("hook_shots 不能为空：每集至少需要 1 个钩子镜头");
  } else {
    const shotMap = new Map<string, Shot>(
      (sb.shots ?? []).map((s) => [s.shot_id, s])
    );
    for (const hookId of sb.hook_shots) {
      const target = shotMap.get(hookId);
      if (!target) {
        errors.push(`hook_shots 中的 ${hookId} 不存在于 shots 列表`);
      } else if (!target.hook_flag) {
        errors.push(`镜头 ${hookId} 的 hook_flag 为 false，与 hook_shots 声明矛盾`);
      }
    }
  }

  // 4. 单集镜头数范围警告
  if (Array.isArray(sb.shots) && sb.shots.length > 0) {
    if (sb.shots.length < 80) {
      errors.push(`[警告] 单集镜头数 ${sb.shots.length} 低于下限 80，节奏可能偏慢`);
    } else if (sb.shots.length > 120) {
      errors.push(`[警告] 单集镜头数 ${sb.shots.length} 超过上限 120，注意成本红线`);
    }
  }

  return errors;
}
