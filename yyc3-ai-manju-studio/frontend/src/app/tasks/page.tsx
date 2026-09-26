"use client";

/**
 * 任务监控：全量任务表 + SSE 实时流（失败时演示模式轮询推进）
 */
import { useTaskStream } from "@/hooks/use-task-stream";
import { PageHeader } from "@/components/layout/page-header";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { STAGES } from "@/lib/constants";
import { formatPercent } from "@/lib/utils";
import { useProjectStore } from "@/store/use-project-store";
import { useTaskStore } from "@/store/use-task-store";
import type { TaskStatus } from "@/types/task";

const STATUS_BADGE: Record<TaskStatus, { label: string; variant: "success" | "warning" | "destructive" | "secondary" | "outline" }> = {
  pending: { label: "待执行", variant: "outline" },
  running: { label: "执行中", variant: "warning" },
  success: { label: "成功", variant: "success" },
  failed: { label: "失败", variant: "destructive" },
  rework: { label: "返工", variant: "secondary" },
};

export default function TasksPage() {
  const activeProjectId = useProjectStore((s) => s.activeProjectId);
  const tasks = useTaskStore((s) => s.tasks);
  const isMock = useTaskStore((s) => s.isMock);
  const { connected } = useTaskStream(activeProjectId);

  const taskList = [...tasks.values()].sort((a, b) =>
    b.updated_at.localeCompare(a.updated_at)
  );

  return (
    <div>
      <PageHeader
        title="任务监控"
        description="六阶段 Agent 任务全链路追踪，支持 trace_id 回溯"
        actions={
          <>
            <Badge variant={connected ? "success" : "outline"}>
              {connected ? "SSE 实时推送中" : "演示模式（2s 轮询模拟）"}
            </Badge>
            {isMock && <Badge variant="warning">演示数据</Badge>}
          </>
        }
      />

      <Card>
        <CardHeader>
          <CardTitle className="text-base">任务列表（{taskList.length}）</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>任务 ID</TableHead>
                <TableHead>阶段</TableHead>
                <TableHead>Agent</TableHead>
                <TableHead>状态</TableHead>
                <TableHead className="w-[180px]">进度</TableHead>
                <TableHead>trace_id</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {taskList.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} className="py-8 text-center text-muted-foreground">
                    暂无任务数据
                  </TableCell>
                </TableRow>
              )}
              {taskList.map((task) => (
                <TableRow key={task.task_id}>
                  <TableCell className="font-mono text-xs">{task.task_id}</TableCell>
                  <TableCell>
                    <Badge variant="secondary">
                      {STAGES.find((s) => s.key === task.stage)?.name ?? task.stage}
                    </Badge>
                  </TableCell>
                  <TableCell className="font-mono text-xs">{task.agent}</TableCell>
                  <TableCell>
                    <div className="space-y-1">
                      <Badge variant={STATUS_BADGE[task.status].variant}>
                        {STATUS_BADGE[task.status].label}
                      </Badge>
                      {task.error && (
                        <p className="max-w-[260px] truncate text-xs text-red-600" title={task.error}>
                          {task.error}
                        </p>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Progress value={task.progress} className="w-24" />
                      <span className="text-xs tabular-nums text-muted-foreground">
                        {formatPercent(task.progress)}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell className="font-mono text-xs text-muted-foreground">
                    {task.trace_id}
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
