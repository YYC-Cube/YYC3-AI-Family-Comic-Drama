/**
 * 项目类型定义
 */

/** 项目状态：草稿/生产中/已完结 */
export type ProjectStatus = "draft" | "producing" | "completed";

/** 项目 */
export interface Project {
  project_id: string;
  title: string;
  /** 小说原著来源（文件名或书名） */
  novice_source: string;
  /** 目标集数 */
  episode_target: number;
  status: ProjectStatus;
  /** 累计成本（元） */
  cost: number;
  created_at: string;
}

/** 创建项目入参 */
export interface CreateProjectInput {
  title: string;
  novice_source: string;
  episode_target: number;
}
