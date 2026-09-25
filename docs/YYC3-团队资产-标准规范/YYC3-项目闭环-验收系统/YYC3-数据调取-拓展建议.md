---
file: YYC3-数据调取-拓展建议.md
description: YYC³ 项目闭环验收系统 — 数据获取策略与API扩展优化建议（第七类验收阶段）
author: YanYuCloudCube Team <admin@0379.email>
version: v2.0.0
created: 2026-05-25
updated: 2026-05-30
status: stable
tags: [验收],[数据调取],[API设计],[缓存策略],[性能优化],[扩展性]
category: acceptance
language: zh-CN
audience: developers,backend-engineers,frontend-engineers,architects
complexity: advanced
---

# YYC³ 数据调取拓展建议

> **"言启千行代码，语枢万物智能"** — 高效的数据流动是智能应用的血液

## 📋 文档概览

| 维度 | 内容 |
|------|------|
| **验收阶段** | 第七阶段：数据调取与API扩展优化 |
| **核心目标** | 建立高效、可靠、可扩展的数据获取体系 |
| **适用范围** | API设计、数据层架构、缓存策略、状态管理 |
| **输出产物** | 数据调取优化报告 + 实施路线图 |
| **关联文档** | [功能逻辑验收](./YYC3-功能逻辑-验收标准.md) \| [闭环验证标准](./YYC3-闭环验证-验收标准.md) \| [性能优化审核](./YYC3-深度审核-性能优化.md) |

---

## 🎯 验收目标与定位

### 核心使命

数据调取是现代Web应用的核心环节，本阶段旨在：

1. **建立标准化API规范** - 统一接口设计风格，提升协作效率
2. **优化数据获取策略** - 减少不必要的请求，提升用户体验
3. **构建多层缓存体系** - 平衡性能与一致性，降低服务器压力
4. **增强错误恢复能力** - 优雅处理网络异常，保证应用稳定性
5. **预留扩展空间** - 支持未来业务增长和技术演进

### 五高架构支撑

```
┌─────────────────────────────────────────────────────────────┐
│                    五高架构支撑体系                            │
├─────────────┬─────────────┬─────────────┬─────────────┬─────┤
│  高可用性    │   高性能     │   高安全     │   高扩展     │高智能 │
│             │             │             │             │      │
│ • 多级降级   │ • 智能预取   │ • 数据加密   │ • 插件化    │• 自适 │
│   策略       │   加载      │ 传输        │   中间件     │  缓存 │
│ • 故障自动   │ • 并行请求   │ • 权限校验   │ • 版本化    │• 智能 │
│   重试       │   合并      │ • 输入过滤   │   API       │  预测 │
│ • 离线支持   • 增量更新    │ • 防重放攻击  │ • GraphQL   │• 学习 │
│             │             │             │   支持       │  能力 │
└─────────────┴─────────────┴─────────────┴─────────────┴─────┘
```

---

## 📊 五维评估框架

### 时间维：响应时效

```typescript
interface TimeDimensionMetrics {
  /** API响应时间分布 */
  responseTimeDistribution: {
    p50: number; // ms
    p90: number; // ms
    p99: number; // ms;
    avg: number; // ms
  };

  /** 缓存命中率 */
  cacheHitRate: {
    l1Cache: number; // 内存缓存命中率
    l2Cache: number; // 分布式缓存命中率
    cdnCache: number; // CDN边缘缓存命中率
    overall: number; // 综合命中率
  };

  /** 数据新鲜度 */
  dataFreshness: {
    maxStaleTime: number; // 最大允许陈旧时间（秒）
    averageAge: number; // 平均数据年龄（秒）
    invalidationLatency: number; // 失效传播延迟（毫秒）
  };

  /** 并发处理能力 */
  concurrencyHandling: {
    maxConcurrentRequests: number;
    requestQueueLength: number;
    throughput: number; // requests/second
  };
}
```

**验收标准**：

- ✅ P0: P99响应时间 ≤ 1000ms（关键API）
- ✅ P1: 综合缓存命中率 ≥ 80%
- ✅ P2: 平均数据新鲜度 ≤ 30秒

### 空间维：覆盖广度

```typescript
interface SpaceDimensionCoverage {
  /** 数据源覆盖 */
  dataSourceCoverage: {
    restApis: { total: number; optimized: number };
    graphqlQueries: { total: number; optimized: number };
    websocketChannels: { total: number; optimized: number };
    thirdPartyIntegrations: { total: number; secured: number };
  };

  /** 层级覆盖 */
  layerCoverage: {
    apiGateway: boolean;
    backendService: boolean;
    database: boolean;
    cacheLayer: boolean;
    clientSide: boolean;
  };

  /** 场景覆盖 */
  scenarioCoverage: {
    initialLoad: boolean;
    pagination: boolean;
    realTimeUpdates: boolean;
    offlineMode: boolean;
    backgroundSync: boolean;
  };
}
```

**验收标准**：

- ✅ P0: 所有核心API已优化
- ✅ P1: 关键场景全覆盖
- ✅ P2: 第三方集成安全性100%

### 属性维：质量特性

```typescript
interface AttributeDimensionQuality {
  /** 一致性保证 */
  consistency: {
    readAfterWriteConsistency: boolean;
    eventualConsistencyWindow: number; // ms
    crossServiceConsistency: boolean;
  };

  /** 可靠性指标 */
  reliability: {
    availability: number; // %
    errorRate: number; // %
    retrySuccessRate: number; // %
  };

  /** 效率指标 */
  efficiency: {
    payloadCompressionRate: number; // %
    bandwidthOptimization: number; // 节省百分比
    requestDeduplicationRate: number; // %
  };

  ** 安全性指标 */
  security: {
    encryptionInTransit: boolean;
    authenticationCoverage: number; // %
    rateLimitingEnabled: boolean;
    inputValidationCoverage: number; // %
  };
}
```

**验收标准**：

