/**
 * 分镜状态：当前分镜、本地校验结果、镜头局部更新
 */
import { create } from "zustand";
import { getStoryboard, updateShot as apiUpdateShot } from "@/api/storyboard";
import { withFallback } from "@/api/client";
import { mockStoryboard } from "@/lib/mock-data";
import { validateStoryboard, type Shot, type StoryboardV1 } from "@/types/storyboard";

interface StoryboardState {
  storyboard: StoryboardV1 | null;
  validationErrors: string[];
  loading: boolean;
  isMock: boolean;
  /** 拉取分镜并自动执行本地校验 */
  load: (projectId: string) => Promise<void>;
  /** 更新镜头：先改本地，再尝试 PATCH 后端（失败静默，保持本地态） */
  updateShot: (shotId: string, patch: Partial<Shot>) => Promise<void>;
  /** 重新执行本地校验 */
  revalidate: () => void;
}

export const useStoryboardStore = create<StoryboardState>((set, get) => ({
  storyboard: null,
  validationErrors: [],
  loading: false,
  isMock: false,

  load: async (projectId) => {
    set({ loading: true });
    const { data, isMock } = await withFallback(
      () => getStoryboard(projectId),
      () => ({ ...mockStoryboard, project_id: projectId })
    );
    set({
      storyboard: data,
      isMock,
      loading: false,
      validationErrors: validateStoryboard(data),
    });
  },

  updateShot: async (shotId, patch) => {
    const sb = get().storyboard;
    if (!sb) return;

    // 乐观更新本地
    const shots = sb.shots.map((s) =>
      s.shot_id === shotId ? { ...s, ...patch } : s
    );
    const next: StoryboardV1 = {
      ...sb,
      shots,
      total_shots: shots.length,
      updated_at: new Date().toISOString(),
    };
    set({
      storyboard: next,
      validationErrors: validateStoryboard(next),
    });

    // 同步后端：失败静默（mock 演示场景常态）
    try {
      await apiUpdateShot(sb.episode_id, shotId, patch);
    } catch {
      // 后端不可达时保持本地态即可
    }
  },

  revalidate: () => {
    const sb = get().storyboard;
    set({ validationErrors: sb ? validateStoryboard(sb) : [] });
  },
}));
