"use client";

/**
 * 分镜工作台：镜头表 + 本地校验结果 + JSON 预览
 */
import { useEffect } from "react";
import { CheckCircle2, Loader2, XCircle } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
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
import { useStoryboardStore } from "@/store/use-storyboard-store";
import { useProjectStore } from "@/store/use-project-store";
import { formatDuration } from "@/lib/utils";

export default function StoryboardPage() {
  const activeProjectId = useProjectStore((s) => s.activeProjectId);
  const storyboard = useStoryboardStore((s) => s.storyboard);
  const validationErrors = useStoryboardStore((s) => s.validationErrors);
  const loading = useStoryboardStore((s) => s.loading);
  const isMock = useStoryboardStore((s) => s.isMock);
  const load = useStoryboardStore((s) => s.load);

  useEffect(() => {
    if (activeProjectId) void load(activeProjectId);
  }, [activeProjectId, load]);

  const passed = validationErrors.length === 0;

  return (
    <div>
      <PageHeader
        title="分镜工作台"
        description="镜头级剧本结构：景别 / 运镜 / 台词 / 钩子标记 / 一致性锚定"
        actions={
          <>
            {isMock && <Badge variant="warning">演示数据</Badge>}
            {storyboard && (
              <Badge variant="secondary">
                {storyboard.episode_title} · {storyboard.shots.length} 镜
              </Badge>
            )}
          </>
        }
      />

      {/* 校验结果条 */}
      <div
        className={`mb-4 rounded-md border p-4 ${
          passed
            ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-700"
            : "border-red-500/40 bg-red-500/10 text-red-700"
        }`}
      >
        <div className="flex items-center gap-2 text-sm font-medium">
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : passed ? (
            <CheckCircle2 className="h-4 w-4" />
          ) : (
            <XCircle className="h-4 w-4" />
          )}
          {loading
            ? "分镜校验中…"
            : passed
              ? "分镜校验通过：结构完整，钩子镜头已标记"
              : `分镜校验发现 ${validationErrors.length} 个问题`}
        </div>
        {!passed && (
          <ul className="mt-2 list-inside list-disc space-y-0.5 text-xs">
            {validationErrors.map((err) => (
              <li key={err}>{err}</li>
            ))}
          </ul>
        )}
      </div>

      <div className="grid gap-4 xl:grid-cols-[1fr_380px]">
        {/* 镜头表 */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">镜头列表</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>镜头 ID</TableHead>
                  <TableHead>景别</TableHead>
                  <TableHead>运镜</TableHead>
                  <TableHead>台词</TableHead>
                  <TableHead className="text-right">时长</TableHead>
                  <TableHead>钩子</TableHead>
                  <TableHead>一致性锚定</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(storyboard?.shots ?? []).map((shot) => (
                  <TableRow key={shot.shot_id}>
                    <TableCell className="font-mono text-xs">{shot.shot_id}</TableCell>
                    <TableCell>{shot.shot_type}</TableCell>
                    <TableCell>{shot.camera_move}</TableCell>
                    <TableCell className="max-w-[240px] truncate text-muted-foreground">
                      {shot.dialogue || "（无台词）"}
                    </TableCell>
                    <TableCell className="text-right tabular-nums">
                      {formatDuration(shot.duration_sec)}
                    </TableCell>
                    <TableCell>
                      {shot.hook_flag ? (
                        <Badge variant="warning">钩子</Badge>
                      ) : (
                        <span className="text-xs text-muted-foreground">-</span>
                      )}
                    </TableCell>
                    <TableCell className="font-mono text-xs text-muted-foreground">
                      {shot.consistency_anchor}
                    </TableCell>
                  </TableRow>
                ))}
                {!loading && (storyboard?.shots.length ?? 0) === 0 && (
                  <TableRow>
                    <TableCell colSpan={7} className="py-8 text-center text-muted-foreground">
                      暂无分镜数据，请先在剧本编辑页提取分镜
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* JSON 预览 */}
        <Card className="h-fit xl:sticky xl:top-20">
          <CardHeader>
            <CardTitle className="text-base">StoryboardV1 协议预览</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="max-h-[400px] overflow-auto rounded-md bg-zinc-950 p-3 font-mono text-[11px] leading-5 text-zinc-200">
              {storyboard ? JSON.stringify(storyboard, null, 2) : "// 暂无数据"}
            </pre>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
