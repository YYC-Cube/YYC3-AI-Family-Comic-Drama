"use client";

/**
 * 运营数据：核心指标 + 近 7 日播放量柱状图（纯 div 实现）
 */
import { StatCard } from "@/components/dashboard/stat-card";
import { PageHeader } from "@/components/layout/page-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { mockDailyPlays } from "@/lib/mock-operations";
import { Flame, ThumbsUp, Watch } from "lucide-react";

/** 播放量格式化：万为单位 */
function formatPlays(n: number): string {
  return `${(n / 10000).toFixed(1)} 万`;
}

export default function AnalyticsPage() {
  const maxPlays = Math.max(...mockDailyPlays.map((d) => d.plays));

  return (
    <div>
      <PageHeader
        title="运营数据"
        description="发布效果回流：完播、互动与爆款指数驱动下一轮创意反哺"
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="平均完播率"
          value="42.6%"
          delta="+5.2% 较上周"
          trend="up"
          icon={<Watch className="h-4 w-4" />}
        />
        <StatCard
          title="平均点赞率"
          value="8.9%"
          delta="+1.3% 较上周"
          trend="up"
          icon={<ThumbsUp className="h-4 w-4" />}
        />
        <StatCard
          title="爆款指数"
          value="76"
          delta="阈值 70，已入爆款池"
          trend="up"
          icon={<Flame className="h-4 w-4" />}
        />
        <StatCard
          title="7 日总播放"
          value={formatPlays(mockDailyPlays.reduce((s, d) => s + d.plays, 0))}
          delta="环比 +18.4%"
          trend="up"
        />
      </div>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="text-base">近 7 日播放量</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex h-56 items-end gap-3">
            {mockDailyPlays.map((d) => (
              <div
                key={d.date}
                className="group flex h-full flex-1 flex-col items-center justify-end gap-2"
                title={`${d.date}：${formatPlays(d.plays)}`}
              >
                <span className="text-[10px] tabular-nums text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100">
                  {formatPlays(d.plays)}
                </span>
                <div
                  className="w-full max-w-14 rounded-t-md bg-primary/70 transition-colors group-hover:bg-primary"
                  style={{ height: `${(d.plays / maxPlays) * 100}%` }}
                />
                <span className="text-xs text-muted-foreground">{d.date}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
