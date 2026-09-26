"use client";

/**
 * 视频预览：HTML5 video 封装 + 镜头信息叠层
 * NAS 成片路径当前无 HTTP 映射，无可用 src 时展示占位说明卡
 */
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Video } from "lucide-react";
import { NAS_BASE } from "@/lib/constants";
import type { Shot } from "@/types/storyboard";

interface VideoPreviewProps {
  /** 视频地址（可传 NAS 路径，将原样透传给 video 标签） */
  src?: string;
  /** 当前镜头信息（叠层展示） */
  shot?: Shot;
  /** 一致性分数 0-1 */
  consistencyScore?: number;
  /** 占位说明用项目 ID */
  projectId?: string;
  className?: string;
}

export function VideoPreview({
  src,
  shot,
  consistencyScore,
  projectId = "{project_id}",
  className,
}: VideoPreviewProps) {
  const hasSource = typeof src === "string" && src.trim() !== "";

  return (
    <Card className={className}>
      <CardContent className="p-4">
        {hasSource ? (
          <div className="relative overflow-hidden rounded-md bg-black">
            {/* NAS 路径需网关提供静态映射后才可播放；当前原样透传 */}
            <video className="aspect-video w-full" controls src={src} preload="metadata" />
            <div className="absolute left-3 top-3 flex items-center gap-2 rounded-md bg-black/60 px-2.5 py-1.5">
              <span className="font-mono text-xs text-white">{shot?.shot_id ?? "预览"}</span>
              {shot && (
                <Badge variant="secondary">
                  {shot.shot_type}景 · {shot.camera_move}
                </Badge>
              )}
              {typeof consistencyScore === "number" && (
                <Badge variant={consistencyScore >= 0.8 ? "success" : "warning"}>
                  一致性 {consistencyScore.toFixed(2)}
                </Badge>
              )}
            </div>
          </div>
        ) : (
          <div className="flex aspect-video w-full flex-col items-center justify-center gap-3 rounded-md border border-dashed bg-muted/40 text-center">
            <Video className="h-10 w-10 text-muted-foreground" />
            <div className="max-w-md space-y-1 px-4">
              <p className="text-sm font-medium">暂无可播放的成片流</p>
              <p className="text-xs leading-5 text-muted-foreground">
                合成后的成片位于 NAS：{NAS_BASE}projects/{projectId}/output/
              </p>
              <p className="text-xs leading-5 text-muted-foreground">
                待网关开通 NAS 静态资源映射后，此处将直接内联播放
              </p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
