// /api/score - human refinement write-back (pipeline step ③ web form endpoint).
// Parses report_batchXX.md pipe-table rows, matches by ref image + seed,
// updates 评分(1~10) and 缺陷标签 columns in place, then refreshes dashboard data bridge.
import { pipelineManager } from "@/lib/pipeline-manager";
import { NextRequest, NextResponse } from "next/server";
import { execFile } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

export const dynamic = "force-dynamic";

const REPO_ROOT = path.resolve(process.cwd(), "..", "..");

interface ScoreBody {
  batch: string; // e.g. "01"
  ref: string; // e.g. "person_a.png"
  seed: number;
  score: number; // 1~10
  tags?: string; // comma separated defect labels
}

function reportPath(batch: string) {
  return path.join(REPO_ROOT, `report_batch${batch}.md`);
}

/** 校验批次存在且行定位唯一 */
function findRowIndex(lines: string[], ref: string, seed: number): number {
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (!line.startsWith("|") || line.includes("---")) continue;
    const cells = line.split("|").map((c) => c.trim());
    // cells: ['', 参考图, Seed, 状态, 视频路径, 时间, 口型分, 评分, 缺陷标签, '']
    if (cells.length < 9) continue;
    if (cells[1] === ref && cells[2] === String(seed)) return i;
  }
  return -1;
}

export async function POST(req: NextRequest) {
  let body: ScoreBody;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "invalid json" }, { status: 400 });
  }

  const { batch, ref, seed, score, tags = "" } = body ?? {};
  if (!/^\d{2}$/.test(batch ?? "")) return NextResponse.json({ error: "batch 须为两位数字" }, { status: 400 });
  if (!ref || typeof seed !== "number") return NextResponse.json({ error: "ref/seed 必填" }, { status: 400 });
  if (!(score >= 1 && score <= 10)) return NextResponse.json({ error: "score 须在 1~10" }, { status: 400 });

  const file = reportPath(batch);
  if (!fs.existsSync(file)) return NextResponse.json({ error: `report 不存在: ${path.basename(file)}` }, { status: 404 });

  const content = fs.readFileSync(file, "utf-8");
  const lines = content.split("\n");
  const idx = findRowIndex(lines, ref, seed);
  if (idx === -1) return NextResponse.json({ error: `未找到行: ${ref} / seed ${seed}` }, { status: 404 });

  const cells = lines[idx].split("|").map((c) => c.trim());
  cells[7] = String(score); // 评分(1~10)
  cells[8] = tags; // 缺陷标签
  lines[idx] = `| ${cells.slice(1, 9).join(" | ")} |`;
  fs.writeFileSync(file, lines.join("\n"), "utf-8");

  // 写回后刷新数据桥（静默，不阻断精评响应）
  const exportScript = path.join(REPO_ROOT, "scripts", "pipeline-tools", "export_dashboard_data.py");
  if (fs.existsSync(exportScript) && !pipelineManager.isRunning()) {
    execFile(process.env.PIPELINE_PYTHON ?? "python3", [exportScript], { cwd: REPO_ROOT }, () => { });
  }

  return NextResponse.json({ ok: true, batch, ref, seed, score, tags });
}

/** GET: 读取某批次全部行的当前精评状态（表单初始值） */
export async function GET(req: NextRequest) {
  const batch = new URL(req.url).searchParams.get("batch") ?? "";
  if (!/^\d{2}$/.test(batch)) return NextResponse.json({ error: "batch 须为两位数字" }, { status: 400 });
  const file = reportPath(batch);
  if (!fs.existsSync(file)) return NextResponse.json({ error: "report 不存在" }, { status: 404 });

  const rows: { ref: string; seed: number; status: string; video: string; lipsync: string; score: string; tags: string }[] = [];
  for (const line of fs.readFileSync(file, "utf-8").split("\n")) {
    if (!line.startsWith("|") || line.includes("---")) continue;
    const cells = line.split("|").map((c) => c.trim());
    if (cells.length < 9 || cells[1] === "参考图") continue;
    rows.push({ ref: cells[1], seed: Number(cells[2]), status: cells[3], video: cells[4], lipsync: cells[6], score: cells[7], tags: cells[8] });
  }
  return NextResponse.json({ batch, rows });
}
