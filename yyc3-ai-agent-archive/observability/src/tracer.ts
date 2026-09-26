/**
 * Observability — 链路追踪器
 *
 * 支持 Span 创建、父子关系、事件记录、采样控制、OTLP HTTP 导出。
 * 遵循 OpenTelemetry 语义约定（W3C Trace Context 兼容的 traceId/spanId 长度）。
 *
 * 修正点（P1-6）：
 * - Span/Trace ID 使用 crypto.randomBytes（traceId 16B / spanId 8B，hex 编码），
 *   替代 Math.random() 生成的低熵 ID；
 * - 父 Span 缺失（跨服务传播）时保留 parentId 字段，并可通过 traceId 参数继承
 *   上游 traceId，避免断链；
 * - 新增 OTLP HTTP exporter：endSpan 时按 OTEL_EXPORTER_OTLP_ENDPOINT 自动上报
 *   （未配置端点则禁用，零开销）。
 */
import { randomBytes } from 'node:crypto';
import type { Span, SpanEvent, SpanExporter, TracerConfig } from './types.js';

const DEFAULT_CONFIG: TracerConfig = {
  sampleRate: 1.0,
  enabled: true,
};

export class Tracer {
  readonly config: TracerConfig;
  private spans = new Map<string, Span>();
  private activeSpans = new Map<string, Span>();
  private exporter: SpanExporter | null;

  constructor(config: Partial<TracerConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.exporter = this.config.exporter ?? createOtlpExporterFromEnv();
  }

  /**
   * 开始一个新的 Span
   *
   * @param name     span 名称
   * @param parentId 父 span ID（跨服务传播时可能不在本地 spans 中）
   * @param tags     标签
   * @param traceId  上游 traceId（跨服务上下文继承，可选）；未提供且父 span 存在时
   *                 继承父 traceId；父 span 不存在时生成新 traceId，但保留 parentId。
   */
  startSpan(
    name: string,
    parentId?: string,
    tags?: Record<string, string>,
    traceId?: string,
  ): Span {
    if (!this.config.enabled) {
      return { id: '', traceId: '', name, startTime: 0, status: 'ok' };
    }

    // 采样判定
    if (Math.random() > this.config.sampleRate) {
      return { id: '', traceId: '', name, startTime: 0, status: 'ok' };
    }

    const tid = traceId
      ?? (parentId ? this.spans.get(parentId)?.traceId : undefined)
      ?? this.generateId('trace');

    const span: Span = {
      id: this.generateId('span'),
      traceId: tid,
      parentId,
      name,
      startTime: Date.now(),
      status: 'ok',
      tags,
      events: [],
    };

    this.spans.set(span.id, span);
    this.activeSpans.set(span.id, span);
    return span;
  }

  /** 结束 Span，并触发 exporter 上报（若已配置） */
  endSpan(spanId: string, status: Span['status'] = 'ok'): Span | undefined {
    const span = this.spans.get(spanId);
    if (!span) return undefined;

    span.endTime = Date.now();
    span.status = status;
    this.activeSpans.delete(spanId);

    if (this.exporter) {
      // 异步上报，不阻塞调用方；失败静默（仅 debug 模式记一条 warn）
      Promise.resolve(this.exporter.export(span)).catch((e) => {
        if (this.config.debug) {
          console.warn('[Tracer] exporter error:', e);
        }
      });
    }
    return span;
  }

  /** 添加事件到 Span */
  addEvent(spanId: string, name: string, attributes?: Record<string, string>): void {
    const span = this.spans.get(spanId);
    if (!span) return;

    const event: SpanEvent = {
      name,
      timestamp: Date.now(),
      attributes,
    };
    span.events = span.events ?? [];
    span.events.push(event);
  }

  /** 获取 Span */
  getSpan(spanId: string): Span | undefined {
    return this.spans.get(spanId);
  }

  /** 按 traceId 获取所有 Span */
  getTrace(traceId: string): Span[] {
    return Array.from(this.spans.values()).filter(s => s.traceId === traceId);
  }

  /** 获取所有 Span 的树形结构 */
  getTraceTree(traceId: string): Record<string, unknown> {
    const spans = this.getTrace(traceId);
    const root = spans.find(s => !s.parentId);
    if (!root) return {};

    const buildTree = (span: Span): Record<string, unknown> => {
      const children = spans
        .filter(s => s.parentId === span.id)
        .map(buildTree);
      return {
        id: span.id,
        name: span.name,
        status: span.status,
        duration: (span.endTime ?? Date.now()) - span.startTime,
        children: children.length > 0 ? children : undefined,
      };
    };
    return buildTree(root);
  }

