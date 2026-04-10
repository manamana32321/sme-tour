"use client";

import { Card, CardContent } from "@/components/ui/card";
import { formatKRW, formatDuration } from "@/lib/format";
import type { OptimizeResult } from "@/lib/schemas";

export function SummaryCards({ result }: { result: OptimizeResult }) {
  const items = [
    { icon: "💰", label: "총 비용", value: formatKRW(result.total_cost_won) },
    { icon: "⏱️", label: "총 기간", value: formatDuration(result.total_time_minutes) },
    { icon: "🌍", label: "국가", value: `${result.visited_iata.length}개국` },
    { icon: "⚙️", label: "솔버", value: `${result.solver} · ${result.solve_time_ms}ms` },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {items.map((item) => (
        <Card key={item.label}>
          <CardContent className="p-3 text-center">
            <div className="text-lg">{item.icon}</div>
            <div className="text-sm font-semibold">{item.value}</div>
            <div className="text-xs text-muted-foreground">{item.label}</div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