- ✅ P0: API可用性 ≥ 99.9%
- ✅ P1: 错误率 < 0.1%
- ✅ P2: 带宽优化 ≥ 40%

### 事件维：异常处理

```typescript
interface EventDimensionHandling {
  /** 错误分类统计 */
  errorClassification: {
    networkErrors: { count: number; rate: number };
    serverErrors: { count: number; rate: number };
    clientErrors: { count: number; number: number };
    timeoutErrors: { count: number; rate: number };
  };

  ** 重试策略效果 */
  retryEffectiveness: {
    totalRetries: number;
    successfulRetries: number;
    retrySuccessRate: number;
    averageRetryCount: number;
    maxRetriesPerRequest: number;
  };

  ** 降级策略触发 */
  degradationTriggers: {
    circuitBreakerOpens: number;
    fallbackResponses: number;
    cacheFallbacks: number;
    offlineModeActivations: number;
  };

  ** 监控告警 */
  monitoringAlerts: {
    criticalAlerts: number;
    warningAlerts: number;
    falsePositives: number;
    meanTimeToDetection: number; // minutes
    meanTimeToResolution: number; // minutes;
  };
}
```

**验收标准**：

- ✅ P0: 关键错误自动恢复率 ≥ 95%
- ✅ P1: 平均故障检测时间 ≤ 5分钟
- ✅ P2: 误报率 < 10%

### 关联维：依赖协调

```typescript
interface AssociationDimensionDependencies {
  ** 上游服务依赖 */
  upstreamServices: {
    primaryDatabase: { latency: number; availability: number };
    cacheService: { latency: number; hitRate: number };
    searchEngine: { latency: number; relevance: number };
    externalAPIs: Array<{ name: string; quotaUsed: number; quotaLimit: number }>;
  };

  ** 下游消费者影响 */
  downstreamConsumers: {
    webClients: { count: number; avgLatency: number };
    mobileApps: { count: number; avgLatency: number };
    thirdPartyClients: { count: number; slaMet: number };
  };

  ** 横向服务调用 */
  serviceCalls: {
    synchronousCalls: { count: number; avgDuration: number };
    asynchronousCalls: { count: number; avgDuration: number };
    fanOutRequests: { maxFanOut: number; timeout: number };
  };
}
```

**验收标准**：

- ✅ P0: 无单点故障依赖
- ✅ P1: 服务间调用超时合理设置
- ✅ P2: 配额使用 < 80%

---

## 🔧 核心技术方案

### 1. RESTful API 设计规范

#### 1.1 URL设计原则

```typescript
// src/api/standards/url-conventions.ts
/**
 * YYC³ API URL设计规范
 *
 * 核心原则:
 * 1. 使用名词而非动词
 * 2. 使用复数形式表示资源集合
 * 3. 使用连字符(-)分隔单词
 * 4. 保持层级深度≤3层
 * 5. 使用查询参数进行过滤、排序、分页
 */

const urlPatterns = {
  /** 资源集合 */
  collections: {
    // ✓ 正确示例
    good: [
      '/api/v1/users',
      '/api/v1/users/{userId}/posts',
      '/api/v1/posts?status=published&sort=-createdAt&page=1&limit=20',
    ],

    // ✗ 错误示例
    bad: [
      '/api/v1/getAllUsers',           // 不应使用动词
      '/api/v1/users/getPosts',         // 过深的嵌套
      '/api/v1/user',                   // 应使用复数
    ],
  },

  /** 动作（当标准CRUD不够用时） */
  actions: {
    // 使用动词作为资源子路径
    examples: [
      '/api/v1/users/{userId}/activate',
      '/api/v1/orders/{orderId}/cancel',
      '/api/v1/posts/{postId}/publish',
    ],
  },

  /** 版本控制 */
  versioning: {
    strategy: 'URL-based', // 推荐: /api/v1/
    alternatives: ['Header-based', 'Content-negotiation'],
    currentVersion: 'v1',
    deprecatedVersions: ['v0'],
  },
};

/** HTTP方法语义映射 */
const httpMethods = {
  GET: '获取资源（安全、幂等）',
  POST: '创建资源（非幂等）',
  PUT: '全量替换资源（幂等）',
  PATCH: '部分更新资源（幂等）',
  DELETE: '删除资源（幂等）',
};
```

#### 1.2 请求/响应格式规范

```typescript
// src/api/types/api-response.ts
import { z } from 'zod';

/**
 * 统一API响应格式
 */

/** 成功响应 */
export const SuccessResponseSchema = z.object({
  success: z.literal(true),
  data: z.unknown(),
  meta: z.object({
    requestId: z.string().uuid(),
    timestamp: z.string().datetime(),
    version: z.string(),
  }).optional(),
  pagination: z.object({
    page: z.number().int().positive(),
    limit: z.number().int().positive().max(100),
    total: z.number().int().nonnegative(),
    totalPages: z.number().int().nonnegative(),
  }).optional(),
});

/** 错误响应 */
export const ErrorResponseSchema = z.object({
  success: z.literal(false),
  error: z.object({
    code: z.string(),          // 错误码: ERR_XXX
    message: z.string(),       // 用户可读的错误信息
    details: z.array(z.object({
      field: z.string(),       // 字段名
      message: z.string(),     // 具体错误描述
      code: z.string(),        // 具体错误码
    })).optional(),
  }),
  meta: z.object({
    requestId: z.string().uuid(),
    timestamp: z.string().datetime(),
    traceId: z.string().optional(), // 用于链路追踪
  }),
});

export type SuccessResponse<T> = z.infer<typeof SuccessResponseSchema> & {
  data: T;
};

export type ErrorResponse = z.infer<typeof ErrorResponseSchema>;

/** 分页参数 */
export const PaginationParamsSchema = z.object({
  page: z.coerce.number().int().positive().default(1),
  limit: z.coerce.number().int().positive().max(100).default(20),
  sortBy: z.string().optional(),
  sortOrder: z.enum(['asc', 'desc']).default('desc'),
});

export type PaginationParams = z.infer<typeof PaginationParamsSchema>;
```

