"use client";

/**
 * 左侧固定导航栏（240px，深色主题）
 */
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BookOpen,
  Clapperboard,
  Coins,
  Film,
  FolderKanban,
  LayoutDashboard,
  ListChecks,
  TrendingUp,
  Users,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
}

const NAV_ITEMS: NavItem[] = [
  { label: "生产监控", href: "/production", icon: LayoutDashboard },
  { label: "成本核算", href: "/cost", icon: Coins },
  { label: "运营数据", href: "/analytics", icon: TrendingUp },
  { label: "项目管理", href: "/project", icon: FolderKanban },
  { label: "剧本编辑", href: "/script", icon: BookOpen },
  { label: "分镜工作台", href: "/storyboard", icon: Clapperboard },
  { label: "资产管理", href: "/assets", icon: Users },
  { label: "时间线剪辑", href: "/video", icon: Film },
  { label: "任务监控", href: "/tasks", icon: ListChecks },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed inset-y-0 left-0 z-40 flex w-60 flex-col bg-zinc-950 text-zinc-300">
      {/* 品牌区 */}
      <div className="flex h-14 items-center border-b border-zinc-800 px-5">
        <span className="text-sm font-semibold tracking-wide text-white">
          YYC³ AI Family
        </span>
        <span className="ml-2 text-xs text-zinc-500">漫剧工场</span>
      </div>

      {/* 导航 */}
      <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
        {NAV_ITEMS.map(({ label, href, icon: Icon }) => {
          const active = pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                active
                  ? "bg-zinc-800 font-medium text-white"
                  : "text-zinc-400 hover:bg-zinc-900 hover:text-zinc-100"
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* 底部：品牌与 NAS 状态 */}
      <div className="border-t border-zinc-800 px-5 py-4 text-xs text-zinc-500">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-emerald-500" />
          <span>NAS /mnt/nas</span>
        </div>
        <p className="mt-2 leading-5">YYC³ AI Family 漫剧生产线</p>
      </div>
    </aside>
  );
}
