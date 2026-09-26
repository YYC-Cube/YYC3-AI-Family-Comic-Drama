/**
 * 项目相关 API
 */
import { request } from "@/api/client";
import type { CreateProjectInput, Project } from "@/types/project";

/** 项目列表 */
export function listProjects(): Promise<Project[]> {
  return request<Project[]>("/api/v1/projects");
}

/** 项目详情 */
export function getProject(projectId: string): Promise<Project> {
  return request<Project>(
    `/api/v1/projects/${encodeURIComponent(projectId)}`
  );
}

/** 创建项目 */
export function createProject(input: CreateProjectInput): Promise<Project> {
  return request<Project>("/api/v1/projects", {
    method: "POST",
    body: JSON.stringify(input),
  });
}