#### 1.3 API客户端封装

```typescript
// src/lib/api-client.ts
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { ErrorResponse } from '@/types/api-response';

class ApiClient {
  private instance: AxiosInstance;

  constructor(baseURL: string) {
    this.instance = axios.create({
      baseURL,
      timeout: 15000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // 请求拦截器：添加认证token
    this.instance.interceptors.request.use((config) => {
      const token = this.getAuthToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }

      // 添加请求ID用于追踪
      config.headers['X-Request-ID'] = crypto.randomUUID();

      return config;
    });

    // 响应拦截器：统一错误处理
    this.instance.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response) {
          const errorData: ErrorResponse = error.response.data;

          // 根据错误码进行不同处理
          switch (error.response.status) {
            case 401:
              this.handleUnauthorized();
              break;
            case 403:
              this.handleForbidden();
              break;
            case 429:
              this.handleRateLimited(error);
              break;
            case 500:
              this.handleServerError(error);
              break;
            default:
              this.handleGenericError(errorData);
          }

          return Promise.reject(errorData);
        } else if (error.request) {
          // 网络错误
          this.handleNetworkError(error);
          return Promise.reject({
            success: false,
            error: {
              code: 'NETWORK_ERROR',
              message: '网络连接失败，请检查网络后重试',
            },
          });
        }

        return Promise.reject(error);
      }
    );
  }

  /**
   * GET请求
   */
  async get<T>(url: string, params?: Record<string, unknown>): Promise<T> {
    const response = await this.instance.get<SuccessResponse<T>>(url, { params });
    return response.data.data;
  }

  /**
   * POST请求
   */
  async post<T>(url: string, data?: unknown): Promise<T> {
    const response = await this.instance.post<SuccessResponse<T>>(url, data);
    return response.data.data;
  }

  /**
   * PUT请求
   */
  async put<T>(url: string, data?: unknown): Promise<T> {
    const response = await this.instance.put<SuccessResponse<T>>(url, data);
    return response.data.data;
  }

  /**
   * DELETE请求
   */
  async delete<T>(url: string): Promise<T> {
    const response = await this.instance.delete<SuccessResponse<T>>(url);
    return response.data.data;
  }

  private getAuthToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('auth_token');
    }
    return null;
  }

  private handleUnauthorized() {
    // 清除token并跳转登录页
    localStorage.removeItem('auth_token');
    window.location.href = '/login?redirect=' + encodeURIComponent(window.location.pathname);
  }

  private handleForbidden() {
    // 显示无权限提示
    console.error('权限不足');
  }

  private handleRateLimited(error: any) {
    const retryAfter = error.response.headers['retry-after'];
    console.warn(`请求过于频繁，请${retryAfter || 60}秒后重试`);
  }

  private handleServerError(error: any) {
    console.error('服务器内部错误，请联系管理员');
    // 可以在此上报错误到监控系统
  }

  private handleNetworkError(error: any) {
    console.error('网络连接失败');
    // 可以尝试从缓存返回数据
  }

  private handleGenericError(errorData: ErrorResponse) {
    console.error(errorData.error.message);
  }
}

// 创建全局实例
export const apiClient = new ApiClient(process.env.NEXT_PUBLIC_API_URL!);
export default ApiClient;
```

### 2. 数据获取策略

#### 2.1 React Query / SWR 最佳实践

```typescript
// src/hooks/use-optimized-query.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';

/**
 * 通用的数据获取Hook
 * 封装了缓存、重试、错误处理等最佳实践
 */
export function useOptimizedQuery<T>(
  key: unknown[],
  fetcher: () => Promise<T>,
  options?: {
    staleTime?: number;        // 数据新鲜时间（ms）
    cacheTime?: number;        // 缓存保留时间（ms）
    refetchOnWindowFocus?: boolean;
    refetchOnReconnect?: boolean;
    retry?: number | boolean;
    retryDelay?: number;
    enabled?: boolean;
  }
) {
  return useQuery({
    queryKey: key,
    queryFn: fetcher,
    staleTime: options?.staleTime ?? 5 * 60 * 1000, // 默认5分钟
    gcTime: options?.cacheTime ?? 10 * 60 * 1000,    // 默认10分钟
    refetchOnWindowFocus: options?.refetchOnWindowFocus ?? true,
    refetchOnReconnect: options?.refetchOnReconnect ?? true,
    retry: options?.retry ?? 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000), // 指数退避，最大30秒
    enabled: options?.enabled ?? true,
  });
}

/**
 * 用户相关Hooks
 */
export function useUser(userId: string) {
  return useOptimizedQuery(
    ['user', userId],
    () => apiClient.get(`/users/${userId}`),
    { staleTime: 10 * 60 * 1000 } // 用户信息变化较少，缓存更久
  );
}

export function useUserList(params: { page: number; limit: number }) {
  return useOptimizedQuery(
    ['users', params],
    () => apiClient.get('/users', params),
    { staleTime: 30 * 1000 } // 列表数据相对实时
  );
}

/**
 * 通用Mutation Hook
 */
export function useOptimizedMutation<TVariables, TData>(
  mutationFn: (variables: TVariables) => Promise<TData>,
  options?: {
    onSuccess?: (data: TData, variables: TVariables) => void;
    onError?: (error: Error, variables: TVariables) => void;
    invalidateQueries?: unknown[]; // mutation成功后失效的查询key
  }
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn,
    onSuccess: (data, variables) => {
      // 自动使相关查询失效
      if (options?.invalidateQueries) {
        queryClient.invalidateQueries({ queryKey: options.invalidateQueries });
      }
      options?.onSuccess?.(data, variables);
    },
    onError: (error, variables) => {
      options?.onError?.(error, variables);
    },
  });
}

/**
 * 创建用户Mutation示例
 */
export function CreateUserMutation() {
  return useOptimizedMutation(
    (userData) => apiClient.post('/users', userData),
    {
      invalidateQueries: ['users'],
      onSuccess: () => {
        // 显示成功提示
      },
      onError: (error) => {
        // 显示错误提示
      },
    }
  );
}
```

