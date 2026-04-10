"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export function InfeasibleBanner() {
  const router = useRouter();
  const sp = useSearchParams();

  function retryWithMoreBudget() {
    const params = new URLSearchParams(sp.toString());
    const budget = Number(params.get("budget_won") ?? 10_000_000);
    params.set("budget_won", String(Math.round(budget * 1.2)));
    router.replace(`/result?${params.toString()}`);
  }

  function retryWithMoreDays() {
    const params = new URLSearchParams(sp.toString());
    const days = Number(params.get("deadline_days") ?? 14);
    params.set("deadline_days", String(Math.min(days + 3, 30)));
    router.replace(`/result?${params.toString()}`);
  }

  return (
    <Card className="border-amber-200 bg-amber-50 dark:border-amber-900 dark:bg-amber-950">
      <CardContent className="p-6 text-center space-y-3">
        <p className="text-lg font-semibold">경로를 찾을 수 없어요</p>
        <p className="text-sm text-muted-foreground">
          현재 조건에서 15개국 모두 방문할 수 있는 경로가 없습니다.
          예산을 늘리거나 기간을 길게 잡아보세요.
        </p>
        <div className="flex gap-2 justify-center">
          <Button variant="outline" size="sm" onClick={retryWithMoreBudget}>
            예산 +20%
          </Button>
          <Button variant="outline" size="sm" onClick={retryWithMoreDays}>
            기간 +3일
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
