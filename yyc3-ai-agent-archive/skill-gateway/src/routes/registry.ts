/**
 * Skill Gateway — MCP Registry 聚合路由（Task G1-4）
 *
 * GET /api/v1/registry               — 原样输出 registry.json（MCP 生态直接消费）
 * GET /api/v1/registry/servers       — 聚合 server 列表（ApiResponse 包装）
 * GET /api/v1/registry/servers/:slug — 按 slug 查询单个 server
 *
 * 数据源为 `yyc3-cli skills export-mcp` 的静态导出产物（单一事实源），
 * 按 mtime 缓存，文件更新自动失效。
 */
import { Hono } from 'hono';
import '../context.js';
import type { ApiResponse } from '../types.js';

/** MCP Registry server.json 条目（官方 schema 子集） */
export interface McpServerEntry {
  $schema: string;
  name: string;
  title?: string;
  description?: string;
  version?: string;
  _meta?: Record<string, unknown>;
}

interface RegistryFile {
  $schema: string;
  servers: McpServerEntry[];
}

const NAMESPACE = 'io.github.yyc-cube';

interface Cache {
  path: string;
  mtime: number;
  data: RegistryFile;
}
let cache: Cache | null = null;

/** registry.json 候选路径：环境变量 → 仓库根（相对本文件回溯 4 级）→ cwd */
function registryPathCandidates(): string[] {
  const candidates: string[] = [];
  if (process.env.YYC3_REGISTRY_FILE) candidates.push(process.env.YYC3_REGISTRY_FILE);
  candidates.push(new URL('../../../../public/registry/registry.json', import.meta.url).pathname);
  candidates.push('public/registry/registry.json');
  return candidates;
}

async function loadRegistry(): Promise<RegistryFile | null> {
  for (const p of registryPathCandidates()) {
    try {
      const fs = await import('node:fs/promises');
      const st = await fs.stat(p);
      if (cache && cache.path === p && cache.mtime === st.mtimeMs) return cache.data;
      const data = JSON.parse(await fs.readFile(p, 'utf-8')) as RegistryFile;
      cache = { path: p, mtime: st.mtimeMs, data };
      return data;
    } catch {
      // 候选路径不存在或损坏 → 尝试下一个
    }
  }
  return null;
}

function notExported(c: { status(code: number): void; json(body: unknown): Response }): Response {
  c.status(404);
  return c.json({
    ok: false,
    error: {
      code: 'REGISTRY_NOT_EXPORTED',
      message: 'registry.json 不存在，请先运行 `yyc3-cli skills export-mcp`',
    },
  });
}

export const registryRoutes = new Hono();

// GET /api/v1/registry — 原样透传 registry.json
registryRoutes.get('/', async (c) => {
  const reg = await loadRegistry();
  if (!reg) return notExported(c);
  return c.json(reg);
});

// GET /api/v1/registry/servers — 聚合列表
registryRoutes.get('/servers', async (c) => {
  const reg = await loadRegistry();
  if (!reg) return notExported(c);
  const q = c.req.query('q')?.toLowerCase();
  const servers = q
    ? reg.servers.filter(
      (s) =>
        s.name.toLowerCase().includes(q) ||
        (s.title ?? '').toLowerCase().includes(q) ||
        (s.description ?? '').toLowerCase().includes(q)
    )
    : reg.servers;
  const body: ApiResponse<McpServerEntry[]> = {
    ok: true,
    data: servers,
    meta: { total: servers.length, timestamp: new Date().toISOString() },
  };
  return c.json(body);
});

// GET /api/v1/registry/servers/:slug — 单个查询（slug 或完整 name）
registryRoutes.get('/servers/:slug', async (c) => {
  const reg = await loadRegistry();
  if (!reg) return notExported(c);
  const raw = c.req.param('slug');
  const full = raw.includes('/') ? raw : `${NAMESPACE}/${raw}`;
  const found = reg.servers.find((s) => s.name === full);
  if (!found) {
    c.status(404);
    return c.json({
      ok: false,
      error: { code: 'SERVER_NOT_FOUND', message: `未找到 server: ${full}` },
    });
  }
  const body: ApiResponse<McpServerEntry> = { ok: true, data: found };
  return c.json(body);
});
