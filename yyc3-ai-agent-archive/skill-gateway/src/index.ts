/**
 * YYC³ Skill Gateway API
 * @module @yyc3/skill-gateway
 *
 * 基于 Hono 构建的 REST API 层，提供 Skill 注册/发现/执行的标准 HTTP 接口。
 *
 * 使用方式:
 * ```ts
 * import { SkillGateway } from '@yyc3/skill-gateway';
 * import { globalSkillRegistry, SkillLoader, SkillExecutor } from '@yyc3/skill-registry';
 *
 * const gateway = new SkillGateway({
 *   registry: globalSkillRegistry,
 *   loader: new SkillLoader(globalSkillRegistry, { rootDir: './skills' }),
 *   executor: new SkillExecutor(globalSkillRegistry),
 * });
 *
 * // 方式 1: 使用内置服务
 * await gateway.start(3030);
 *
 * // 方式 2: 直接使用 Hono app (集成到已有服务)
 * // const app = new Hono().route('/gateway', gateway.app);
 * ```
 */

export { SkillGateway } from './gateway.js';
export type { GatewayDependencies } from './gateway.js';
export { apiKeyAuth, apiKeysFromEnv } from './middleware/auth.js';
export type { AuthConfig } from './middleware/auth.js';
export {
  createRateLimitStore,
  MemoryStore,
  RedisStore,
} from './middleware/rate-limit-store.js';
export type { Bucket, RateLimitStore } from './middleware/rate-limit-store.js';
export { rateLimiter, resolveClientIp, trustedProxyHopsFromEnv } from './middleware/security.js';
export { skillExecuteSchema, mcpCallSchema, skillQuerySchema } from './schemas.js';
export type {
  ApiResponse,
  SkillQueryParams,
  SkillExecuteRequest,
  SkillExecuteResult,
  GatewayConfig,
  HealthResponse,
} from './types.js';