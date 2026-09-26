// /api/pipeline/run - trigger pipeline via whitelisted spawn (POST) or query status (GET).
// Auth: Bearer token (PIPELINE_TOKEN) OR loopback peers. Rate/lock: single-flight in manager.
import { NextRequest, NextResponse } from "next/server";
import { pipelineManager } from "@/lib/pipeline-manager";

export const dynamic = "force-dynamic";

function authorize(req: NextRequest): boolean {
  const token = process.env.PIPELINE_TOKEN;
  if (token && req.headers.get("authorization") === `Bearer ${token}`) return true;
  // 本机/局域网运维便利：回环地址放行（Bearer 未配置时）
  const isLoopback = ["127.0.0.1", "::1", "::ffff:127.0.0.1"].includes(
    req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ?? ""
  );
  return !token && isLoopback;
}

export async function GET(req: NextRequest) {
  if (!authorize(req)) return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  return NextResponse.json(pipelineManager.getStatus());
}

export async function POST(req: NextRequest) {
  if (!authorize(req)) return NextResponse.json({ error: "unauthorized" }, { status: 401 });

  let body: { batch?: string | null; dryRun?: boolean } = {};
  try {
    body = await req.json();
  } catch {
    // 空 body 允许：批次自动递增
  }

  const result = pipelineManager.start(body.batch ?? null, body.dryRun === true);
  if (!result.ok) return NextResponse.json({ error: result.error }, { status: 409 });
  return NextResponse.json({ started: true, batch: result.batch, status: pipelineManager.getStatus() });
}
