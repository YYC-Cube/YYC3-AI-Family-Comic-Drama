"use client";

import { useCallback, useEffect, useRef, useState } from "react";

interface LogLine {
  ts: number;
  text: string;
}

interface RunStatus {
  state: "idle" | "running" | "completed" | "failed";
  batch: string | null;
  startedAt: number | null;
  endedAt: number | null;
  exitCode: number | null;
  runId: number;
}

const STATE_STYLE: Record<RunStatus["state"], string> = {
  idle: "text-(--muted)",
  running: "text-yellow-400",
  completed: "text-emerald-400",
  failed: "text-red-400",
};

const STATE_TEXT: Record<RunStatus["state"], string> = {
  idle: "空闲",
  running: "运行中",
  completed: "已完成",
  failed: "失败",
};

export default function PipelinePage() {
  const [logs, setLogs] = useState<LogLine[]>([]);
  const [status, setStatus] = useState<RunStatus | null>(null);
  const [batch, setBatch] = useState("");
  const [dryRun, setDryRun] = useState(true);
  const [connected, setConnected] = useState(false);
  const logBoxRef = useRef<HTMLDivElement>(null);
  const retryRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const esRef = useRef<EventSource | null>(null);

  // SSE 订阅：断线 3s 自动重连（对齐 benchmark ping/pong 重连模式）
  useEffect(() => {
    let disposed = false;
    const connect = () => {
      if (disposed) return;
      const es = new EventSource("/api/pipeline/stream");
      esRef.current = es;
      es.addEventListener("open", () => setConnected(true));
      es.addEventListener("state", (e) => setStatus(JSON.parse((e as MessageEvent).data)));
      es.addEventListener("log", (e) =>
        setLogs((prev) => {
          const next = [...prev, JSON.parse((e as MessageEvent).data)];
          return next.length > 2000 ? next.slice(-2000) : next;
        })
      );
      es.addEventListener("error", () => {
        setConnected(false);
        es.close();
        retryRef.current = setTimeout(connect, 3_000);
      });
    };
    connect();
    return () => {
      disposed = true;
      if (retryRef.current) clearTimeout(retryRef.current);
      esRef.current?.close();
    };
  }, []);

  // 自动滚底
  useEffect(() => {
    logBoxRef.current?.scrollTo({ top: logBoxRef.current.scrollHeight });
  }, [logs.length]);

  const trigger = useCallback(async () => {
    const res = await fetch("/api/pipeline/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ batch: batch.trim() || null, dryRun }),
    });
    const data = await res.json();
    if (!res.ok) alert(`触发失败: ${data.error}`);
  }, [batch, dryRun]);

  const running = status?.state === "running";

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">流水线控制 · 实时日志（SSE）</h1>
        <span className={`mono text-xs ${connected ? "text-emerald-400" : "text-red-400"}`}>
          {connected ? "● 已连接" : "○ 重连中…"}
        </span>
      </div>

      <section className="card flex flex-wrap items-end gap-4">
        <div>
          <div className="text-xs text-(--muted) mb-1">批次号（留空=自动递增）</div>
          <input
            value={batch}
            onChange={(e) => setBatch(e.target.value)}
            placeholder="如 03"
            className="mono bg-(--background) border border-(--border) rounded px-3 py-1.5 w-32"
          />
        </div>
        <label className="flex items-center gap-2 text-sm pb-1.5">
          <input type="checkbox" checked={dryRun} onChange={(e) => setDryRun(e.target.checked)} />
          演练模式（不实际生成，联调用）
        </label>
        <button
          onClick={trigger}
          disabled={running}
          className={`px-4 py-1.5 rounded font-semibold text-sm ${
            running ? "bg-(--border) text-(--muted) cursor-not-allowed" : "bg-(--accent) text-black"
          }`}
        >
          {running ? "运行中…" : "▶ 触发流水线"}
        </button>
        <div className="mono text-sm ml-auto">
          状态：<span className={STATE_STYLE[status?.state ?? "idle"]}>{STATE_TEXT[status?.state ?? "idle"]}</span>
          {status?.batch ? <span className="text-(--muted)"> · batch{status.batch}</span> : null}
          {status?.exitCode != null ? (
            <span className="text-(--muted)"> · exit={status.exitCode}</span>
          ) : null}
        </div>
      </section>

      <section className="card">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-(--muted)">实时输出（回填最近 300 行 · 心跳保活）</span>
          <button onClick={() => setLogs([])} className="text-xs text-(--muted) hover:text-(--foreground)">
            清屏
          </button>
        </div>
        <div
          ref={logBoxRef}
          className="mono text-xs leading-5 h-120 overflow-y-auto bg-(--background) border border-(--border) rounded p-3 whitespace-pre-wrap"
        >
          {logs.length === 0 ? (
            <span className="text-(--muted)">暂无输出 —— 触发流水线或等待运行事件…</span>
          ) : (
            logs.map((l, i) => (
              <div key={i} className="text-(--foreground)">
                <span className="text-(--muted) mr-2">{new Date(l.ts).toLocaleTimeString()}</span>
                {l.text}
              </div>
            ))
          )}
        </div>
      </section>
    </div>
  );
}
