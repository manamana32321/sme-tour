"use client";

import { Slider } from "@/components/ui/slider";

interface WeightSliderProps {
  value: number;
  onChange: (value: number) => void;
}

export function WeightSlider({ value, onChange }: WeightSliderProps) {
  const label =
    value < 0.35 ? "⏱️ 시간 우선" :
    value > 0.65 ? "💰 비용 우선" :
    "⚖️ 균형";

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium">우선 순위</label>
        <span className="text-sm font-semibold">{label}</span>
      </div>
      <Slider
        min={0}
        max={1}
        step={0.05}
        value={[value]}
        onValueChange={(v) => { const arr = Array.isArray(v) ? v : [v]; onChange(arr[0]); }}
      />
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>⏱️ 시간</span>
        <span>💰 비용</span>
      </div>
    </div>
  );
}