  /** 获取活跃 Span */
  getActiveSpans(): Span[] {
    return Array.from(this.activeSpans.values());
  }

  /** 清空 */
  clear(): void {
    this.spans.clear();
    this.activeSpans.clear();
  }

  /** 注入自定义 exporter（测试/定制用） */
  setExporter(exporter: SpanExporter | null): void {
    this.exporter = exporter;
  }

  /**
   * 生成 ID：traceId = 16 字节 hex（32 字符），spanId = 8 字节 hex（16 字符）。
   * 与 W3C Trace Context / OTLP 长度对齐。
   */
  private generateId(kind: 'trace' | 'span'): string {
    return randomBytes(kind === 'trace' ? 16 : 8).toString('hex');
  }
}

// ============================================================
// OTLP HTTP Exporter（最小可用实现，env 控制）
// ============================================================

/** OTLP JSON 的 Span 数据结构（OTLP/v1/traces 子集） */
interface OtlpResourceSpan {
  resource: { attributes: Array<{ key: string; value: { stringValue: string } }> };
  scopeSpans: Array<{
    scope: { name: string };
    spans: Array<{
      traceId: string;
      spanId: string;
      parentSpanId?: string;
      name: string;
      startTimeUnixNano: string;
      endTimeUnixNano: string;
      status: { code: number; message?: string };
      attributes?: Array<{ key: string; value: { stringValue: string } }>;
      events?: Array<{
        name: string;
        timeUnixNano: string;
        attributes?: Array<{ key: string; value: { stringValue: string } }>;
      }>;
    }>;
  }>;
}

/**
 * 从环境变量创建 OTLP HTTP exporter。
 *
 * 读取 `OTEL_EXPORTER_OTLP_ENDPOINT`（如 `http://localhost:4318`）；
 * 未设置或为空时返回 null（禁用导出，零开销）。
 * 端点路径按 OTLP 规范自动补 `/v1/traces`。
 */
export function createOtlpExporterFromEnv(endpoint?: string): SpanExporter | null {
  const ep = (endpoint ?? process.env.OTEL_EXPORTER_OTLP_ENDPOINT ?? '').trim();
  if (!ep) return null;

  const url = ep.endsWith('/v1/traces') ? ep : `${ep.replace(/\/$/, '')}/v1/traces`;
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  const apiKey = process.env.OTEL_EXPORTER_OTLP_HEADERS;
  if (apiKey) {
    for (const part of apiKey.split(',')) {
      const eq = part.indexOf('=');
      if (eq > 0) headers[part.slice(0, eq).trim()] = part.slice(eq + 1).trim();
    }
  }

  return {
    async export(span: Span): Promise<void> {
      const body = toOtlpPayload(span);
      const res = await fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        throw new Error(`OTLP export failed: ${res.status}`);
      }
    },
  };
}

/** 将内部 Span 转为 OTLP/v1/traces JSON 负载 */
function toOtlpPayload(span: Span): { resourceSpans: OtlpResourceSpan[] } {
  const msToNs = (ms: number) => String(ms * 1_000_000);
  const code = span.status === 'error' ? 2 : 1; // OTLP StatusCode: 1=OK, 2=ERROR
  const attrs = span.tags
    ? Object.entries(span.tags).map(([key, value]) => ({ key, value: { stringValue: String(value) } }))
    : undefined;
  const events = span.events?.map((e) => ({
    name: e.name,
    timeUnixNano: msToNs(e.timestamp),
    attributes: e.attributes
      ? Object.entries(e.attributes).map(([k, v]) => ({ key: k, value: { stringValue: String(v) } }))
      : undefined,
  }));

  return {
    resourceSpans: [
      {
        resource: {
          attributes: [{ key: 'service.name', value: { stringValue: process.env.SERVICE_NAME ?? 'yyc3' } }],
        },
        scopeSpans: [
          {
            scope: { name: '@yyc3/observability' },
            spans: [
              {
                traceId: span.traceId,
                spanId: span.id,
                parentSpanId: span.parentId,
                name: span.name,
                startTimeUnixNano: msToNs(span.startTime),
                endTimeUnixNano: msToNs(span.endTime ?? Date.now()),
                status: { code },
                attributes: attrs,
                events,
              },
            ],
          },
        ],
      },
    ],
  };
}
