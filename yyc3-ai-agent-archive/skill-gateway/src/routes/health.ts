/**
 * Skill Gateway — 健康检查 & 服务信息路由
 *
 * GET /api/v1/health          — 健康检查
 * GET /api/v1/health/ready    — 就绪检查
 * GET /api/v1/health/version  — 版本信息
 */
import { Hono } from 'hono';
import '../context.js';
import type { ApiResponse, HealthResponse } from '../types.js';

export const healthRoutes = new Hono();

// GET /api/v1/health — 健康检查
healthRoutes.get('/', (c) => {
  const registry = c.get('registry');
  const gateway = c.get('gateway');
  const stats = registry.getStats();

  const uptime = gateway?.getUptime() ?? 0;
  const body: ApiResponse<HealthResponse> = {
    ok: true,
    data: {
      status: 'ok',
      uptime,
      version: '1.0.0',
      skills: {
        total: stats.totalSkills,
        byDomain: stats.byDomain as Record<string, number>,
        byType: stats.byType as Record<string, number>,
      },
    },
  };
  return c.json(body);
});

// GET /api/v1/health/ready — 就绪检查
healthRoutes.get('/ready', (c) => {
  const registry = c.get('registry');
  try {
    registry.getStats();
    const body: ApiResponse = { ok: true, data: { ready: true } };
    return c.json(body);
  } catch {
    const body: ApiResponse = { ok: false, error: { code: 'NOT_READY', message: 'Registry not ready' } };
    c.status(503);
    return c.json(body);
  }
});

// GET /api/v1/health/version — 版本信息
healthRoutes.get('/version', (c) => {
  const body: ApiResponse = {
    ok: true,
    data: { version: '1.0.0', node: process.version, platform: process.platform },
  };
  return c.json(body);
});