#### 2.2 乐观更新模式

```typescript
// src/hooks/use-optimistic-update.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';

/**
 * 乐观更新Hook
 * 在等待服务器响应前先更新UI，提升用户体验
 */
export function useOptimisticUpdate<T>(
  mutationFn: (data: T) => Promise<any>,
  queryKey: unknown[],
  updateFn: (oldData: T | undefined, newData: T) => T | undefined,
  rollbackFn?: (oldData: T | undefined) => T | undefined
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn,
    onMutate: async (newData) => {
      // 取消正在进行的查询以避免冲突
      await queryClient.cancelQueries({ queryKey });

      // 快照之前的值
      const previousData = queryClient.getQueryData<T>(queryKey);

      // 乐观更新
      queryClient.setQueryData<T>(queryKey, (old) => updateFn(old, newData));

      // 返回快照以便回滚
      return { previousData };
    },
    onError: (err, newData, context) => {
      // 出错时回滚
      if (context?.previousData) {
        queryClient.setQueryData(queryKey, context.previousData);
      }
      // 或者使用自定义回滚函数
      if (rollbackFn && context?.previousData) {
        queryClient.setQueryData(queryKey, rollbackFn(context.previousData));
      }
    },
    onSettled: () => {
      // 无论成功失败都重新获取数据确保一致性
      queryClient.invalidateQueries({ queryKey });
    },
  });
}

/**
 * 示例：点赞功能的乐观更新
 */
export function useLikePost(postId: string) {
  return useOptimisticUpdate(
    (isLiked: boolean) =>
      apiClient.post(`/posts/${postId}/like`, { isLiked }),
    ['post', postId],
    (oldPost, isLiked) => {
      if (!oldPost) return oldPost;
      return {
        ...oldPost,
        isLiked,
        likesCount: isLiked ? oldPost.likesCount + 1 : oldPost.likesCount - 1,
      };
    }
  );
}
```

### 3. 缓存策略体系

#### 3.1 多级缓存架构

```typescript
// src/cache/multi-level-cache.ts
/**
 * YYC³ 多级缓存策略
 *
 * L1: 内存缓存 (React Query/SWR)
 * L2: 浏览器持久化 (IndexedDB/LocalStorage)
 * L3: CDN/边缘缓存 (静态资源和公开API)
 * L4: 服务端缓存 (Redis/Memcached)
 * L5: 数据库查询缓存
 */

enum CacheLevel {
  MEMORY = 'L1',       // 内存缓存
  PERSISTENT = 'L2',   // 持久化缓存
  CDN = 'L3',          // CDN缓存
  REDIS = 'L4',        // Redis缓存
  DATABASE = 'L5',     // 数据库缓存
}

interface CachePolicy {
  level: CacheLevel;
  ttl: number;          // 存活时间（秒）
  staleWhileRevalidate?: number; // SWR时间（秒）
  maxSize?: number;     // 最大条目数（仅内存缓存）
}

/** 不同类型数据的缓存策略 */
const cachePolicies: Record<string, CachePolicy> = {
  // 用户个人信息 - 变化少，缓存久
  user_profile: {
    level: CacheLevel.MEMORY,
    ttl: 3600,                    // 1小时
    staleWhileRevalidate: 300,    // 5分钟SWR
  },

  // 公开内容 - 可CDN缓存
  public_content: {
    level: CacheLevel.CDN,
    ttl: 300,                     // 5分钟
    staleWhileRevalidate: 60,     // 1分钟SWR
  },

  // 权限信息 - 需要较新
  permissions: {
    level: CacheLevel.MEMORY,
    ttl: 300,                     // 5分钟
    staleWhileRevalidate: 30,     // 30秒SWR
  },

  // 配置数据 - 很少变化
  app_config: {
    level: CacheLevel.PERSISTENT,
    ttl: 86400,                   // 24小时
    staleWhileRevalidate: 3600,   // 1小时SWR
  },

  // 会话数据 - 不能缓存太久
  session_data: {
    level: CacheLevel.REDIS,
    ttl: 1800,                    // 30分钟
  },
};

/**
 * 缓存键命名规范
 */
function generateCacheKey(namespace: string, identifier: string, params?: Record<string, unknown>): string {
  const base = `${namespace}:${identifier}`;
  if (!params || Object.keys(params).length === 0) {
    return base;
  }

  const sortedParams = Object.keys(params)
    .sort()
    .map(key => `${key}=${params[key]}`)
    .join('&');

  return `${base}?${sortedParams}`;
}

// 示例使用
const userCacheKey = generateCacheKey('user', '123', { includeProfile: true });
// 结果: "user:123?includeProfile=true"
```

#### 3.2 React Query 缓存配置

```typescript
// src/lib/query-client.ts
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // 数据被认为过时的时间（ms）
      staleTime: 5 * 60 * 1000, // 5分钟

      // 缓存垃圾回收时间（ms），未使用的缓存将被清理
      gcTime: 10 * 60 * 1000, // 10分钟

      // 窗口聚焦时是否重新获取
      refetchOnWindowFocus: true,

      // 网络重连时是否重新获取
      refetchOnReconnect: true,

      // 组件挂载时是否重新获取
      refetchOnMount: true,

      // 重试次数
      retry: 3,

      // 重试延迟（指数退避）
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),

      // 是否在后台重新获取过期数据
      refetchInterval: false,

      // 结构共享（减少内存占用）
      structuralSharing: true,
    },
    mutations: {
      // Mutation重试次数
      retry: 1,

      // Mutation重试延迟
      retryDelay: 1000,
    },
  },
});
```

#### 3.3 Service Worker 缓存策略

