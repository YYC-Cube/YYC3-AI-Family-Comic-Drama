/**
 * 全局常量：六阶段流水线、NAS 路径、成本与质量红线
 */

/** 流水线阶段定义 */
export interface StageDef {
  id: number;
  key: string;
  name: string;
}

/** 生产六阶段（创意立项 → 剧本分镜 → 视听生成 → 音画同步 → 合成交付 → 运营反哺） */
export const STAGES: StageDef[] = [
  { id: 1, key: "creative", name: "创意立项" },
  { id: 2, key: "script", name: "剧本分镜" },
  { id: 3, key: "visual", name: "视听生成" },
  { id: 4, key: "audio", name: "音画同步" },
  { id: 5, key: "compose", name: "合成交付" },
  { id: 6, key: "ops", name: "运营反哺" },
];

/** 阶段主题色（hex，用于 SVG 流水线画布） */
export const STAGE_COLORS: Record<string, string> = {
  creative: "#8b5cf6",
  script: "#3b82f6",
  visual: "#06b6d4",
  audio: "#10b981",
  compose: "#f59e0b",
  ops: "#ec4899",
};

/** NAS 挂载根路径 */
export const NAS_BASE = "/mnt/nas/";

/** 成本红线：单集目标成本（元/集） */
export const COST_TARGET = 2;

/** 质量红线：角色一致性均分达标线 */
export const CONSISTENCY_TARGET = 0.8;

/** 质量红线：音画同步达标线 */
export const SYNC_TARGET = 0.75;
