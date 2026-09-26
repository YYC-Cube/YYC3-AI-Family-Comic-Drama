"use client";

/**
 * 时间线剪辑：时间线编辑器 + 成片预览（上下布局）
 */
import { PageHeader } from "@/components/layout/page-header";
import { TimelineEditor } from "@/components/timeline/timeline-editor";
import { VideoPreview } from "@/components/preview/video-preview";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useStoryboardStore } from "@/store/use-storyboard-store";
import { useProjectStore } from "@/store/use-project-store";

export default function VideoPage() {
  const activeProjectId = useProjectStore((s) => s.activeProjectId);
  const storyboard = useStoryboardStore((s) => s.storyboard);
  const shots = storyboard?.shots ?? [];

  return (
    <div>
      <PageHeader
        title="时间线剪辑"
        description="镜头轨与音画轨对齐预览；成片合成后回传 NAS 归档"
      />

      <Card>
        <CardHeader>
          <CardTitle className="text-base">时间线（{shots.length} 镜）</CardTitle>
        </CardHeader>
        <CardContent>
          <TimelineEditor shots={shots} />
        </CardContent>
      </Card>

      <div className="mt-6">
        <VideoPreview
          projectId={activeProjectId ?? "{project_id}"}
          shot={shots[0]}
          consistencyScore={0.83}
        />
      </div>
    </div>
  );
}
