"use client";

/**
 * 项目管理：项目列表 + 行内新建表单
 */
import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { PageHeader } from "@/components/layout/page-header";
import { useProjectStore } from "@/store/use-project-store";
import { formatCost } from "@/lib/utils";
import type { ProjectStatus } from "@/types/project";

const STATUS_BADGE: Record<ProjectStatus, { label: string; variant: "success" | "warning" | "secondary" }> = {
  draft: { label: "草稿", variant: "secondary" },
  producing: { label: "生产中", variant: "warning" },
  completed: { label: "已完结", variant: "success" },
};

export default function ProjectPage() {
  const projects = useProjectStore((s) => s.projects);
  const isMock = useProjectStore((s) => s.isMock);
  const createProject = useProjectStore((s) => s.createProject);

  const [title, setTitle] = useState("");
  const [noviceSource, setNoviceSource] = useState("");
  const [episodeTarget, setEpisodeTarget] = useState("");
  const [creating, setCreating] = useState(false);

  const handleCreate = async () => {
    if (!title.trim()) return;
    setCreating(true);
    await createProject({
      title: title.trim(),
      novice_source: noviceSource.trim() || "未指定",
      episode_target: Math.max(1, Number(episodeTarget) || 1),
    });
    setTitle("");
    setNoviceSource("");
    setEpisodeTarget("");
    setCreating(false);
  };

  return (
    <div>
      <PageHeader
        title="项目管理"
        description="管理小说 IP 到漫剧的项目全生命周期"
        actions={isMock ? <Badge variant="warning">演示数据</Badge> : undefined}
      />

      {/* 行内新建表单 */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-base">新建项目</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-center gap-2">
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="项目名称，如：万古神帝"
              className="w-56"
            />
            <Input
              value={noviceSource}
              onChange={(e) => setNoviceSource(e.target.value)}
              placeholder="小说源文件，如：novel.txt"
              className="w-64"
            />
            <Input
              value={episodeTarget}
              onChange={(e) => setEpisodeTarget(e.target.value.replace(/\D/g, ""))}
              placeholder="目标集数"
              className="w-28"
              inputMode="numeric"
            />
            <Button onClick={handleCreate} disabled={creating || !title.trim()}>
              {creating ? "创建中…" : "创建项目"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 项目列表 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">项目列表（{projects.length}）</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>项目名称</TableHead>
                <TableHead>状态</TableHead>
                <TableHead>集数目标</TableHead>
                <TableHead className="text-right">累计成本</TableHead>
                <TableHead className="text-right">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {projects.length === 0 && (
                <TableRow>
                  <TableCell colSpan={5} className="py-8 text-center text-muted-foreground">
                    暂无项目，请先创建
                  </TableCell>
                </TableRow>
              )}
              {projects.map((project) => (
                <TableRow key={project.project_id}>
                  <TableCell>
                    <p className="font-medium">{project.title}</p>
                    <p className="text-xs text-muted-foreground">
                      原著：{project.novice_source}
                    </p>
                  </TableCell>
                  <TableCell>
                    <Badge variant={STATUS_BADGE[project.status].variant}>
                      {STATUS_BADGE[project.status].label}
                    </Badge>
                  </TableCell>
                  <TableCell className="tabular-nums">{project.episode_target} 集</TableCell>
                  <TableCell className="text-right tabular-nums">
                    {formatCost(project.cost)}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => useProjectStore.getState().setActive(project.project_id)}
                    >
                      切换为当前项目
                    </Button>
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
