/**
 * 进度条组件（轻量实现，不依赖 Radix）
 */
import * as React from "react";
import { cn } from "@/lib/utils";

interface ProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  /** 进度值 0-100 */
  value?: number;
  /** 进度条颜色类名（默认主色） */
  indicatorClassName?: string;
}

const Progress = React.forwardRef<HTMLDivElement, ProgressProps>(
  ({ className, value = 0, indicatorClassName, ...props }, ref) => {
    const clamped = Math.min(100, Math.max(0, value));
    return (
      <div
        ref={ref}
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={clamped}
        className={cn(
          "relative h-2 w-full overflow-hidden rounded-full bg-primary/15",
          className
        )}
        {...props}
      >
        <div
          className={cn(
            "h-full rounded-full bg-primary transition-all duration-500",
            indicatorClassName
          )}
          style={{ width: `${clamped}%` }}
        />
      </div>
    );
  }
);
Progress.displayName = "Progress";

export { Progress };
