import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "YYC3-MiniMax-H3 控制台",
  description: "Ref2VA 流水线生产控制台 — RSC 直读 manifest 单一事实源",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body>
        <header className="border-b border-(--border) px-6 py-3 flex items-center gap-5">
          <span className="text-lg font-bold" style={{ color: "var(--accent)" }}>
            YYC³ MiniMax-H3
          </span>
          <nav className="flex gap-4 text-sm">
            <a href="/" className="text-(--muted) hover:text-(--foreground)">仪表盘</a>
            <a href="/pipeline" className="text-(--muted) hover:text-(--foreground)">流水线控制</a>
          </nav>
          <span className="text-sm text-(--muted) ml-auto">路线B · Phase 2</span>
        </header>
        <main className="p-6">{children}</main>
      </body>
    </html>
  );
}
