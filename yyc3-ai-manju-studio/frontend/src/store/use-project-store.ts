/**
 * 项目状态：列表、当前激活项目、拉取与新建
 */
import { create } from "zustand";
import { createProject as apiCreateProject, listProjects } from "@/api/project";
import { withFallback } from "@/api/client";
import { mockProjects } from "@/lib/mock-data";
import type { CreateProjectInput, Project } from "@/types/project";

interface ProjectState {
  projects: Project[];
  activeProjectId: string | null;
  loading: boolean;
  /** 当前数据是否来自 mock 降级 */
  isMock: boolean;
  setActive: (projectId: string) => void;
  fetchProjects: () => Promise<void>;
  /** 新建项目：优先走真实 API，失败则本地追加演示数据 */
  createProject: (input: CreateProjectInput) => Promise<void>;
}

export const useProjectStore = create<ProjectState>((set, get) => ({
  projects: [],
  activeProjectId: null,
  loading: false,
  isMock: false,

  setActive: (projectId) => set({ activeProjectId: projectId }),

  fetchProjects: async () => {
    if (get().loading) return;
    set({ loading: true });
    const { data, isMock } = await withFallback(listProjects, () => mockProjects);
    set((state) => ({
      projects: data,
      isMock,
      loading: false,
      // 默认激活第一个项目
      activeProjectId: state.activeProjectId ?? data[0]?.project_id ?? null,
    }));
  },

  createProject: async (input) => {
    const { data, isMock } = await withFallback(() => apiCreateProject(input), () => ({
      project_id: `proj-local-${Date.now()}`,
      title: input.title,
      novice_source: input.novice_source,
      episode_target: input.episode_target,
      status: "draft" as const,
      cost: 0,
      created_at: new Date().toISOString(),
    }));
    set((state) => ({
      projects: [...state.projects, data],
      activeProjectId: data.project_id,
      isMock: state.isMock || isMock,
    }));
  },
}));
