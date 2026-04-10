"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { HubSelect } from "./hub-select";
import { BudgetSlider } from "./budget-slider";
import { DeadlineSlider } from "./deadline-slider";
import { WeightSlider } from "./weight-slider";
import { CountrySelect } from "./country-select";

interface OptimizeFormProps {
  budget_won: number;
  deadline_days: number;
  start_hub: string;
  w_cost: number;
  required_countries: string[] | null;
  onBudgetChange: (v: number) => void;
  onDeadlineChange: (v: number) => void;
  onHubChange: (v: string) => void;
  onWeightChange: (v: number) => void;
  onCountriesChange: (v: string[] | null) => void;
}

export function OptimizeForm(props: OptimizeFormProps) {
  return (
    <Card className="h-fit lg:sticky lg:top-4">
      <CardHeader className="pb-3">
        <CardTitle className="text-lg">입력 조건</CardTitle>
      </CardHeader>
      <CardContent className="space-y-5">
        <HubSelect value={props.start_hub} onChange={props.onHubChange} />
        <BudgetSlider value={props.budget_won} onChange={props.onBudgetChange} />
        <DeadlineSlider value={props.deadline_days} onChange={props.onDeadlineChange} />
        <WeightSlider value={props.w_cost} onChange={props.onWeightChange} />
        <CountrySelect value={props.required_countries} onChange={props.onCountriesChange} />
        <p className="text-xs text-muted-foreground text-center">
          변경 시 자동 재계산
        </p>
      </CardContent>
    </Card>
  );
}
