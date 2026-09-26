/**
 * Skill Gateway API — 类型定义
 * @module @yyc3/skill-gateway
 */

import type { SkillSearchOptions, SkillRegistryStats } from '@yyc3/skill-registry';

/** API 统一响应格式 */
export interface ApiResponse<T = unknown> {
  ok: boolean;
  data?: T;
  error?: { code: string; message: string; details?: unknown };
  meta?: { page?: number; pageSize?: number; total?: number; timestamp: string };
}

/** 技能查询参数 */
export interface SkillQueryParams {
  q?: string;
  domain?: string;
  type?: string;
  runtime?: string;
  status?: string;
  page?: number;
  pageSize?: number;
}

/** 技能执行请求 */
export interface SkillExecuteRequest {
  skillId: string;
  params: Record<string, unknown>;
  timeout?: number;
}

/** 技能执行结果 */
export interface SkillExecuteResult {
  skillId: string;
  duration: number;
  output: unknown;
  error?: string;
}

/** Gateway 配置 */
export interface GatewayConfig {
  port?: number;
  host?: string;
  skillsRootDir?: string;
  maxSkillsDepth?: number;
  defaultTimeout?: number;
  maxTimeout?: number;
  corsOrigins?: string[];
  /** API Key 列表（认证层）；未提供时回退读取 YYC3_API_KEYS 环境变量 */
  apiKeys?: string[];
  /** 认证保护模式：'write'（默认，保护非 GET）/ 'all'（保护 /api/v1 全部） */
  authMode?: 'write' | 'all';
  /**
   * 受信代理跳数：>0 时限流从 XFF 链倒数第 N 跳取真实客户端 IP；
   * 0（默认）不信任 XFF。环境变量 `YYC3_TRUSTED_PROXY_HOPS` 可覆盖。
   * 部署在反向代理（Nginx/CDN）之后时必须设置为实际代理层数。
   */
  trustedProxyHops?: number;
}

/** 健康检查响应 */
export interface HealthResponse {
  status: 'ok' | 'degraded' | 'down';
  uptime: number;
  version: string;
  skills: {
    total: number;
    byDomain: Record<string, number>;
    byType: Record<string, number>;
  };
}