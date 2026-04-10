"use client";

import { useRouter } from "next/navigation";
import { useQueryStates, parseAsInteger, parseAsFloat, parseAsString } from "nuqs";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { HubSelect } from "./hub-select";
import { BudgetSlider } from "./budget-slider";
import { DeadlineSlider } from "./deadline-slider";
import { WeightSlider } from "./weight-slider";

export function OptimizeForm() {
  const router = useRouter();

  const [params, setParams] = useQueryStates({
    budget_won: parseAsInteger.withDefault(10_000_000),
    deadline_days: parseAsInteger.withDefault(14),
    start_hub: parseAsString.withDefault("CDG"),
    w_cost: parseAsFloat.withDefault(0.5),
  });

  function handleSubmit() {
    const search = new URLSearchParams({
      budget_won: String(params.budget_won),
      deadline_days: String(params.deadline_days),
      start_hub: params.start_hub,
      w_cost: String(params.w_cost),
    });
    router.push(`/result?${search.toString()}`);
  }

  return (
    <Card className="w-full max-w-lg">
      <CardContent className="space-y-6 pt-6">
        <HubSelect
          value={params.start_hub}
          onChange={(v) => setParams({ start_hub: v })}
        />

        <BudgetSlider
          value={params.budget_won}
          onChange={(v) => setParams({ budget_won: v })}
        />

        <DeadlineSlider
          value={params.deadline_days}
          onChange={(v) => setParams({ deadline_days: v })}
        />

        <WeightSlider
          value={params.w_cost}
          onChange={(v) => setParams({ w_cost: v })}
        />

        <Button onClick={handleSubmit} className="w-full" size="lg">
          ✨ 최적 경로 찾기
        </Button>
      </CardContent>
    </Card>
  );
}