```typescript
// public/sw.js (Service Worker)
const CACHE_NAME = 'yyc3-v1';
const STATIC_ASSETS = [
  '/',
  '/offline.html',
  '/manifest.json',
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png',
];

/** 安装事件：预缓存静态资源 */
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

/** 激活事件：清理旧缓存 */
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME)
          .map((name) => caches.delete(name))
      );
    })
  );
  self.clients.claim();
});

/** 请求拦截：缓存策略 */
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // 只处理GET请求
  if (request.method !== 'GET') return;

  // API请求：Network First + Cache Fallback
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      caches.open(`${CACHE_NAME}-api`).then(async (cache) => {
        try {
          const networkResponse = await fetch(request);

          // 只缓存成功的GET请求
          if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
          }

          return networkResponse;
        } catch (error) {
          const cachedResponse = await cache.match(request);
          if (cachedResponse) {
            // 返回缓存数据但添加警告头
            const headers = new Headers(cachedResponse.headers);
            headers.set('X-Cache-Status', 'stale');
            return new Response(cachedResponse.body, {
              status: cachedResponse.status,
              statusText: cachedResponse.statusText,
              headers,
            });
          }

          // 返回离线响应
          return caches.match('/offline.html');
        }
      })
    );
    return;
  }

  // 静态资源：Cache First + Network Fallback
  if (STATIC_ASSETS.some(asset => url.pathname.endsWith(asset.split('/').pop()!))) {
    event.respondWith(
      caches.match(request).then((response) => {
        if (response) {
          return response;
        }
        return fetch(request).then((networkResponse) => {
          if (networkResponse.ok) {
            const clone = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
          }
          return networkResponse;
        });
      })
    );
    return;
  }

  // 其他请求：Stale While Revalidate
  event.respondWith(
    caches.open(CACHE_NAME).then(async (cache) => {
      const cachedResponse = await cache.match(request);
      const networkPromise = fetch(request).then((networkResponse) => {
        if (networkResponse.ok) {
          cache.put(request, networkResponse.clone());
        }
        return networkResponse;
      });

      // 优先返回缓存，后台更新
      return cachedResponse || networkPromise;
    })
  );
});
```

### 4. 错误处理与重试机制

#### 4.1 统一错误处理中间件

```typescript
// src/middleware/error-handler.ts
import { NextRequest, NextResponse } from 'next/server';
import { ZodError } from 'zod';

type ErrorWithStatus = Error & { status?: number };

export function errorHandler(err: ErrorWithStatus, req: NextRequest) {
  console.error(`[Error] ${req.method} ${req.pathname}:`, err.message);
  console.error(err.stack);

  // Zod验证错误
  if (err instanceof ZodError) {
    return NextResponse.json(
      {
        success: false,
        error: {
          code: 'VALIDATION_ERROR',
          message: '请求参数验证失败',
          details: err.errors.map(e => ({
            field: e.path.join('.'),
            message: e.message,
            code: e.code,
          })),
        },
      },
      { status: 400 }
    );
  }

  // 自定义错误
  if (err.status) {
    return NextResponse.json(
      {
        success: false,
        error: {
          code: getErrorCode(err.status),
          message: err.message,
        },
      },
      { status: err.status }
    );
  }

  // 未知错误
  return NextResponse.json(
    {
      success: false,
      error: {
        code: 'INTERNAL_SERVER_ERROR',
        message: process.env.NODE_ENV === 'production'
          ? '服务器内部错误'
          : err.message,
      },
    },
    { status: 500 }
  );
}

function getErrorCode(status: number): string {
  const codes: Record<number, string> = {
    400: 'BAD_REQUEST',
    401: 'UNAUTHORIZED',
    403: 'FORBIDDEN',
    404: 'NOT_FOUND',
    409: 'CONFLICT',
    422: 'UNPROCESSABLE_ENTITY',
    429: 'RATE_LIMITED',
  };
  return codes[status] || 'SERVER_ERROR';
}
```

#### 4.2 智能重试策略

```typescript
// src/utils/retry-strategy.ts
interface RetryOptions {
  maxRetries: number;
  baseDelay: number;          // ms
  maxDelay: number;           // ms
  backoffFactor: number;      // 指数退避因子
  retryableStatuses: number[]; // 可重试的HTTP状态码
  retryableErrors: string[];  // 可重试的错误码
}

const defaultRetryOptions: RetryOptions = {
  maxRetries: 3,
  baseDelay: 1000,
  maxDelay: 30000,
  backoffFactor: 2,
  retryableStatuses: [408, 429, 500, 502, 503, 504],
  retryableErrors: ['NETWORK_ERROR', 'TIMEOUT', 'ECONNRESET'],
};

/**
 * 带指数退避的重试函数
 */
async function withRetry<T>(
  fn: () => Promise<T>,
  options: Partial<RetryOptions> = {}
): Promise<T> {
  const opts = { ...defaultRetryOptions, ...options };
  let lastError: Error;

  for (let attempt = 0; attempt <= opts.maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;

      // 检查是否应该重试
      if (attempt === opts.maxRetries || !shouldRetry(error, opts)) {
        throw error;
      }

      // 计算延迟时间
      const delay = calculateDelay(attempt, opts);
      console.log(`[Retry] Attempt ${attempt + 1}/${opts.maxRetries} failed, retrying in ${delay}ms`);

      await sleep(delay);
    }
  }

  throw lastError!;
}

function shouldRetry(error: any, options: RetryOptions): boolean {
  // 检查HTTP状态码
  if (error.response?.status && options.retryableStatuses.includes(error.response.status)) {
    return true;
  }

  // 检查错误码
  if (error.error?.code && options.retryableErrors.includes(error.error.code)) {
    return true;
  }

  // 检查网络错误
  if (error.code === 'ECONNRESET' || error.code === 'ETIMEDOUT') {
    return true;
  }

  return false;
}

function calculateDelay(attempt: number, options: RetryOptions): number {
  const exponentialDelay = options.baseDelay * Math.pow(options.backoffFactor, attempt);

  // 添加随机抖动避免惊群效应
  const jitter = exponentialDelay * 0.1 * Math.random();

  return Math.min(exponentialDelay + jitter, options.maxDelay);
}

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export { withRetry, defaultRetryOptions };
export type { RetryOptions };
```

