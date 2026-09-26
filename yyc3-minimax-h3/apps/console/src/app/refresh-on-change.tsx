"use client";

// Listens to SSE `file` events (manifest/report changes) and refreshes RSC data.
// Debounced: multiple file events within 800ms trigger a single router.refresh().
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function RefreshOnChange() {
  const router = useRouter();
  useEffect(() => {
    let es: EventSource | null = null;
    let timer: ReturnType<typeof setTimeout> | null = null;
    let dirty = false;
    let disposed = false;

    const connect = () => {
      if (disposed) return;
      es = new EventSource("/api/pipeline/stream");
      es.addEventListener("file", () => {
        dirty = true;
        if (!timer) {
          timer = setTimeout(() => {
            timer = null;
            if (dirty) {
              dirty = false;
              router.refresh(); // RSC 重新渲染，浏览器无感局部更新
            }
          }, 800);
        }
      });
      es.addEventListener("error", () => {
        es?.close();
        setTimeout(connect, 5_000);
      });
    };
    connect();
    return () => {
      disposed = true;
      if (timer) clearTimeout(timer);
      es?.close();
    };
  }, [router]);
  return null;
}
