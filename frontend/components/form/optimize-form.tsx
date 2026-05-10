"use client";

import { useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { HubSelect } from "./hub-select";
import { BudgetSlider } from "./budget-slider";
import { DeadlineSlider } from "./deadline-slider";
import { WeightSlider } from "./weight-slider";
import { CountrySelect } from "./country-select";
import { CitySelect } from "./city-select";
import { StayDaysInput } from "./stay-days-input";

export type FocusField = "budget" | "deadline" | "countries" | null;

interface OptimizeFormProps {
  budget_won: number;
  deadline_days: number;
  start_hub: string;
  w_cost: number;
  required_countries: string[] | null;
  required_cities: string[] | null;
  stay_days: Record<string, number>;
  focusField: FocusField;
  onBudgetChange: (v: number) => void;
  onDeadlineChange: (v: number) => void;
  onHubChange: (v: string) => void;
  onWeightChange: (v: number) => void;
  onCountriesChange: (v: string[] | null) => void;
  onCitiesChange: (v: string[] | null) => void;
  onStayDaysChange: (v: Record<string, number>) => void;
}

export function OptimizeForm(props: OptimizeFormProps) {
  const budgetRef = useRef<HTMLDivElement>(null);
  const deadlineRef = useRef<HTMLDivElement>(null);
  const countriesRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const ref =
      props.focusField === "budget"
        ? budgetRef
        : props.focusField === "deadline"
          ? deadlineRef
          : props.focusField === "countries"
            ? countriesRef
            : null;
    ref?.current?.scrollIntoView({ behavior: "smooth", block: "center" });
  }, [props.focusField]);

  return (
    <Card className="h-fit lg:sticky lg:top-4">
      <CardHeader className="pb-3">
        <CardTitle className="text-lg">입력 조건</CardTitle>
      </CardHeader>
      <CardContent className="space-y-5">
        <HubSelect value={props.start_hub} onChange={props.onHubChange} />
        <FocusableField fieldRef={budgetRef} active={props.focusField === "budget"}>
          <BudgetSlider value={props.budget_won} onChange={props.onBudgetChange} />
        </FocusableField>
        <FocusableField fieldRef={deadlineRef} active={props.focusField === "deadline"}>
          <DeadlineSlider value={props.deadline_days} onChange={props.onDeadlineChange} />
        </FocusableField>
        <WeightSlider value={props.w_cost} onChange={props.onWeightChange} />
        <FocusableField fieldRef={countriesRef} active={props.focusField === "countries"}>
          <CountrySelect value={props.required_countries} onApply={props.onCountriesChange} />
        </FocusableField>
        <CitySelect value={props.required_cities} onApply={props.onCitiesChange} />
        <StayDaysInput
          selectedCountries={props.required_countries}
          stayDays={props.stay_days}
          onChange={props.onStayDaysChange}
        />
        <p className="text-xs text-muted-foreground text-center">
          슬라이더 변경 시 자동 재계산 · 국가 변경은 "적용" 클릭
        </p>
      </CardContent>
    </Card>
  );
}

interface FocusableFieldProps {
  active: boolean;
  children: React.ReactNode;
  fieldRef: React.RefObject<HTMLDivElement | null>;
}

function FocusableField({ active, children, fieldRef }: FocusableFieldProps) {
  return (
    <div
      ref={fieldRef}
      className={cn(
        "rounded-lg p-2 -m-2 transition-shadow",
        active && "ring-2 ring-amber-400 animate-pulse",
      )}
    >
      {children}
    </div>
  );
}
