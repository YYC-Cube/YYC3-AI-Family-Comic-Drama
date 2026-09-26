/**
 * Gateway HTTP 边界 Zod Schema（P2-2：入参统一校验，非法 JSON→400）
 */
import { z } from 'zod';

/** 技能执行请求体 */
export const skillExecuteSchema = z.object({
  skillId: z.string().min(1, 'skillId is required'),
  params: z.record(z.string(), z.unknown()).default({}),
  timeout: z.number().int().positive().optional(),
});

/** MCP 工具调用请求体 */
export const mcpCallSchema = z.object({
  name: z.string().min(1, 'name is required'),
  args: z.record(z.string(), z.unknown()).default({}),
});

/** 技能列表查询参数 */
export const skillQuerySchema = z.object({
  q: z.string().optional(),
  domain: z.string().optional(),
  type: z.string().optional(),
  runtime: z.string().optional(),
  status: z.string().optional(),
  page: z.coerce.number().int().positive().optional().catch(1),
  pageSize: z.coerce.number().int().min(1).max(100).optional().catch(20),
});
