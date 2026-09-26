"use client";

/**
 * 生产监控：核心指标 + 六阶段流水线 + 最近任务
 */
import { useMemo } from "react";
import { Activity, Clapperboard, Cpu, Gauge } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { StatCard } from "@/components/dashboard/stat-card";
import {
  WorkflowCanvas,
  type WorkflowStage,
} from "@/components/workflow/workflow-canvas";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useTaskStream } from "@/hooks/use-task-stream";
import { STAGES } from "@/lib/constants";
import { formatPercent } from "@/lib/utils";
import { useProjectStore } from "@/store/use-project-store";
import { useTaskStore } from "@/store/use-task-store";
import type { TaskStatus } from "@/types/task";

/** 任务状态 → 徽章变体 */
const STATUS_BADGE: Record<TaskStatus, { label: string; variant: "success" | "warning" | "destructive" | "secondary" | "outline" }> = {
  pending: { label: "待执行", variant: "outline" },
  running: { label: "执行中", variant: "warning" },
  success: { label: "成功", variant: "success" },
  failed: { label: "失败", variant: "destructive" },
  rework: { label: "返工", variant: "secondary" },
};

export default function ProductionPage() {
  const activeProjectId = useProjectStore((s) => s.activeProjectId);
  const tasks = useTaskStore((s) => s.tasks);
  const connected = useTaskStream(activeProjectId);

  const taskList = useMemo(() => [...tasks.values()], [tasks]);

  // 六阶段状态推导：running 优先 → failed → 全 done → idle
  const stages: WorkflowStage[] = useMemo(
    () =>
      STAGES.map(({ key, name }) => {
        const stageTasks = taskList.filter((t) => t.stage === key);
        if (stageTasks.some((t) => t.status === "running")) {
          return { key, name, status: "running" as const };
        }
        if (stageTasks.some((t) => t.status === "failed" || t.status === "rework")) {
          return { key, name, status: "failed" as const };
        }
        if (stageTasks.length > 0 && stageTasks.every((t) => t.status === "success")) {
          return { key, name, status: "done" as const };
        }
        return { key, name, status: "idle" as const };
      }),
    [taskList]
  );

  const runningCount = taskList.filter((t) => t.status === "running").length;
  const recentTasks = useMemo(
    () =>
      [...taskList]
        .sort((a, b) => b.updated_at.localeCompare(a.updated_at))
        .slice(0, 6),
    [taskList]
  );

  return (
    <div>
      <PageHeader
        title="生产监控"
        description={`六阶段自动化流水线实时状态 · ${connected ? "SSE 已连接" : "演示模式（SSE 未连接，进度模拟推进）"}`}
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="今日产量（集）"
          value="12"
          delta="+3 较昨日"
          trend="up"
          icon={<Clapperboard className="h-4 w-4" />}
        />
        <StatCard
          title="进行中任务"
          value={String(runningCount)}
          delta="流水线满载中"
          trend="flat"
          icon={<Activity className="h-4 w-4" />}
        />
        <StatCard
          title="一致性均分"
          value="0.83"
          delta="红线 0.80 已达标"
          trend="up"
          icon={<Gauge className="h-4 w-4" />}
        />
        <StatCard
          title="GPU 利用率"
          value={formatPercent(86.4)}
          delta="-2.1% 较昨日"
          trend="down"
          icon={<Cpu className="h-4 w-4" />}
        />
      </div>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="text-base">生产流水线</CardTitle>
        </CardHeader>
        <CardContent>
          <WorkflowCanvas stages={stages} />
        </CardContent>
      </Card>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="text-base">最近任务</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>任务 ID</TableHead>
                <TableHead>阶段</TableHead>
                <TableHead>Agent</TableHead>
                <TableHead>状态</TableHead>
                <TableHead className="text-right">进度</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {recentTasks.length === 0 && (
                <TableRow>
                  <TableCell colSpan={5} className="py-8 text-center text-muted-foreground">
                    暂无任务数据
                  </TableCell>
                </TableRow>
              )}
              {recentTasks.map((task) => (
                <TableRow key={task.task_id}>
                  <TableCell className="font-mono text-xs">{task.task_id}</TableCell>
                  <TableCell>
                    {STAGES.find((s) => s.key === task.stage)?.name ?? task.stage}
                  </TableCell>
                  <TableCell className="font-mono text-xs">{task.agent}</TableCell>
                  <TableCell>
                    <Badge variant={STATUS_BADGE[task.status].variant}>
                      {STATUS_BADGE[task.status].label}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {formatPercent(task.progress)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
