/**
 * 剧本生成与分镜提取 API
 */
import { request } from "@/api/client";
import type { StoryboardV1 } from "@/types/storyboard";

/** 剧本结构化结果：角色 / 场景 / 钩子点 / 分集建议 */
export interface ScriptResult {
  characters: string[];
  scenes: string[];
  hooks: string[];
  /** 分集建议（每集标题与梗概） */
  episode_suggestions: Array<{ title: string; synopsis: string }>;
}

export interface GenerateScriptInput {
  /** 小说原文 */
  novel_text: string;
  project_id: string;
}

/** 生成剧本（结构化解析） */
export function generateScript(input: GenerateScriptInput): Promise<ScriptResult> {
  return request<ScriptResult>("/api/v1/script/generate", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

/** 剧本优化（润色与节奏调整） */
export function optimizeScript(input: GenerateScriptInput): Promise<ScriptResult> {
  return request<ScriptResult>("/api/v1/script/optimize", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

/** 从剧本提取分镜 */
export function extractStoryboard(input: {
  project_id: string;
  episode_id: string;
  script_text: string;
}): Promise<StoryboardV1> {
  return request<StoryboardV1>("/api/v1/storyboard/extract", {
    method: "POST",
    body: JSON.stringify(input),
  });
}
