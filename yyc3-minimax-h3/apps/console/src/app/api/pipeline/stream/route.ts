// /api/pipeline/stream - SSE: replay last 300 lines then live tail; state event on
// transition; 15s heartbeat keepalive (benchmark ping/pong pattern, client auto-reconnect).
import { pipelineManager, type FileChange, type LogLine } from "@/lib/pipeline-manager";

export const dynamic = "force-dynamic";

const HEARTBEAT_MS = 15_000;

export async function GET() {
  const encoder = new TextEncoder();
  let unsubscribe: (() => void) | null = null;
  let unsubscribeFiles: (() => void) | null = null;
  let heartbeat: ReturnType<typeof setInterval> | null = null;
  const stateTimers = new Set<ReturnType<typeof setInterval>>();

  const stream = new ReadableStream({
    start(controller) {
      const send = (event: string, data: unknown) => {
        try {
          controller.enqueue(encoder.encode(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`));
        } catch {
          // 客户端断开时 enqueue 可能抛错——由 cancel 清理
        }
      };

      // 1) 回填（断线重连不丢上下文）
      const { status, logs } = pipelineManager.replay();
      send("state", status);
      for (const line of logs) send("log", line);

      // 2) 实时订阅（日志 + 文件变更）
      unsubscribe = pipelineManager.subscribe((line: LogLine) => send("log", line));
      unsubscribeFiles = pipelineManager.subscribeFiles((change: FileChange) => send("file", change));

      // 3) 状态轮询广播（manager 内部 close → completed/failed）
      let lastState = status.state;
      const stateTimer = setInterval(() => {
        const cur = pipelineManager.getStatus();
        if (cur.state !== lastState) {
          lastState = cur.state;
          send("state", cur);
        }
      }, 2_000);

      // 4) 心跳（代理/客户端保活）
      heartbeat = setInterval(() => {
        try {
          controller.enqueue(encoder.encode(`: ping\n\n`));
        } catch {
          /* noop */
        }
      }, HEARTBEAT_MS);

      // 客户端断开 → cancel() 统一清理（stateTimer 挂到闭包供其访问）
      stateTimers.add(stateTimer);
    },
    cancel() {
      if (heartbeat) clearInterval(heartbeat);
      unsubscribe?.();
      unsubscribeFiles?.();
      for (const t of stateTimers) clearInterval(t);
      stateTimers.clear();
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
      "X-Accel-Buffering": "no",
    },
  });
}
