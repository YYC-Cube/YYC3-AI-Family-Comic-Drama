/**
 * 任务状态：任务 Map、SSE 连接生命周期、mock 进度模拟
 */
import { withFallback } from "@/api/client";
import { listTasks, subscribeTaskStream } from "@/api/task";
import { mockTasks } from "@/lib/mock-data";
import type { ProductionTask } from "@/types/task";
import { create } from "zustand";

interface TaskState {
  /** task_id → 任务 */
  tasks: Map<string, ProductionTask>;
  /** SSE 是否已连接（真实流在线） */
  connected: boolean;
  /** 初始列表是否来自 mock 降级 */
  isMock: boolean;
  /** 当前订阅的项目 ID */
  projectId: string | null;
  /** 连接 SSE 并拉取初始列表；重复调用会先断开旧连接 */
  connect: (projectId: string) => Promise<void>;
  disconnect: () => void;
  /** 直接写入/更新一个任务（SSE 事件入口） */
  upsertTask: (task: ProductionTask) => void;
  /**
   * mock 轮询推进：SSE 不可用时由页面 hook 每 2s 调一次
   * 随机挑选 running 任务 +5% 进度，到 100 转 success；不足时提升 pending 为 running
   */
  simulateProgress: () => void;
}

export const useTaskStore = create<TaskState>((set, get) => {
  let closeStream: (() => void) | null = null;

  const upsert = (task: ProductionTask) => {
    set((state) => {
      const next = new Map(state.tasks);
      next.set(task.task_id, task);
      return { tasks: next };
    });
  };

  return {
    tasks: new Map(),
    connected: false,
    isMock: false,
    projectId: null,

    connect: async (projectId) => {
      // 幂等：同一项目重复 connect 不重复建流
      if (get().projectId === projectId && closeStream) return;
      closeStream?.();
      closeStream = null;
      set({ projectId, tasks: new Map(), connected: false });

      // 初始列表：真实优先，失败降级 mock
      const { data, isMock } = await withFallback(
        () => listTasks(projectId),
        () => mockTasks
      );
      const initial = new Map<string, ProductionTask>(
        data.map((t) => [t.task_id, t])
      );
      // 拉取期间可能已断开，避免脏写
      if (get().projectId !== projectId) return;
      set({ tasks: initial, isMock });

      // 订阅真实 SSE 流（失败仅影响 connected 标志，由 hook 启动 mock 轮询）
      closeStream = subscribeTaskStream(projectId, upsert, (connected) => {
        set({ connected });
      });
    },

    disconnect: () => {
      closeStream?.();
      closeStream = null;
      set({ connected: false, projectId: null });
    },

    upsertTask: upsert,

    simulateProgress: () => {
      const state = get();
      if (state.connected) return; // 真实流在线时不模拟
      const next = new Map(state.tasks);
      const all = [...next.values()];

      // 1) running 任务随机推进 +5%
      const running = all.filter((t) => t.status === "running");
      if (running.length > 0) {
        const pick = running[Math.floor(Math.random() * running.length)];
        const target = next.get(pick.task_id);
        if (target) {
          const progress = Math.min(100, target.progress + 5);
          next.set(target.task_id, {
            ...target,
            progress,
            status: progress >= 100 ? "success" : "running",
            updated_at: new Date().toISOString(),
          });
        }
      } else {
        // 2) 无 running 时提升 pending → running（保持流水线动感）
        const pending = all.filter((t) => t.status === "pending");
        if (pending.length > 0) {
          const pick = pending[Math.floor(Math.random() * pending.length)];
          const target = next.get(pick.task_id);
          if (target) {
            next.set(target.task_id, {
              ...target,
              status: "running",
              progress: 1,
              updated_at: new Date().toISOString(),
            });
          }
        }
      }
      set({ tasks: next });
    },
  };
});
