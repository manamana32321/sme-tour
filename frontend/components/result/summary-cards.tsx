"use client";

import { Wallet, Clock, Globe, Cpu, type LucideIcon } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { formatKRW, formatDuration } from "@/lib/format";
import type { OptimizeResult } from "@/lib/schemas";

export function SummaryCards({ result }: { result: OptimizeResult }) {
  const items: { icon: LucideIcon; label: string; value: string }[] = [
    { icon: Wallet, label: "총 비용", value: formatKRW(result.total_cost_won) },
    { icon: Clock, label: "총 기간", value: formatDuration(result.total_time_minutes) },
    { icon: Globe, label: "국가", value: `${result.visited_iata.length}개국` },
    { icon: Cpu, label: "솔버", value: `${result.solver} · ${result.solve_time_ms}ms` },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {items.map(({ icon: Icon, label, value }) => (
        <Card key={label}>
          <CardContent className="p-3 text-center">
            <Icon className="mx-auto h-5 w-5 text-muted-foreground" aria-hidden />
            <div className="mt-1 text-sm font-semibold tabular-nums">{value}</div>
            <div className="text-xs text-muted-foreground">{label}</div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
