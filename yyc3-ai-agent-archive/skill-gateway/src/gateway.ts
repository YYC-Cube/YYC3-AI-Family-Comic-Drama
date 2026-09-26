/**
 * Skill Gateway — 核心应用类
 *
 * 基于 Hono 构建 REST API，封装 Skill 注册/发现/执行能力
 * 支持 Bun / Node / Deno 多运行时
 */
import type { UnifiedMCPRuntime } from '@yyc3/mcp-runtime';
import type {
  SkillExecutor,
  SkillLoader,
  SkillRegistry,
} from '@yyc3/skill-registry';
import { Hono } from 'hono';
import { cors } from 'hono/cors';
import './context.js';
import { apiKeyAuth, apiKeysFromEnv } from './middleware/auth.js';
import { errorHandler } from './middleware/error-handler.js';
import { logger } from './middleware/logger.js';
import { bodySizeLimit, rateLimiter, securityHeaders, trustedProxyHopsFromEnv } from './middleware/security.js';
import { executeRoutes } from './routes/execute.js';
import { healthRoutes } from './routes/health.js';
import { registryRoutes } from './routes/registry.js';
import { skillsRoutes } from './routes/skills.js';
import type { GatewayConfig } from './types.js';

export interface GatewayDependencies {
  registry: SkillRegistry;
  loader: SkillLoader;
  executor: SkillExecutor;
  mcpRuntime?: UnifiedMCPRuntime;
}

const DEFAULT_CONFIG: Required<GatewayConfig> = {
  port: 3030,
  host: '0.0.0.0',
  skillsRootDir: './skills',
  maxSkillsDepth: 3,
  defaultTimeout: 30_000,
  maxTimeout: 120_000,
  corsOrigins: ['*'],
  apiKeys: [],
  authMode: 'write',
  trustedProxyHops: 0,
};

export class SkillGateway {
  readonly app: Hono;
  readonly config: Required<GatewayConfig>;
  readonly deps: GatewayDependencies;
  private startedAt: number = 0;

  constructor(deps: GatewayDependencies, config: GatewayConfig = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    // apiKeys 未显式提供时回退环境变量
    if (!config.apiKeys) {
      this.config.apiKeys = apiKeysFromEnv(process.env.YYC3_API_KEYS);
    }
    // trustedProxyHops 未显式提供时回退环境变量
    if (config.trustedProxyHops === undefined) {
      this.config.trustedProxyHops = trustedProxyHopsFromEnv(process.env.YYC3_TRUSTED_PROXY_HOPS);
    }
    // corsOrigins 未显式提供时回退环境变量（P2 收敛：逗号分隔显式白名单；
    // 未配置保持 '*' 兼容存量部署 — API Key 头部认证下 '*' 不携带凭据，风险受控）
    if (!config.corsOrigins) {
      const raw = process.env.YYC3_CORS_ORIGINS;
      this.config.corsOrigins = raw
        ? raw.split(',').map((s) => s.trim()).filter(Boolean)
        : ['*'];
    }
    this.deps = deps;
    this.app = this.createApp();
  }

  private createApp(): Hono {
    const app = new Hono();

    app.use('*', cors({ origin: this.config.corsOrigins }));
    app.use('*', securityHeaders());
    app.use('*', bodySizeLimit(1024 * 1024)); // 1MB
    const limiter = rateLimiter({
      windowMs: 60_000,
      maxRequests: 100,
      trustedProxyHops: this.config.trustedProxyHops,
    });
    app.use('*', limiter);
    app.use('*', logger());
    app.use(
      '*',
      apiKeyAuth({
        apiKeys: this.config.apiKeys,
        // 'all' 模式下 GET 发现类端点也纳入保护
        protectedPrefixes: this.config.authMode === 'all' ? ['/api/v1'] : [],
      })
    );
    app.onError(errorHandler());

    app.use('*', async (c, next) => {
      c.set('registry', this.deps.registry);
      c.set('loader', this.deps.loader);
      c.set('executor', this.deps.executor);
      c.set('mcpRuntime', this.deps.mcpRuntime);
      c.set('gateway', this);
      c.set('gatewayConfig', this.config);
      await next();
    });

    app.route('/api/v1/skills', skillsRoutes);
    app.route('/api/v1/execute', executeRoutes);
    app.route('/api/v1/health', healthRoutes);
    app.route('/api/v1/registry', registryRoutes);

    return app;
  }

  async initialize(): Promise<void> {
    this.deps.loader.load();
    this.startedAt = Date.now();
  }

  async start(port?: number): Promise<void> {
    await this.initialize();
    const p = port ?? this.config.port;
    console.warn(`[SkillGateway] 启动于 http://${this.config.host}:${p}`);

    try {
      const { serve } = await import('@hono/node-server');
      serve({ fetch: this.app.fetch, port: p, hostname: this.config.host });
    } catch {
      // @hono/node-server 不可用时，仅输出提示
      console.warn('[SkillGateway] 请手动启动服务: app.fetch 可直接作为 HTTP handler 使用');
    }
  }

  getUptime(): number {
    return this.startedAt ? Date.now() - this.startedAt : 0;
  }
}