### 5. 性能优化方案

#### 5.1 请求合并与去重

```typescript
// src/utils/request-deduplicator.ts
/**
 * 请求去重器
 * 相同的并发请求只发送一次，结果共享
 */

class RequestDeduplicator {
  private pendingRequests = new Map<string, Promise<any>>();

  /**
   * 发送去重请求
   */
  async dedupe<T>(key: string, requestFn: () => Promise<T>): Promise<T> {
    // 如果已有相同请求在进行中，直接返回该Promise
    if (this.pendingRequests.has(key)) {
      console.log(`[Dedupe] Reusing existing request: ${key}`);
      return this.pendingRequests.get(key)!;
    }

    // 创建新请求
    const promise = requestFn()
      .finally(() => {
        // 请求完成后清除记录
        this.pendingRequests.delete(key);
      });

    this.pendingRequests.set(key, promise);
    return promise;
  }

  /**
   * 批量请求合并
   * 将多个单独的请求合并为一个批量请求
   */
  async batchFetch<T>(
    items: Array<{ id: string }>,
    batchFetcher: (ids: string[]) => Promise<Map<string, T>>
  ): Promise<Map<string, T>> {
    const ids = items.map(item => item.id);
    const results = await batchFetcher(ids);
    return results;
  }
}

export const requestDeduplicator = new RequestDeduplicator();

// 使用示例
async function getUser(userId: string) {
  return requestDeduplicator.dedupe(
    `user:${userId}`,
    () => apiClient.get(`/users/${userId}`)
  );
}

// 即使同时多次调用getUser('123')，也只会发送一次请求
const [user1, user2, user3] = await Promise.all([
  getUser('123'),
  getUser('123'), // 复用上面的请求
  getUser('123'), // 复用上面的请求
]);
```

#### 5.2 数据预加载

```typescript
// src/utils/prefetch.ts
import { queryClient } from '@/lib/query-client';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

/**
 * 预加载工具
 * 在用户可能需要数据之前提前加载
 */

/** 鼠标悬停预加载 */
export function usePrefetchOnHover<T>(
  queryKey: unknown[],
  prefetchFn: () => Promise<T>,
  delay: number = 200
) {
  const timerRef = useRef<NodeJS.Timeout>();

  const handleMouseEnter = () => {
    timerRef.current = setTimeout(() => {
      queryClient.prefetchQuery({
        queryKey,
        queryFn: prefetchFn,
        staleTime: 10000, // 预加载数据10秒内有效
      });
    }, delay);
  };

  const handleMouseLeave = () => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }
  };

  return { onMouseEnter: handleMouseEnter, onMouseLeave: handleMouseLeave };
}

/** 视口内预加载 */
export function useIntersectionPrefetch<T>(
  queryKey: unknown[],
  prefetchFn: () => Promise<T>,
  options?: {
    rootMargin?: string;
    threshold?: number;
  }
) {
  const elementRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const element = elementRef.current;
    if (!element) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            queryClient.prefetchQuery({
              queryKey,
              queryFn: prefetchFn,
            });
            observer.unobserve(element); // 只触发一次
          }
        });
      },
      {
        rootMargin: options?.rootMargin ?? '200px', // 提前200px开始加载
        threshold: options?.threshold ?? 0,
      }
    );

    observer.observe(element);

    return () => observer.disconnect();
  }, [queryKey, prefetchFn]);

  return elementRef;
}

/** 路由切换预加载 */
export function useRoutePrefetch() {
  const router = useRouter();

  const prefetchRoute = (href: string) => {
    router.prefetch(href);
  };

  return { prefetchRoute };
}

// 使用示例：带预加载的Link组件
function PrefetchLink({ href, children, ...props }: LinkProps) {
  const { onMouseEnter, onMouseLeave } = usePrefetchOnHover(
    ['route-data', href],
    () => fetch(href).then(res => res.json())
  );

  return (
    <Link
      href={href}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      {...props}
    >
      {children}
    </Link>
  );
}
```

#### 5.3 响应压缩与优化

```typescript
// next.config.js (Next.js配置)
module.exports = {
  // 启用Gzip/Brotli压缩
  compress: true,

  // 图片优化
  images: {
    formats: ['image/avif', 'image/webp'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920],
    imageSizes: [16, 32, 48, 64, 96, 128, 256],
  },

  // 响应头配置
  async headers() {
    return [
      {
        source: '/api/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'no-store, must-revalidate', // API默认不缓存
          },
          {
            key: 'Content-Encoding',
            value: 'gzip', // 或根据Accept-Encoding动态选择
          },
        ],
      },
      {
        source: '/static/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable', // 静态资源长期缓存
          },
        ],
      },
    ];
  },

  // 实验性功能
  experimental: {
    // 启用optimizePackageImports减小bundle体积
    optimizePackageImports: ['lodash', 'date-fns', '@mui/material'],
  },
};
```

---

## ✅ 验收标准体系

### P0 必须通过（阻塞发布）

| 编号 | 验收项 | 标准 | 验证方法 |
|------|--------|------|----------|
| DTF-001 | API响应格式 | 100%符合规范 | 自动化测试 |
| DTF-002 | 认证覆盖率 | 所有API 100%覆盖 | 代码审查 |
| DTF-003 | 错误处理 | 无未捕获异常 | 错误监控 |
| DTF-004 | 超时设置 | 所有外部调用有超时 | 配置检查 |
| DTF-005 | 敏感数据保护 | 日志/响应中无明文密码 | 安全扫描 |

### P1 强烈建议（影响质量评级）

