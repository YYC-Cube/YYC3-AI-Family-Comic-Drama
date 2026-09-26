/**
 * 分镜 API（拉取 / 局部更新 / 本地校验）
 */
import { request } from "@/api/client";
import { validateStoryboard, type Shot, type StoryboardV1 } from "@/types/storyboard";

/** 拉取单集分镜 */
export function getStoryboard(
  projectId: string,
  episodeId = "ep01"
): Promise<StoryboardV1> {
  const query = `?project_id=${encodeURIComponent(projectId)}&episode_id=${encodeURIComponent(episodeId)}`;
  return request<StoryboardV1>(`/api/v1/storyboard${query}`);
}

/** 更新单个镜头（局部字段 PATCH） */
export function updateShot(
  episodeId: string,
  shotId: string,
  patch: Partial<Shot>
): Promise<Shot> {
  return request<Shot>(
    `/api/v1/storyboard/${encodeURIComponent(episodeId)}/shots/${encodeURIComponent(shotId)}`,
    { method: "PATCH", body: JSON.stringify(patch) }
  );
}

/** 本地校验分镜（不请求后端） */
export function validate(sb: StoryboardV1): string[] {
  return validateStoryboard(sb);
}
