/**
 * Observability — 指标收集器
 *
 * 支持 Counter（计数器）、Gauge（仪表盘）、Histogram（直方图）
 * 提供指标注册、快照导出、Prometheus 格式输出。
 *
 * 语义对齐 Prometheus：
 * - Histogram 分桶为**累计**桶（le=X 包含所有 ≤ X 的观测值）；
 * - 导出包含 `_bucket{le="..."}`、`_sum`、`_count`；
 * - Labels 参与分区：同一指标不同标签值为不同时间序列，Prometheus
 *   输出以 `name{k1="v1",k2="v2"}` 形式渲染。
 */
import type { Labels, MetricDef, MetricSnapshot } from './types.js';

/** 将标签对象序列化为分区键（稳定排序，避免 Map 顺序差异） */
function labelKey(labels?: Labels): string {
  if (!labels) return '';
  const entries = Object.entries(labels).sort((a, b) => a[0].localeCompare(b[0]));
  return entries.map(([k, v]) => `${k}=${v}`).join(',');
}

/** 转为 Prometheus 标签选择器字符串，如 `env="prod",region="cn"` */
function labelSelector(labels?: Labels): string {
  if (!labels) return '';
  const entries = Object.entries(labels).sort((a, b) => a[0].localeCompare(b[0]));
  return entries.map(([k, v]) => `${k}="${v}"`).join(',');
}

interface HistogramPartition {
  buckets: Map<number, number>;
  count: number;
  sum: number;
}

interface MetricValue {
  def: MetricDef;
  /** 各标签分区的值（counter/gauge 用） */
  partitions: Map<string, number>;
  /** 各标签分区的直方图状态（histogram 用） */
  histPartitions?: Map<string, HistogramPartition>;
  /** 桶上界（升序），仅 histogram */
  bucketBounds?: number[];
  /** 单指标最大分区（序列）数：防高基数标签无界增长（P2） */
  maxSeries?: number;
  /** 序列超限告警是否已发（每指标一次，避免日志洪水） */
  seriesWarned?: boolean;
}

/** 写入分区：新序列超限时丢弃并告警一次（既有序列不受影响） */
function putSeries<T>(m: MetricValue, map: Map<string, T>, key: string, make: () => T): T | undefined {
  const existing = map.get(key);
  if (existing !== undefined) return existing;
  if (map.size >= (m.maxSeries ?? Number.POSITIVE_INFINITY)) {
    if (!m.seriesWarned) {
      m.seriesWarned = true;
      console.warn(`[Metrics] '${m.def.name}' 达到序列上限 ${m.maxSeries}，新分区被丢弃（高基数标签？）`);
    }
    return undefined;
  }
  const created = make();
  map.set(key, created);
  return created;
}

export class MetricsRegistry {
  private metrics = new Map<string, MetricValue>();
  /** 单指标最大分区（序列）数，默认 10_000（P2 无界增长防御） */
  private readonly maxSeries: number;

  constructor(options: { maxSeries?: number } = {}) {
    this.maxSeries = options.maxSeries ?? 10_000;
  }

  /** 注册 Counter */
  counter(name: string, help: string, labels?: Labels): Counter {
    const def: MetricDef = { name, type: 'counter', help, labels };
    if (this.metrics.has(name)) {
      throw new Error(`Metric "${name}" already registered`);
    }
    this.metrics.set(name, { def, partitions: new Map(), maxSeries: this.maxSeries });
    return new Counter(name, this.metrics, labels);
  }

  /** 注册 Gauge */
  gauge(name: string, help: string, labels?: Labels): Gauge {
    const def: MetricDef = { name, type: 'gauge', help, labels };
    if (this.metrics.has(name)) {
      throw new Error(`Metric "${name}" already registered`);
    }
    this.metrics.set(name, { def, partitions: new Map(), maxSeries: this.maxSeries });
    return new Gauge(name, this.metrics, labels);
  }

  /** 注册 Histogram */
  histogram(name: string, help: string, buckets: number[], labels?: Labels): Histogram {
    const def: MetricDef = { name, type: 'histogram', help, labels };
    if (this.metrics.has(name)) {
      throw new Error(`Metric "${name}" already registered`);
    }
    const bounds = [...buckets].sort((a, b) => a - b);
    this.metrics.set(name, {
      def,
      partitions: new Map(),
      histPartitions: new Map(),
      bucketBounds: bounds,
      maxSeries: this.maxSeries,
    });
    return new Histogram(name, this.metrics, labels);
  }

  /** 获取所有指标快照 */
  snapshot(): MetricSnapshot[] {
    const snaps: MetricSnapshot[] = [];
    for (const { def, partitions, histPartitions, bucketBounds } of this.metrics.values()) {
      // 单分区或无标签：保持向后兼容，输出主快照
      const mainLabels = def.labels;
      const mainKey = labelKey(mainLabels);
      const snap: MetricSnapshot = {
        name: def.name,
        type: def.type,
        help: def.help,
        value: def.type === 'histogram'
          ? (histPartitions?.get(mainKey)?.count ?? 0)
          : (partitions.get(mainKey) ?? 0),
        labels: mainLabels,
      };
      if (def.type === 'histogram' && histPartitions && bucketBounds) {
        const p = histPartitions.get(mainKey);
        snap.buckets = Object.fromEntries((p?.buckets ?? new Map()).entries());
        snap.count = p?.count ?? 0;
        snap.sum = p?.sum ?? 0;
      }
      snaps.push(snap);
    }
    return snaps;
  }