| 编号 | 验收项 | 标准 | 验证方法 |
|------|--------|------|----------|
| DTF-101 | 缓存命中率 | ≥ 80% | 监控面板 |
| DTF-102 | P95响应时间 | < 500ms | APM工具 |
| DTF-103 | 请求去重 | 并发重复请求 < 5% | 日志分析 |
| DTF-104 | 离线支持 | 核心功能可用 | 手动测试 |
| DTF-105 | 限流保护 | 所有限流生效 | 压力测试 |

### P2 可选优化（锦上添花）

| 编号 | 验收项 | 标准 | 验证方法 |
|------|--------|------|----------|
| DTF-201 | GraphQL支持 | 复杂查询可用 | 功能测试 |
| DTF-202 | 实时推送 | WebSocket稳定 | 长时间测试 |
| DTF-203 | 预取准确率 | > 70%命中 | 分析统计 |
| DTF-204 | Bundle Size | 较基线减小≥15% | 构建分析 |

---

## 📄 优化报告模板

### 数据调取优化报告

```markdown
# YYC³ 数据调取优化报告

**项目名称**: {{projectName}}
**评估日期**: {{assessmentDate}}
**评估周期**: {{startDate}} ~ {{endDate}}

---

## 📊 执行摘要

### 优化等级评定

{% if overallGrade == 'A' %}
🌟 **优秀 (A级)** — 数据调取体系达到业界领先水平
{% elif overallGrade == 'B' %}
✅ **良好 (B级)** — 整体表现良好，存在少量优化空间
{% elif overallGrade == 'C' %}
⚠️ **及格 (C级)** — 基本满足需求，建议重点优化以下领域
{% else %}
❌ **需改进 (D级)** — 存在严重问题，必须立即处理
{% endif %}

### 关键指标总览

| 指标 | 当前值 | 目标值 | 达成率 | 趋势 |
|------|--------|--------|--------|------|
| 平均响应时间 | {{avgResponse}}ms | < 300ms | {{responseRate}}% | {{responseTrend}} |
| 缓存命中率 | {{cacheHit}}% | > 80% | {{cacheRate}}% | {{cacheTrend}} |
| 错误率 | {{errorRate}}% | < 0.1% | {{errorRateAchieved}}% | {{errorTrend}} |
| 带宽节省 | {{bandwidthSaved}}% | > 40% | {{bandwidthRate}}% | {{bandwidthTrend}} |

---

## 一、API设计评估

### 1.1 RESTful规范遵循度

| 检查项 | 状态 | 备注 |
|--------|------|------|
| URL命名规范 | {{urlNaming}} | {{urlNamingNote}} |
| HTTP方法正确使用 | {{httpMethods}} | {{httpMethodsNote}} |
| 状态码使用恰当 | {{statusCode}} | {{statusCodeNote}} |
| 版本控制实施 | {{versioning}} | {{versioningNote}} |
| 分页实现规范 | {{pagination}} | {{paginationNote}} |

### 1.2 接口质量分析

{% for api in apis }}
#### {{api.name}} (`{{api.method}} {{api.path}}`)

- **复杂度**: {{api.complexity}}
- **平均耗时**: {{api.avgTime}}ms
- **P99耗时**: {{api.p99Time}}ms
- **调用频率**: {{api.calls}}次/天
- **错误率**: {{api.errorRate}}%
- **优化建议**: {{api.recommendation}}

{% endfor %}

---

## 二、缓存策略评估

### 2.1 缓存层级分析

| 缓存层 | 命中率 | 平均响应 | 配置合理性 | 优化建议 |
|--------|--------|----------|------------|----------|
| L1 内存缓存 | {{l1Hit}}% | {{l1Time}}ms | {{l1Config}} | {{l1Suggestion}} |
| L2 持久化缓存 | {{l2Hit}}% | {{l2Time}}ms | {{l2Config}} | {{l2Suggestion}} |
| L3 CDN缓存 | {{l3Hit}}% | {{l3Time}}ms | {{l3Config}} | {{l3Suggestion}} |
| L4 Redis缓存 | {{l4Hit}}% | {{l4Time}}ms | {{l4Config}} | {{l4Suggestion}} |

### 2.2 缓存键设计评估

- **命名规范遵循度**: {{namingCompliance}}%
- **键冲突风险**: {{collisionRisk}}
- **失效策略有效性**: {{invalidationEfficiency}}

---

## 三、性能瓶颈识别

### 3.1 TOP 5 慢接口

| 排名 | 接口 | 平均耗时 | 主要原因 | 优化方案 | 预期收益 |
|------|------|----------|----------|----------|----------|
| 1 | {{slowApi1.name}} | {{slowApi1.time}}ms | {{slowApi1.reason}} | {{slowApi1.solution}} | ↓{{slowApi1.gain}}% |
| 2 | {{slowApi2.name}} | {{slowApi2.time}}ms | {{slowApi2.reason}} | {{slowApi2.solution}} | ↓{{slowApi2.gain}}% |
| 3 | {{slowApi3.name}} | {{slowApi3.time}}ms | {{slowApi3.reason}} | {{slowApi3.solution}} | ↓{{slowApi3.gain}}% |
| 4 | {{slowApi4.name}} | {{slowApi4.time}}ms | {{slowApi4.reason}} | {{slowApi4.solution}} | ↓{{slowApi4.gain}}% |
| 5 | {{slowApi5.name}} | {{slowApi5.time}}ms | {{slowApi5.reason}} | {{slowApi5.solution}} | ↓{{slowApi5.gain}}% |

### 3.2 N+1查询问题

{% for nplus1 in nplus1Problems }}
- **位置**: {{nplus1.location}}
- **影响**: 每次请求额外产生 {{nplus1.extraQueries}} 次查询
- **解决方案**: {{nplus1.solution}}
- **优先级**: {{nplus1.priority}}

{% endfor %}

---

## 四、安全合规检查

### 4.1 数据传输安全

| 检查项 | 状态 | 详情 |
|--------|------|------|
| HTTPS强制使用 | {{httpsEnforced}} | {{httpsDetail}} |
| TLS版本 | {{tlsVersion}} | {{tlsDetail}} |
| 证书有效性 | {{certValid}} | {{certDetail}} |
| HSTS启用 | {{hstsEnabled}} | {{hstsDetail}} |

### 4.2 输入输出安全

| 检查项 | 状态 | 详情 |
|--------|------|------|
| SQL注入防护 | {{sqlInjection}} | {{sqlInjectionDetail}} |
| XSS防护 | {{xssProtection}} | {{xssDetail}} |
| CSRF防护 | {{csrfProtection}} | {{csrfDetail}} |
| 敏感数据脱敏 | {{dataMasking}} | {{dataMaskingDetail}} |

---

## 五、优化建议与路线图

### 5.1 立即执行（本周）

{% for immediate in immediates }}
- [ ] **{{immediate.title}}**
  - 预估工作量: {{immediate.effort}}
  - 预期收益: {{immediate.benefit}}
  - 负责人: {{immediate.owner}}

{% endfor %}

### 5.2 短期优化（本月）

{% for shortTerm in shortTerms }}
- [ ] **{{shortTerm.title}}**
  - 预估工作量: {{shortTerm.effort}}
  - 预期收益: {{shortTerm.benefit}}
  - 负责人: {{shortTerm.owner}}

{% endfor %}

### 5.3 中长期规划（下季度）

{{longTermPlan}}

---

## 六、结论与签字

### 6.1 总体评价

**综合评分**: {{overallScore}}/100
**优化潜力**: {{optimizationPotential}}

### 6.2 签字确认

| 角色 | 姓名 | 签字 | 日期 |
|------|------|------|------|
| 评估负责人 | ________________ | ________________ | _______ |
| 后端负责人 | ________________ | ________________ | _______ |
| 前端负责人 | ________________ | ________________ | _______ |
| 架构师 | ________________ | ________________ | _______ |

---

**报告生成时间**: {{reportGeneratedAt}}
**报告版本**: {{reportVersion}}

---

*本报告由 YYC³ 数据调取优化系统生成*
*如有疑问请联系: admin@0379.email*
```

