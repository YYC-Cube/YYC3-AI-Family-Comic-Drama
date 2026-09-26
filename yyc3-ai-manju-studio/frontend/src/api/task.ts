/**
 * 生产任务 API（列表 / 详情 / SSE 流订阅）
 */
import { API_BASE, request } from "@/api/client";
import type { ProductionTask } from "@/types/task";

/** 任务列表（可按项目过滤） */
export function listTasks(projectId?: string): Promise<ProductionTask[]> {
  const query = projectId
    ? `?project_id=${encodeURIComponent(projectId)}`
    : "";
  return request<ProductionTask[]>(`/api/v1/tasks${query}`);
}

/** 任务详情 */
export function getTask(taskId: string): Promise<ProductionTask> {
  return request<ProductionTask>(
    `/api/v1/tasks/${encodeURIComponent(taskId)}`
  );
}

/**
 * 订阅任务进度 SSE 流
 * 返回 close 函数用于组件卸载时断开连接
 * onStatusChange：可选的连接状态回调（open → true / error → false）
 */
export function subscribeTaskStream(
  projectId: string,
  onEvent: (task: ProductionTask) => void,
  onStatusChange?: (connected: boolean) => void
): () => void {
  const url = `${API_BASE}/api/v1/tasks/stream?project_id=${encodeURIComponent(projectId)}`;
  const source = new EventSource(url);

  source.onopen = () => onStatusChange?.(true);

  source.onmessage = (event: MessageEvent<string>) => {
    try {
      const task = JSON.parse(event.data) as ProductionTask;
      onEvent(task);
    } catch {
      // 单条消息解析失败不影响流，忽略
    }
  };

  source.onerror = () => onStatusChange?.(false);

  return () => source.close();
}
