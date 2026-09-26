/**
 * 指标卡：标题、值、同比、图标
 */
import type { ReactNode } from "react";
import { ArrowDownRight, ArrowUpRight, Minus } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface StatCardProps {
  title: string;
  value: string;
  /** 同比变化文案，如 "+12.4%" */
  delta?: string;
  /** 趋势方向：up 好 / down 差 / flat 持平 */
  trend?: "up" | "down" | "flat";
  icon?: ReactNode;
  className?: string;
}

export function StatCard({ title, value, delta, trend = "flat", icon, className }: StatCardProps) {
  const TrendIcon = trend === "up" ? ArrowUpRight : trend === "down" ? ArrowDownRight : Minus;
  const trendColor =
    trend === "up"
      ? "text-emerald-600"
      : trend === "down"
        ? "text-red-600"
        : "text-muted-foreground";

  return (
    <Card className={className}>
      <CardContent className="flex items-start justify-between p-5">
        <div>
          <p className="text-sm text-muted-foreground">{title}</p>
          <p className="mt-1.5 text-2xl font-semibold tabular-nums">{value}</p>
          {delta && (
            <p className={cn("mt-1 flex items-center gap-1 text-xs", trendColor)}>
              <TrendIcon className="h-3.5 w-3.5" />
              <span>{delta}</span>
            </p>
          )}
        </div>
        {icon && (
          <div className="rounded-md bg-muted p-2 text-muted-foreground">{icon}</div>
        )}
      </CardContent>
    </Card>
  );
}
