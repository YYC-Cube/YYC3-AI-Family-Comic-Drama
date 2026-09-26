import { displayScore, readBatchesPayload, readManifests } from "@/lib/manifest";
import type { Manifest } from "@yyc3/manifest-schema";
import Link from "next/link";
import RefreshOnChange from "./refresh-on-change";

// manifest 是文件系统数据：每次请求重读（对齐「断点续跑」工作流，面板跑完即见）
export const dynamic = "force-dynamic";

function Stat({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="card">
      <div className="text-xs text-(--muted)">{label}</div>
      <div className="mono text-2xl font-bold mt-1" style={{ color: "var(--accent)" }}>
        {value}
      </div>
      {hint ? <div className="text-xs text-(--muted) mt-1">{hint}</div> : null}
    </div>
  );
}

export default function DashboardPage() {
  const { manifests, errors } = readManifests();
  const payload = readBatchesPayload();

  const totalRecords = manifests.reduce((n, m) => n + m.records.length, 0);
  const successRecords = manifests.reduce(
    (n, m) => n + m.records.filter((r) => r.status === "SUCCESS").length,
    0
  );
  const scores = manifests.flatMap((m) =>
    m.records.filter((r) => r.status === "SUCCESS").map(displayScore).filter((s) => s.source !== "none")
  );
  const avg = scores.length ? (scores.reduce((a, s) => a + s.score, 0) / scores.length).toFixed(2) : "-";
  const top = payload?.top10?.[0];

  return (
    <div className="space-y-6">
      <RefreshOnChange />
      <section>
        <h1 className="text-xl font-bold mb-4">仪表盘 · 单一事实源直读</h1>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Stat label="批次总数" value={String(manifests.length)} />
          <Stat label="生成记录" value={`${successRecords}/${totalRecords}`} hint="SUCCESS / 全部" />
          <Stat label="平均分（0-10）" value={avg} hint="human 优先，lipsync×10 回退" />
          <Stat label="Top1" value={top ? `${top.seed}` : "-"} hint={top ? `${top.batch} · ${top.score} 分` : "暂无"} />
        </div>
      </section>

      {errors.length > 0 ? (
        <section className="card border-yellow-700">
          <div className="text-sm text-yellow-400">⚠ schema 校验警告（双端契约漂移检查）</div>
          <ul className="mono text-xs text-(--muted) mt-2 space-y-1">
            {errors.map((e) => (
              <li key={e}>{e}</li>
            ))}
          </ul>
        </section>
      ) : null}

      <section>
        <h2 className="font-semibold mb-3">批次明细（RSC 直读 manifest.json）</h2>
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-(--muted) border-b border-(--border)">
                <th className="py-2 pr-4">批次</th>
                <th className="py-2 pr-4">模型</th>
                <th className="py-2 pr-4">开始时间</th>
                <th className="py-2 pr-4">成功/失败/跳过</th>
                <th className="py-2 pr-4">均分</th>
                <th className="py-2 pr-4">耗时(min)</th>
                <th className="py-2">状态</th>
              </tr>
            </thead>
            <tbody className="mono">
              {manifests.map((m) => {
                const success = m.records.filter((r) => r.status === "SUCCESS").length;
                const failed = m.records.filter((r) => r.status !== "SUCCESS" && r.status !== "SKIPPED").length;
                const skipped = m.records.filter((r) => r.status === "SKIPPED").length;
                const bs: number[] = scoresOf(m);
                const batchAvg = bs.length
                  ? (bs.reduce((a: number, b: number) => a + b, 0) / bs.length).toFixed(2)
                  : "-";
                const dur =
                  m.ended_at && m.started_at
                    ? ((new Date(m.ended_at).getTime() - new Date(m.started_at).getTime()) / 60000).toFixed(1)
                    : "-";
                return (
                  <tr key={m.batch} className="border-b border-(--border) last:border-0">
                    <td className="py-2 pr-4">
                      <Link href={`/batches/batch${m.batch}`} className="font-bold hover:underline" style={{ color: "var(--accent)" }}>
                        batch{m.batch}
                      </Link>
                    </td>
                    <td className="py-2 pr-4">
                      {m.model.variant.toUpperCase()} · {m.model.pipeline}
                    </td>
                    <td className="py-2 pr-4">{m.started_at.replace("T", " ").slice(0, 16)}</td>
                    <td className="py-2 pr-4">
                      {success}/{failed}/{skipped}
                    </td>
                    <td className="py-2 pr-4">{batchAvg}</td>
                    <td className="py-2 pr-4">{dur}</td>
                    <td className="py-2">{m.ended_at ? "✅ 完成" : "🔄 运行中"}</td>
                  </tr>
                );
              })}
              {manifests.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-6 text-center text-(--muted)">
                    未发现 output_batch*/manifest.json — 先运行 pipeline_auto.py
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>

      <section className="text-xs text-(--muted)">
        数据链路：scripts/pipeline-tools（Python 引擎写 manifest）→ RSC fs 直读（本页）→
        dashboard/data/batches.json（路线A桥，Top10 复用）。路线B Phase 2 将追加：SSE 实时日志（app/api/pipeline/stream）与
        触发运行（app/api/pipeline/run，spawn 白名单 + Bearer Token）。
      </section>
    </div>
  );

  function scoresOf(m: Manifest) {
    return m.records
      .filter((r) => r.status === "SUCCESS")
      .map(displayScore)
      .filter((s) => s.source !== "none")
      .map((s) => s.score);
  }
}
