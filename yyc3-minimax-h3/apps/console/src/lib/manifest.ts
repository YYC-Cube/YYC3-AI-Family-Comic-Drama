// @ts-check
// manifest reader - RSC server-side, reads output_batch*\/manifest.json directly.
// Contract: @yyc3/manifest-schema (single source of truth for both ends).
import { batchesPayloadSchema, manifestSchema, type BatchesPayload, type Manifest } from "@yyc3/manifest-schema";
import fs from "node:fs";
import path from "node:path";

/** 仓库根 = console 的上两级（apps/console → 仓库根） */
export const REPO_ROOT = path.resolve(process.cwd(), "..", "..");

/** 读取全部批次 manifest（zod 校验，损坏文件跳过不阻断） */
export function readManifests(): { manifests: Manifest[]; errors: string[] } {
  const errors: string[] = [];
  const manifests: Manifest[] = [];
  const root = REPO_ROOT;
  let dirs: string[] = [];
  try {
    dirs = fs
      .readdirSync(root)
      .filter((d) => /^output_batch/.test(d))
      .sort();
  } catch {
    return { manifests, errors: ["仓库根不可读"] };
  }
  for (const d of dirs) {
    const file = path.join(root, d, "manifest.json");
    if (!fs.existsSync(file)) continue;
    try {
      const raw = JSON.parse(fs.readFileSync(file, "utf-8"));
      const parsed = manifestSchema.safeParse(raw);
      if (parsed.success) manifests.push(parsed.data);
      else errors.push(`${d}: schema 校验失败 ${parsed.error.issues[0]?.message ?? ""}`);
    } catch (e) {
      errors.push(`${d}: ${String(e)}`);
    }
  }
  return { manifests, errors };
}

/** 读取路线A数据桥的聚合产物（若存在），供趋势图直接使用 */
export function readBatchesPayload(): BatchesPayload | null {
  const file = path.join(REPO_ROOT, "dashboard", "data", "batches.json");
  if (!fs.existsSync(file)) return null;
  try {
    const parsed = batchesPayloadSchema.safeParse(JSON.parse(fs.readFileSync(file, "utf-8")));
    return parsed.success ? parsed.data : null;
  } catch {
    return null;
  }
}

/** 0-10 展示分：human 优先，回退 lipsync score_norm×10 */
export function displayScore(rec: Manifest["records"][number]): { score: number; source: "human" | "lipsync" | "none" } {
  if (rec.human?.score != null) return { score: rec.human.score, source: "human" };
  if (rec.lipsync?.score_norm != null) return { score: Math.round(rec.lipsync.score_norm * 100) / 10, source: "lipsync" };
  return { score: 0, source: "none" };
}