  /** 导出 Prometheus 格式（逐标签分区渲染） */
  toPrometheus(): string {
    const lines: string[] = [];
    for (const { def, partitions, histPartitions, bucketBounds } of this.metrics.values()) {
      lines.push(`# HELP ${def.name} ${def.help}`);
      lines.push(`# TYPE ${def.name} ${def.type}`);

      if (def.type === 'histogram' && histPartitions && bucketBounds) {
        for (const [sig, hp] of histPartitions) {
          const extra = sig ? `,${labelSelector(labelsFromSig(sig))}` : '';
          for (const le of bucketBounds) {
            lines.push(`${def.name}_bucket{le="${le}"${extra}} ${hp.buckets.get(le) ?? 0}`);
          }
          lines.push(`${def.name}_bucket{le="+Inf"${extra}} ${hp.count}`);
          lines.push(`${def.name}_sum${sig ? `{${labelSelector(labelsFromSig(sig))}}` : ''} ${hp.sum}`);
          lines.push(`${def.name}_count${sig ? `{${labelSelector(labelsFromSig(sig))}}` : ''} ${hp.count}`);
        }
      } else {
        // counter / gauge：若有声明标签且存在分区，逐分区输出
        const declaredKeys = def.labels ? Object.keys(def.labels) : [];
        if (declaredKeys.length > 0 && partitions.size > 0) {
          for (const [sig, val] of partitions) {
            const ls = sig ? `{${labelSelector(labelsFromSig(sig))}}` : '';
            lines.push(`${def.name}${ls} ${val}`);
          }
        } else {
          const val = partitions.get('') ?? 0;
          lines.push(`${def.name} ${val}`);
        }
      }
    }
    return lines.join('\n') + '\n';
  }

  /** 清空所有指标 */
  clear(): void {
    this.metrics.clear();
  }
}

/** 从分区键还原标签对象（仅用于 Prometheus 输出渲染） */
function labelsFromSig(sig: string): Labels {
  if (!sig) return {};
  const out: Labels = {};
  for (const pair of sig.split(',')) {
    const eq = pair.indexOf('=');
    if (eq > 0) out[pair.slice(0, eq)] = pair.slice(eq + 1);
  }
  return out;
}

// ============================================================
// Metric 类型（支持 labels 分区：.with(values) 返回绑定子实例）
// ============================================================

abstract class LabeledMetric {
  constructor(
    readonly name: string,
    protected store: Map<string, MetricValue>,
    readonly baseLabels?: Labels,
  ) { }

  /** 返回绑定到指定标签值的子实例（共享同一指标，不同分区） */
  with(labelValues: Labels): this {
    // 合并：以 baseLabels 为默认，覆盖为 labelValues
    const merged: Labels = { ...(this.baseLabels ?? {}) };
    for (const [k, v] of Object.entries(labelValues)) merged[k] = v;
    const bound = Object.create(this.constructor.prototype) as this;
    Object.assign(bound, this, { baseLabels: merged });
    return bound;
  }

  protected key(): string {
    return labelKey(this.baseLabels);
  }
}

class Counter extends LabeledMetric {
  inc(by = 1): void {
    const m = this.store.get(this.name);
    if (!m) return;
    const k = this.key();
    const cur = putSeries(m, m.partitions, k, () => 0);
    if (cur !== undefined) m.partitions.set(k, cur + by);
  }

  get(): number {
    return this.store.get(this.name)?.partitions.get(this.key()) ?? 0;
  }
}

class Gauge extends LabeledMetric {
  set(value: number): void {
    const m = this.store.get(this.name);
    if (!m) return;
    const cur = putSeries(m, m.partitions, this.key(), () => 0);
    if (cur !== undefined) m.partitions.set(this.key(), value);
  }

  inc(by = 1): void {
    const m = this.store.get(this.name);
    if (!m) return;
    const k = this.key();
    const cur = putSeries(m, m.partitions, k, () => 0);
    if (cur !== undefined) m.partitions.set(k, cur + by);
  }

  dec(by = 1): void {
    const m = this.store.get(this.name);
    if (!m) return;
    const k = this.key();
    const cur = putSeries(m, m.partitions, k, () => 0);
    if (cur !== undefined) m.partitions.set(k, cur - by);
  }

  get(): number {
    return this.store.get(this.name)?.partitions.get(this.key()) ?? 0;
  }
}

class Histogram extends LabeledMetric {
  observe(value: number): void {
    const m = this.store.get(this.name);
    if (!m || !m.histPartitions || !m.bucketBounds) return;
    const k = this.key();
    const hp = putSeries(m, m.histPartitions, k, () => ({
      buckets: new Map(m.bucketBounds!.map(b => [b, 0])),
      count: 0,
      sum: 0,
    }));
    if (!hp) return;
    hp.count++;
    hp.sum += value;
    // 累计桶：每个 ≤ value 的上界都 +1
    for (const le of m.bucketBounds) {
      if (value <= le) {
        hp.buckets.set(le, (hp.buckets.get(le) ?? 0) + 1);
      }
    }
  }

  get(): number {
    return this.store.get(this.name)?.histPartitions?.get(this.key())?.count ?? 0;
  }
}
