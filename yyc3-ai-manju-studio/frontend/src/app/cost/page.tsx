"use client";

/**
 * 成本核算：单集成本红线对比 + 累计成本与剩余预算
 */
import { CostPanel } from "@/components/dashboard/cost-panel";
import { StatCard } from "@/components/dashboard/stat-card";
import { PageHeader } from "@/components/layout/page-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { COST_TARGET } from "@/lib/constants";
import { mockCostReport } from "@/lib/mock-operations";
import { formatCost } from "@/lib/utils";
import { Coins, PiggyBank, Wallet } from "lucide-react";

export default function CostPage() {
  const totalActual = mockCostReport.items.reduce((sum, i) => sum + i.actual, 0);
  const monthlyTotal = totalActual * 120; // 本月累计（按 120 集估算演示值）
  const remainingBudget = COST_TARGET * 120 - monthlyTotal;

  return (
    <div>
      <PageHeader
        title="成本核算"
        description="单集成本红线管理：目标 2 元/集，超出红线自动预警"
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="单集实际成本"
          value={formatCost(totalActual)}
          delta={totalActual <= COST_TARGET ? "低于红线，达标" : "超出红线"}
          trend={totalActual <= COST_TARGET ? "up" : "down"}
          icon={<Coins className="h-4 w-4" />}
        />
        <StatCard
          title="单集目标成本"
          value={formatCost(COST_TARGET)}
          trend="flat"
          icon={<Wallet className="h-4 w-4" />}
        />
        <StatCard
          title="本月累计（估）"
          value={formatCost(monthlyTotal)}
          delta="按 120 集估算"
          trend="flat"
          icon={<PiggyBank className="h-4 w-4" />}
        />
        <StatCard
          title="剩余预算（估）"
          value={formatCost(Math.max(0, remainingBudget))}
          delta={remainingBudget >= 0 ? "预算内" : "已超支"}
          trend={remainingBudget >= 0 ? "up" : "down"}
        />
      </div>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="text-base">单集成本明细</CardTitle>
        </CardHeader>
        <CardContent>
          <CostPanel items={mockCostReport.items} />
        </CardContent>
      </Card>
    </div>
  );
}
