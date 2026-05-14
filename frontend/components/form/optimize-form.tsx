"use client";

import { useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { HubSelect } from "./hub-select";
import { BudgetSlider } from "./budget-slider";
import { DeadlineSlider } from "./deadline-slider";
import { WeightSlider } from "./weight-slider";
import { DestinationPicker, type PickerMode } from "./destination-picker";

export type FocusField = "budget" | "deadline" | "countries" | null;

interface OptimizeFormProps {
  budget_won: number;
  deadline_days: number;
  start_hub: string;
  w_cost: number;
  mode: PickerMode;
  selectedHubs: string[];
  selectedCities: string[];
  stayDays: Record<string, number>;
  focusField: FocusField;
  onBudgetChange: (v: number) => void;
  onDeadlineChange: (v: number) => void;
  onHubChange: (v: string) => void;
  onWeightChange: (v: number) => void;
  onModeChange: (v: PickerMode) => void;
  onSelectedHubsChange: (v: string[]) => void;
  onSelectedCitiesChange: (v: string[]) => void;
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
          <DestinationPicker
            mode={props.mode}
            selectedHubs={props.selectedHubs}
            selectedCities={props.selectedCities}
            stayDays={props.stayDays}
            onModeChange={props.onModeChange}
            onSelectedHubsChange={props.onSelectedHubsChange}
            onSelectedCitiesChange={props.onSelectedCitiesChange}
            onStayDaysChange={props.onStayDaysChange}
          />
        </FocusableField>
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
