"use client";

/**
 * 顶栏：项目切换、网关连接状态、版本号
 */
import { useEffect } from "react";
import { Badge } from "@/components/ui/badge";
import { useProjectStore } from "@/store/use-project-store";
import { useTaskStore } from "@/store/use-task-store";

export const APP_VERSION = "v1.0.0";

export function Topbar() {
  const projects = useProjectStore((s) => s.projects);
  const activeProjectId = useProjectStore((s) => s.activeProjectId);
  const setActive = useProjectStore((s) => s.setActive);
  const fetchProjects = useProjectStore((s) => s.fetchProjects);
  const connected = useTaskStore((s) => s.connected);

  // 顶栏挂载时拉取项目列表（全局仅此一处触发）
  useEffect(() => {
    void fetchProjects();
  }, [fetchProjects]);

  const activeTitle =
    projects.find((p) => p.project_id === activeProjectId)?.title ?? "加载中";

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-4 border-b bg-background/95 px-6 backdrop-blur">
      <label className="flex items-center gap-2 text-sm text-muted-foreground">
        当前项目
        <select
          value={activeProjectId ?? ""}
          onChange={(e) => setActive(e.target.value)}
          className="h-8 rounded-md border border-input bg-background px-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
          aria-label="切换当前项目"
        >
          {projects.length === 0 && <option value="">{activeTitle}</option>}
          {projects.map((p) => (
            <option key={p.project_id} value={p.project_id}>
              {p.title}
            </option>
          ))}
        </select>
      </label>

      <Badge variant={connected ? "success" : "outline"}>
        {connected ? "网关已连接" : "网关离线"}
      </Badge>

      <span className="ml-auto text-xs text-muted-foreground">{APP_VERSION}</span>
    </header>
  );
}
