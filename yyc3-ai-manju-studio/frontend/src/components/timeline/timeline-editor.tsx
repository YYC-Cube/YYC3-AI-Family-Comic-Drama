"use client";

/**
 * 时间线编辑器：标尺 + 视频轨 + 音频轨 + 播放头 + 缩放
 * 纯 React 实现，无第三方播放器依赖
 */
import { useEffect, useMemo, useRef, useState } from "react";
import { Minus, Pause, Plus, Star } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn, formatDuration } from "@/lib/utils";
import type { Shot } from "@/types/storyboard";

interface TimelineEditorProps {
  shots: Shot[];
  /** 初始缩放：每秒像素 */
  initialPxPerSec?: number;
  className?: string;
}

const TICK_INTERVAL_SEC = 5;

export function TimelineEditor({ shots, initialPxPerSec = 48, className }: TimelineEditorProps) {
  const [pxPerSec, setPxPerSec] = useState(initialPxPerSec);
  const [position, setPosition] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const rafRef = useRef<number | null>(null);
  const lastTsRef = useRef<number | null>(null);

  const totalDuration = useMemo(
    () => shots.reduce((sum, s) => sum + s.duration_sec, 0),
    [shots]
  );
  const width = Math.max(totalDuration * pxPerSec, 320);

  // 播放推进（requestAnimationFrame 平滑播放头）
  useEffect(() => {
    if (!playing) {
      lastTsRef.current = null;
      return;
    }
    const step = (ts: number) => {
      if (lastTsRef.current != null) {
        const dt = (ts - lastTsRef.current) / 1000;
        setPosition((prev) => {
          const next = prev + dt;
          if (next >= totalDuration) {
            setPlaying(false);
            return totalDuration;
          }
          return next;
        });
      }
      lastTsRef.current = ts;
      rafRef.current = requestAnimationFrame(step);
    };
    rafRef.current = requestAnimationFrame(step);
    return () => {
      if (rafRef.current != null) cancelAnimationFrame(rafRef.current);
    };
  }, [playing, totalDuration]);

  // 标尺刻度
  const ticks: number[] = [];
  for (let t = 0; t <= Math.ceil(totalDuration); t += TICK_INTERVAL_SEC) {
    ticks.push(t);
  }

  // 按 trackLeft 定位镜头块
  let cursor = 0;
  const videoBlocks = shots.map((shot) => {
    const left = cursor;
    cursor += shot.duration_sec;
    return { shot, left };
  });

  return (
    <div className={cn("space-y-3", className)}>
      {/* 工具栏 */}
      <div className="flex items-center gap-2">
        <Button size="sm" variant={playing ? "secondary" : "default"} onClick={() => setPlaying((p) => !p)}>
          {playing ? <Pause className="h-4 w-4" /> : null}
          {playing ? "暂停" : "播放"}
        </Button>
        <span className="text-xs tabular-nums text-muted-foreground">
          {formatDuration(position)} / {formatDuration(totalDuration)}
        </span>
        <div className="ml-auto flex items-center gap-1">
          <Button
            size="icon"
            variant="outline"
            aria-label="缩小时间线"
            disabled={pxPerSec <= 16}
            onClick={() => setPxPerSec((v) => Math.max(16, v - 16))}
          >
            <Minus className="h-4 w-4" />
          </Button>
          <span className="w-16 text-center text-xs tabular-nums text-muted-foreground">
            {pxPerSec} px/s
          </span>
          <Button
            size="icon"
            variant="outline"
            aria-label="放大时间线"
            disabled={pxPerSec >= 160}
            onClick={() => setPxPerSec((v) => Math.min(160, v + 16))}
          >
            <Plus className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* 轨道区 */}
      <div className="overflow-x-auto rounded-md border bg-muted/30 p-2">
        <div className="relative" style={{ width }}>
          {/* 标尺 */}
          <div className="relative h-6 border-b">
            {ticks.map((t) => (
              <div key={t} className="absolute top-0 h-full" style={{ left: t * pxPerSec }}>
                <div className="h-2 w-px bg-border" />
                <span className="ml-1 text-[10px] tabular-nums text-muted-foreground">
                  {formatDuration(t)}
                </span>
              </div>
            ))}
          </div>

          {/* 视频轨 */}
          <div className="relative mt-2 h-12">
            {videoBlocks.map(({ shot, left }) => (
              <button
                key={shot.shot_id}
                type="button"
                onClick={() => setSelectedId(shot.shot_id)}
                className={cn(
                  "absolute inset-y-0 flex items-center gap-1 truncate rounded-sm border px-2 text-left text-xs transition-colors",
                  selectedId === shot.shot_id
                    ? "border-primary bg-primary/20 ring-1 ring-primary"
                    : "border-primary/40 bg-primary/10 hover:bg-primary/20"
                )}
                style={{ left: left * pxPerSec, width: shot.duration_sec * pxPerSec - 2 }}
                title={`${shot.shot_id} · ${shot.shot_type}景 · ${shot.camera_move} · ${shot.duration_sec}s`}
              >
                {shot.hook_flag && <Star className="h-3 w-3 shrink-0 fill-amber-400 text-amber-400" />}
                <span className="truncate font-mono">{shot.shot_id}</span>
              </button>
            ))}
          </div>

          {/* 音频轨：BGM 上半 / SFX 下半 */}
          {(() => {
            let bgmLeft = 0;
            let sfxLeft = 0;
            return (
              <div className="relative mt-1 h-10">
                {shots.map((shot) => {
                  const bgmBlock = shot.bgm ? (
                    <div
                      key={`bgm-${shot.shot_id}`}
                      className="absolute left-0 top-0 h-4 truncate rounded-sm bg-emerald-500/25 px-1.5 text-[10px] leading-4 text-emerald-700"
                      style={{ left: bgmLeft * pxPerSec, width: shot.duration_sec * pxPerSec - 2 }}
                      title={`BGM：${shot.bgm}`}
                    >
                      {shot.bgm}
                    </div>
                  ) : null;
                  const sfxBlock = shot.sfx ? (
                    <div
                      key={`sfx-${shot.shot_id}`}
                      className="absolute bottom-0 h-4 truncate rounded-sm bg-amber-500/25 px-1.5 text-[10px] leading-4 text-amber-700"
                      style={{ left: sfxLeft * pxPerSec, width: shot.duration_sec * pxPerSec - 2 }}
                      title={`音效：${shot.sfx}`}
                    >
                      {shot.sfx}
                    </div>
                  ) : null;
                  bgmLeft += shot.duration_sec;
                  sfxLeft += shot.duration_sec;
                  return (
                    <div key={`audio-${shot.shot_id}`}>
                      {bgmBlock}
                      {sfxBlock}
                    </div>
                  );
                })}
              </div>
            );
          })()}

          {/* 播放头 */}
          <div
            className="pointer-events-none absolute top-0 bottom-0 z-10 w-px bg-red-500"
            style={{ left: position * pxPerSec }}
          >
            <div className="-ml-1.5 h-2.5 w-2.5 rotate-45 bg-red-500" />
          </div>
        </div>
      </div>
    </div>
  );
}
