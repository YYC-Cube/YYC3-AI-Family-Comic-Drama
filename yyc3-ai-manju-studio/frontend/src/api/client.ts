/**
 * API 客户端：统一请求封装 + mock 降级
 * 后端未实现期间，前端依赖 withFallback 降级到演示数据，可独立开发
 */

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:25200";

export const GATEWAY_URL =
  process.env.NEXT_PUBLIC_GATEWAY_URL ?? "http://localhost:30001";

/** 请求超时时间（毫秒） */
const TIMEOUT_MS = 5000;

/** API 业务错误 */
export class ApiError extends Error {
  status?: number;

  constructor(message: string, status?: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

/** 统一 JSON 请求：5 秒超时 + 统一错误处理 */
export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);

  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...init,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        ...init?.headers,
      },
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new ApiError(`请求超时（${TIMEOUT_MS / 1000}s）：${path}`);
    }
    throw new ApiError(
      `网络错误：${err instanceof Error ? err.message : String(err)}`
    );
  } finally {
    clearTimeout(timer);
  }

  if (!res.ok) {
    throw new ApiError(`请求失败 ${res.status}：${path}`, res.status);
  }

  try {
    return (await res.json()) as T;
  } catch {
    throw new ApiError(`响应不是合法 JSON：${path}`);
  }
}

/** request 的别名导出，语义上表示“通用 API 拉取” */
export const apiFetch = request;

/**
 * mock 降级包装：真实请求失败时打印警告并返回演示数据
 * 后端补齐后无需改动调用方，自动切换回真实数据
 */
export async function withFallback<T>(
  realFn: () => Promise<T>,
  mockFn: () => T | Promise<T>
): Promise<{ data: T; isMock: boolean }> {
  try {
    const data = await realFn();
    return { data, isMock: false };
  } catch (err) {
    console.warn(
      "[API 降级] 后端不可达，使用演示数据：",
      err instanceof Error ? err.message : err
    );
    return { data: await mockFn(), isMock: true };
  }
}