---

## 🔄 实施检查清单

### Phase 1: 基础设施搭建（第1周）

- [ ] **API网关部署**
  - [ ] 选择并配置API网关（Kong/Apisix）
  - [ ] 设置路由规则和负载均衡
  - [ ] 配置限流和熔断策略

- [ ] **缓存基础设施**
  - [ ] Redis集群部署
  - [ ] 缓存监控面板搭建
  - [ ] 缓存失效通知机制

- [ ] **日志与监控**
  - [ ] 请求日志收集（ELK/Loki）
  - [ ] 性能指标采集（Prometheus）
  - [ ] 告警规则配置（Grafana）

### Phase 2: API规范化（第2-3周）

- [ ] **RESTful改造**
  - [ ] URL结构重构
  - [ ] HTTP方法语义修正
  - [ ] 统一响应格式

- [ ] **错误处理统一**
  - [ ] 错误码体系定义
  - [ ] 全局异常处理器
  - [ ] 友好错误提示

- [ ] **认证授权完善**
  - [ ] JWT/OAuth2.0集成
  - [ ] RBAC权限模型
  - [ ] Token刷新机制

### Phase 3: 性能优化（第4-5周）

- [ ] **查询优化**
  - [ ] 慢SQL分析与优化
  - [ ] N+1问题解决
  - [ ] 批量接口开发

- [ ] **缓存策略实施**
  - [ ] 热点数据缓存
  - [ ] 缓存穿透/击穿/雪崩防护
  - [ ] 多级缓存联动

- [ ] **前端优化**
  - [ ] React Query/SWR集成
  - [ ] 请求去重与合并
  - [ ] 预加载策略落地

### Phase 4: 安全加固（第6周）

- [ ] **传输加密**
  - [ ] HTTPS强制跳转
  - [ ] TLS 1.3启用
  - [ ] HSTS头部配置

- [ ] **输入验证**
  - [ ] Schema验证（Zod/Yup）
  - [ ] SQL注入防护
  - [ ] XSS过滤

- [ ] **限流防刷**
  - [ ] IP级别限流
  - [ ] 用户级别限流
  - [ ] 接口级别限流

---

## 🛠️ 工具链推荐

### 开发调试工具

```bash
# API测试
pnpm add -D @openapitools/openapi-generator-cli

# 性能分析
pnpm add -D lighthouse
pnpm add -D webpack-bundle-analyzer

# 缓存调试
# Chrome DevTools → Application → Storage
# RedisInsight (Redis GUI)

# 网络抓包
# Charles Proxy / Fiddler
# Wireshark (底层网络)
```

### 监控告警工具

```yaml
# docker-compose.yml (监控栈)
version: v2.0.0
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

  redis-exporter:
    image: oliver006/redis_exporter:latest
    command:
      - '--redis.addr=redis://redis:6379'
```

---

## 📚 相关资源与参考

### 内部文档

- [功能逻辑验收](./YYC3-功能逻辑-验收标准.md) - 业务逻辑层面的数据使用
- [闭环验证标准](./YYC3-闭环验证-验收标准.md) - 全链路数据追溯
- [性能优化审核](./YYC3-深度审核-性能优化.md) - 性能专项优化

### 外部参考

- [OpenAPI Specification](https://spec.openapis.org/oas/latest.html)
- [Google Web Fundamentals - Data Fetching](https://web.dev/fetching-data/)
- [React Query Documentation](https://tanstack.com/query/latest)

---

## 📝 版本历史

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| v1.0.0 | 2026-05-25 | YanYuCloudCube Team | 初始版本创建 |

---

*本文档遵循 YYC³ 团队标规闭环体系，基于五高五标五化五维框架构建*
*最后更新: 2026-05-25 | 下次审查: 2026-06-25*
