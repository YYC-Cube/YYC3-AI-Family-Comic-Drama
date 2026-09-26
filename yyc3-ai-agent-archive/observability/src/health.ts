/**
 * Observability — 健康检查器
 *
 * 支持多组件健康状态聚合，提供整体健康评估
 */
import type { HealthChecker, HealthCheckResult, HealthStatus } from './types.js';

export class HealthRegistry {
  private checkers = new Map<string, HealthChecker>();
  private results = new Map<string, HealthCheckResult>();

  /** 注册健康检查器 */
  register(checker: HealthChecker): void {
    if (this.checkers.has(checker.name)) {
      throw new Error(`Health checker "${checker.name}" already registered`);
    }
    this.checkers.set(checker.name, checker);
  }

  /** 注销健康检查器 */
  unregister(name: string): boolean {
    this.results.delete(name);
    return this.checkers.delete(name);
  }

  /** 执行所有健康检查 */
  async runAll(): Promise<Map<string, HealthCheckResult>> {
    const checks = Array.from(this.checkers.values()).map(async (checker) => {
      const start = Date.now();
      try {
        const result = await checker.check();
        const full: HealthCheckResult = {
          ...result,
          latency: Date.now() - start,
          timestamp: new Date().toISOString(),
        };
        this.results.set(checker.name, full);
        return [checker.name, full] as const;
      } catch (err) {
        const full: HealthCheckResult = {
          component: checker.name,
          status: 'unhealthy',
          message: err instanceof Error ? err.message : String(err),
          latency: Date.now() - start,
          timestamp: new Date().toISOString(),
        };
        this.results.set(checker.name, full);
        return [checker.name, full] as const;
      }
    });

    const entries = await Promise.all(checks);
    return new Map(entries);
  }

  /** 获取整体健康状态 */
  getOverallStatus(): HealthStatus {
    if (this.results.size === 0) return 'healthy';
    const statuses = Array.from(this.results.values()).map(r => r.status);
    if (statuses.some(s => s === 'unhealthy')) return 'unhealthy';
    if (statuses.some(s => s === 'degraded')) return 'degraded';
    return 'healthy';
  }

  /** 获取所有结果 */
  getResults(): HealthCheckResult[] {
    return Array.from(this.results.values());
  }

  /** 获取单个组件结果 */
  getResult(name: string): HealthCheckResult | undefined {
    return this.results.get(name);
  }

  /** 清空 */
  clear(): void {
    this.results.clear();
    this.checkers.clear();
  }
}