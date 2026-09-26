import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** 合并 Tailwind 类名（clsx + tailwind-merge） */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/** 格式化成本：保留两位小数并追加单位“元” */
export function formatCost(value: number): string {
  return `${value.toFixed(2)} 元`;
}

/** 格式化时长：秒 → mm:ss */
export function formatDuration(totalSeconds: number): string {
  const safe = Math.max(0, Math.floor(totalSeconds));
  const minutes = Math.floor(safe / 60);
  const seconds = safe % 60;
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

/** 格式化百分比：输入 0-100，输出保留一位小数 */
export function formatPercent(value: number): string {
  return `${value.toFixed(1)}%`;
}
