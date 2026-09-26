/**
 * Skill Gateway — 执行路由
 *
 * POST   /api/v1/execute           — 执行 Skill
 * POST   /api/v1/execute/mcp/list  — 列出 MCP 工具
 * POST   /api/v1/execute/mcp/call  — 调用 MCP 工具
 */
import { Hono } from 'hono';
import '../context.js';
import { skillExecuteSchema, mcpCallSchema } from '../schemas.js';
import type { ApiResponse, SkillExecuteRequest, SkillExecuteResult } from '../types.js';
import type { SkillExecutionContext } from '@yyc3/skill-registry';
import { PayloadTooLargeError } from '../middleware/security.js';

export const executeRoutes = new Hono();

/** 安全解析 JSON body：非法 JSON / null 返回 null，调用方转 400；计数流超限上抛 413 */
async function safeJson(c: { req: { json: () => Promise<unknown> } }): Promise<unknown | null> {
  try {
    const raw = await c.req.json();
    return raw ?? null;
  } catch (err) {
    if (err instanceof PayloadTooLargeError) throw err;
    return null;
  }
}

// POST /api/v1/execute — 执行 Skill
executeRoutes.post('/', async (c) => {
  const registry = c.get('registry');
  const executor = c.get('executor');
  const config = c.get('gatewayConfig');

  const rawBody = await safeJson(c);
  const parsed = skillExecuteSchema.safeParse(rawBody);
  if (!parsed.success) {
    const first = parsed.error.issues[0];
    const resp: ApiResponse = {
      ok: false,
      error: {
        code: 'BAD_REQUEST',
        message: first ? `${first.path.join('.')}: ${first.message}` : 'invalid request body',
        details: parsed.error.issues.map((i) => ({ path: i.path.join('.'), message: i.message })),
      },
    };
    c.status(400);
    return c.json(resp);
  }

  const body = parsed.data as SkillExecuteRequest;

  const skill = registry.get(body.skillId);
  if (!skill) {
    const resp: ApiResponse = {
      ok: false,
      error: { code: 'NOT_FOUND', message: `Skill '${body.skillId}' not found` },
    };
    c.status(404);
    return c.json(resp);
  }

  // timeout：下限 1s，上限 maxTimeout；NaN/0/负数已被 Zod 拒绝，此处仅钳制越界正数
  const timeout = Math.min(Math.max(body.timeout ?? config.defaultTimeout, 1_000), config.maxTimeout);
  const start = Date.now();

  try {
    const ctx: SkillExecutionContext = {
      callId: `gw-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      timeout,
    };
    const output = await executor.execute(body.skillId, body.params, ctx);
    const result: SkillExecuteResult = {
      skillId: body.skillId,
      duration: Date.now() - start,
      output,
      error: output.success ? undefined : (output.error ?? 'Execution failed'),
    };
    const resp: ApiResponse<SkillExecuteResult> = {
      ok: output.success,
      data: result,
      ...(output.success
        ? {}
        : { error: { code: 'EXECUTION_ERROR', message: result.error ?? 'Execution failed' } }),
    };
    if (!output.success) {
      c.status(500);
    }
    return c.json(resp);
  } catch (err) {
    const errorMsg = err instanceof Error ? err.message : 'Execution failed';
    const result: SkillExecuteResult = {
      skillId: body.skillId,
      duration: Date.now() - start,
      output: null,
      error: errorMsg,
    };
    const resp: ApiResponse = { ok: false, data: result, error: { code: 'EXECUTION_ERROR', message: errorMsg } };
    c.status(500);
    return c.json(resp);
  }
});

// POST /api/v1/execute/mcp/list — 列出 MCP 工具
executeRoutes.post('/mcp/list', (c) => {
  const mcpRuntime = c.get('mcpRuntime');
  if (!mcpRuntime) {
    const resp: ApiResponse = {
      ok: false,
      error: { code: 'NOT_AVAILABLE', message: 'MCP Runtime not configured' },
    };
    c.status(503);
    return c.json(resp);
  }
  const tools = mcpRuntime.listAllTools();
  const resp: ApiResponse = { ok: true, data: tools };
  return c.json(resp);
});

// POST /api/v1/execute/mcp/call — 调用 MCP 工具
executeRoutes.post('/mcp/call', async (c) => {
  const mcpRuntime = c.get('mcpRuntime');
  if (!mcpRuntime) {
    const resp: ApiResponse = {
      ok: false,
      error: { code: 'NOT_AVAILABLE', message: 'MCP Runtime not configured' },
    };
    c.status(503);
    return c.json(resp);
  }

  const rawBody = await safeJson(c);
  const parsed = mcpCallSchema.safeParse(rawBody);
  if (!parsed.success) {
    const first = parsed.error.issues[0];
    const resp: ApiResponse = {
      ok: false,
      error: {
        code: 'BAD_REQUEST',
        message: first ? `${first.path.join('.')}: ${first.message}` : 'invalid request body',
        details: parsed.error.issues.map((i) => ({ path: i.path.join('.'), message: i.message })),
      },
    };
    c.status(400);
    return c.json(resp);
  }

  const body = parsed.data as { name: string; args: Record<string, unknown> };

  try {
    const result = await mcpRuntime.callTool(body.name, body.args);
    const resp: ApiResponse = { ok: true, data: result };
    return c.json(resp);
  } catch (err) {
    const resp: ApiResponse = {
      ok: false,
      error: {
        code: 'MCP_ERROR',
        message: err instanceof Error ? err.message : 'MCP call failed',
      },
    };
    c.status(500);
    return c.json(resp);
  }
});