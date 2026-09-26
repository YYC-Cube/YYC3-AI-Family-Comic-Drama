/**
 * Skill Gateway — 错误处理中间件
 */
import type { ErrorHandler } from 'hono';
import type { ApiResponse } from '../types.js';
import { PayloadTooLargeError } from './security.js';

export function errorHandler(): ErrorHandler {
  return (err, c) => {
    // chunked 计数流超限：映射为 413（而非 500）
    if (err instanceof PayloadTooLargeError) {
      const body: ApiResponse = {
        ok: false,
        error: { code: 'PAYLOAD_TOO_LARGE', message: err.message },
      };
      return c.json(body, 413);
    }

    const message = err instanceof Error ? err.message : 'Internal Server Error';
    console.error(`[Gateway] Error: ${message}`, err);
    const body: ApiResponse = {
      ok: false,
      error: { code: 'INTERNAL_ERROR', message },
    };
    return c.json(body, 500);
  };
}
