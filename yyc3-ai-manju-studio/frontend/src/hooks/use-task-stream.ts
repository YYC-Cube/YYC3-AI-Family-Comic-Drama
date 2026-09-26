"use client";

/**
 * useTaskStream：任务 SSE 流连接生命周期 + mock 降级轮询
 *
 * - 挂载时 connect(projectId)，卸载时 disconnect
 * - 真实 SSE 未连接（connected=false，含后端未实现场景）时，
 *   每 2 秒调用 simulateProgress 模拟 running 任务推进，
 *   保证演示态下任务进度仍可动态变化
 */
import { useEffect } from "react";
import { useTaskStore } from "@/store/use-task-store";

export function useTaskStream(projectId: string | null): { connected: boolean } {
  const connect = useTaskStore((s) => s.connect);
  const disconnect = useTaskStore((s) => s.disconnect);
  const simulateProgress = useTaskStore((s) => s.simulateProgress);
  const connected = useTaskStore((s) => s.connected);

  useEffect(() => {
    if (!projectId) return;
    void connect(projectId);
    return () => disconnect();
  }, [projectId, connect, disconnect]);

  useEffect(() => {
    if (connected) return; // 真实流在线，无需模拟
    const timer = setInterval(() => simulateProgress(), 2000);
    return () => clearInterval(timer);
  }, [connected, simulateProgress]);

  return { connected };
}
