// /batches/[id] - batch detail: video grid + human refinement drawer (RSC reads manifest,
// client drawer POSTs /api/score). Route: /batches/batch01 → id = "01".
import { readManifests, displayScore } from "@/lib/manifest";
import Link from "next/link";
import RefineDrawer from "./refine-drawer";

export const dynamic = "force-dynamic";

export default async function BatchDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id: raw } = await params;
  const batch = raw.replace(/^batch/i, "").padStart(2, "0");
  const { manifests } = readManifests();
  const manifest = manifests.find((m) => m.batch === batch);

  if (!manifest) {
    return (
      <div className="space-y-4">
        <Link href="/" className="text-sm text-(--muted) hover:text-(--foreground)">← 返回仪表盘</Link>
        <div className="card text-(--muted)">未找到 batch{batch} 的 manifest.json</div>
      </div>
    );
  }

  const success = manifest.records.filter((r) => r.status === "SUCCESS");

  return (
    <div className="space-y-5">
      <Link href="/" className="text-sm text-(--muted) hover:text-(--foreground)">← 返回仪表盘</Link>
      <div className="flex items-baseline gap-4">
        <h1 className="text-xl font-bold">batch{batch} 批次详情</h1>
        <span className="mono text-sm text-(--muted)">
          {manifest.model.variant.toUpperCase()} · {success.length}/{manifest.records.length} 成功 ·
          {manifest.started_at.replace("T", " ").slice(0, 16)} 启动
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {success.map((r) => {
          const { score, source } = displayScore(r);
          return (
            <div key={`${r.ref_img}-${r.seed}`} className="card space-y-2">
              <div className="flex items-center justify-between">
                <span className="mono text-sm font-bold" style={{ color: "var(--accent)" }}>seed {r.seed}</span>
                <span className="mono text-sm">
                  {score > 0 ? `${score}/10` : "待精评"}
                  <span className="text-(--muted) text-xs ml-1">{source === "lipsync" ? "自动" : source === "human" ? "人工" : ""}</span>
                </span>
              </div>
              <div className="mono text-xs text-(--muted)">{r.ref_img}</div>
              <div className="mono text-xs text-(--muted)">
                {r.gen_seconds ? `${r.gen_seconds.toFixed(0)}s` : "-"} · {r.peak_rss_gb ? `${r.peak_rss_gb.toFixed(1)}GB` : "-"}
                {r.lipsync?.av_offset != null ? ` · offset ${r.lipsync.av_offset.toFixed(3)}` : ""}
              </div>
              <div className="mono text-[10px] break-all text-(--muted) opacity-70">{r.video_path}</div>
              <RefineDrawer batch={batch} refImg={r.ref_img} seed={r.seed} initialScore={r.human?.score ?? null} initialTags={r.human?.tags ?? ""} />
            </div>
          );
        })}
      </div>
    </div>
  );
}
