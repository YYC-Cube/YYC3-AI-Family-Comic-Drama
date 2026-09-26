/**
 * 成本面板：分项成本表 + 合计行 + 成本红线对比
 */
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Table,
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { COST_TARGET } from "@/lib/constants";
import type { CostItem } from "@/lib/mock-operations";
import { formatCost, formatPercent } from "@/lib/utils";

interface CostPanelProps {
  items: CostItem[];
  className?: string;
}

export function CostPanel({ items, className }: CostPanelProps) {
  const totalTarget = items.reduce((sum, i) => sum + i.target, 0);
  const totalActual = items.reduce((sum, i) => sum + i.actual, 0);
  // 达标判定：以 COST_TARGET 红线为基准
  const withinBudget = totalActual <= COST_TARGET;
  const diff = totalActual - COST_TARGET;

  return (
    <div className={className}>
      <div className="mb-3 flex items-center gap-3">
        <span className="text-sm text-muted-foreground">
          成本红线：单集 {formatCost(COST_TARGET)}
        </span>
        <Badge variant={withinBudget ? "success" : "destructive"}>
          {withinBudget
            ? `达标（低于红线 ${formatCost(Math.abs(diff))}）`
            : `超标 ${formatCost(diff)}`}
        </Badge>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>成本项</TableHead>
            <TableHead className="text-right">目标成本</TableHead>
            <TableHead className="text-right">实际成本（累计）</TableHead>
            <TableHead className="w-[220px]">占比</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {items.map((item) => {
            const ratio = totalActual > 0 ? (item.actual / totalActual) * 100 : 0;
            return (
              <TableRow key={item.key}>
                <TableCell className="font-medium">{item.name}</TableCell>
                <TableCell className="text-right tabular-nums">
                  {formatCost(item.target)}
                </TableCell>
                <TableCell className="text-right tabular-nums">
                  {formatCost(item.actual)}
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    <Progress value={ratio} className="w-36" />
                    <span className="text-xs tabular-nums text-muted-foreground">
                      {formatPercent(ratio)}
                    </span>
                  </div>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
        <TableFooter>
          <TableRow className="bg-muted/60 font-semibold hover:bg-muted/60">
            <TableCell>合计</TableCell>
            <TableCell className="text-right tabular-nums">
              {formatCost(totalTarget)}
            </TableCell>
            <TableCell
              className={`text-right tabular-nums ${withinBudget ? "text-emerald-600" : "text-red-600"}`}
            >
              {formatCost(totalActual)}
            </TableCell>
            <TableCell>
              <span className="text-xs text-muted-foreground">
                {formatPercent(100)}
              </span>
            </TableCell>
          </TableRow>
        </TableFooter>
      </Table>
    </div>
  );
}
