"use client";

import { Slider } from "@/components/ui/slider";
import { formatKRW } from "@/lib/format";

interface BudgetSliderProps {
  value: number;
  onChange: (value: number) => void;
}

const MIN = 1_000_000;
const MAX = 30_000_000;
const STEP = 500_000;

export function BudgetSlider({ value, onChange }: BudgetSliderProps) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium">예산</label>
        <span className="text-sm font-semibold tabular-nums">{formatKRW(value)}</span>
      </div>
      <Slider
        min={MIN}
        max={MAX}
        step={STEP}
        value={[value]}
        onValueChange={(v) => { const arr = Array.isArray(v) ? v : [v]; onChange(arr[0]); }}
      />
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>{formatKRW(MIN)}</span>
        <span>{formatKRW(MAX)}</span>
      </div>
    </div>
  );
}
