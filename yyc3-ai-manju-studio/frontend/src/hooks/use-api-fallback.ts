"use client";

/**
 * useApiFallback：通用数据拉取 hook（真实 API 优先，失败自动降级 mock）
 *
 * 返回 data / loading / error / isMock / refresh
 */
import { useCallback, useEffect, useRef, useState } from "react";
import { withFallback } from "@/api/client";

interface ApiFallbackResult<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  isMock: boolean;
  refresh: () => void;
}

export function useApiFallback<T>(
  fn: () => Promise<T>,
  mockFn: () => T,
  deps: ReadonlyArray<unknown>
): ApiFallbackResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isMock, setIsMock] = useState(false);
  const [tick, setTick] = useState(0);

  // 用 ref 固化最新回调，避免回调身份变化导致循环请求
  const fnRef = useRef(fn);
  const mockRef = useRef(mockFn);
  fnRef.current = fn;
  mockRef.current = mockFn;

  const refresh = useCallback(() => setTick((t) => t + 1), []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    withFallback(() => fnRef.current(), () => mockRef.current())
      .then(({ data: result, isMock: mock }) => {
        if (cancelled) return;
        setData(result);
        setIsMock(mock);
        setLoading(false);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : String(err));
        setLoading(false);
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick]);

  return { data, loading, error, isMock, refresh };
}
